"""CLI entry point for web research tool."""

from __future__ import annotations

import argparse
import logging

from web_research.extraction.chunker import chunk_text
from web_research.extraction.cleaners import get_cleaner
from web_research.extraction.extractor import OllamaExtractor
from web_research.extraction.fetcher import HttpxFetcher
from web_research.extraction.firecrawl_fetcher import FirecrawlFetcher
from web_research.extraction.merger import merge_results
from web_research.extraction.models import max_extract_chars
from web_research.extraction.output import JsonOutputWriter
from web_research.extraction.protocols import ExtractionConfig
from web_research.conductor import build_default_auditor, iterate
from web_research.knowledge.store import KnowledgeStore
from web_research.search.firecrawl import FirecrawlSearchEngine
from web_research.search.filters import is_blacklisted

logger = logging.getLogger(__name__)


class ThinContentError(ValueError):
    """Raised when content is too short to extract meaningful information."""


def _get_fetcher(name: str) -> HttpxFetcher | FirecrawlFetcher:
    if name == "firecrawl":
        return FirecrawlFetcher()
    return HttpxFetcher()


def extract_single_url(
    url: str,
    cleaner: str = "trafilatura",
    model: str = "qwen3:14b",
    prompt_type: str = "open",
    focus: str | None = None,
    output_dir: str = "output",
    min_chars: int = 200,
    fetcher: str = "httpx",
    store: KnowledgeStore | None = None,
    query: str | None = None,
) -> None:
    """Extract from a single URL using the full pipeline."""
    print(f"Fetching {url}...")
    page = _get_fetcher(fetcher).fetch(url)

    if page.status_code >= 400:
        raise ValueError(f"HTTP {page.status_code} for {url}")

    print(f"Cleaning ({cleaner})...")
    content = get_cleaner(cleaner).clean(page.html)

    if len(content.text) < min_chars:
        raise ThinContentError(f"Thin content ({len(content.text)} chars) for {url}")

    text = content.text
    max_chars = max_extract_chars(model)
    chunks = chunk_text(text, max_chars)
    print(f"Content: {len(text)} chars → {len(chunks)} chunk(s) @ {max_chars} max")

    config = ExtractionConfig(
        model=model,
        prompt_type=prompt_type,
        focus=focus,
    )
    extractor = OllamaExtractor()
    results = []
    for i, chunk in enumerate(chunks):
        print(f"Extracting chunk {i + 1}/{len(chunks)} ({len(chunk)} chars, {model})...")
        results.append(extractor.extract(chunk, config))

    result = merge_results(results, prompt_type) if len(results) > 1 else results[0]

    path = JsonOutputWriter(output_dir).save(url, content, result)
    print(f"Saved to {path}")

    if store is not None:
        store.save(url, content, result, query=query, focus=focus)

    print(f"\n--- Summary ---")
    print(f"Model: {result.model}")
    print(f"Duration: {result.duration_seconds:.1f}s")
    if "key_features" in result.data:
        print(f"Key features: {len(result.data['key_features'])}")


def search_and_extract(
    query: str,
    limit: int = 5,
    top: int = 3,
    model: str = "qwen3:14b",
    prompt_type: str = "open",
    focus: str | None = None,
    cleaner: str = "trafilatura",
    output_dir: str = "output",
    min_chars: int = 200,
    skip_domains: frozenset[str] = frozenset(),
    fetcher: str = "httpx",
    store: KnowledgeStore | None = None,
) -> list[str]:
    """Search the web and extract from top results.

    Returns the list of URLs that were freshly extracted this round
    (cached/skipped/errored URLs are excluded). The Conductor uses this
    signal to detect rounds that produced no new knowledge.
    """
    engine = FirecrawlSearchEngine()
    print(f"Searching for '{query}'...")
    results = engine.search(query, limit)

    if not results:
        print("No results found.")
        return []

    print(f"\n--- Search Results ---")
    for r in results:
        print(f"  {r.position}. {r.title} — {r.url}")

    print(f"\nExtracting from top {top} usable results...\n")

    filtered = [r for r in results if not is_blacklisted(r.url, skip_domains)]

    for r in results:
        if is_blacklisted(r.url, skip_domains):
            print(f"Skipping (blacklisted domain): {r.url}")

    if not filtered:
        print("No results after domain filtering.")
        return []

    usable_count = 0
    new_urls: list[str] = []
    for i, r in enumerate(filtered):
        if usable_count >= top:
            break

        print(f"{'='*60}")
        print(f"[{i + 1}/{len(filtered)}] {r.title}")

        if store is not None and store.has_url(r.url):
            print(f"Skipping (already in knowledge store): {r.url}")
            usable_count += 1  # already-known counts as usable
            continue

        try:
            extract_single_url(
                url=r.url,
                cleaner=cleaner,
                model=model,
                prompt_type=prompt_type,
                focus=focus,
                output_dir=output_dir,
                min_chars=min_chars,
                fetcher=fetcher,
                store=store,
                query=query,
            )
            usable_count += 1
            new_urls.append(r.url)
        except ThinContentError:
            print(f"Skipping — thin content: {r.url}")
        except Exception as e:
            print(f"Error extracting {r.url}: {e}")

    print(f"\n{'='*60}")
    print(f"Done. Extracted {usable_count} usable pages for query: {query}")
    return new_urls


def _run_search(args, store: KnowledgeStore | None) -> None:
    """Run the audit-driven search loop via Conductor."""
    skip_domains = frozenset(
        d.strip() for d in args.skip_domains.split(",") if d.strip()
    )

    def _do_search(query: str, **_) -> list[str]:
        return search_and_extract(
            query=query,
            limit=args.limit,
            top=args.top,
            model=args.model,
            prompt_type=args.prompt_type,
            focus=args.focus,
            cleaner=args.cleaner,
            output_dir=args.output_dir,
            min_chars=args.min_chars,
            skip_domains=skip_domains,
            fetcher=args.fetcher,
            store=store,
        )

    auditor = None if args.no_audit or store is None else build_default_auditor(store)
    max_iter = 1 if args.no_audit else args.max_iterations

    final = None
    for result in iterate(
        args.query,
        search_and_extract=_do_search,
        auditor=auditor,
        max_iterations=max_iter,
    ):
        final = result
        _print_iteration_banner(result, max_iter)

    if final is not None and final.verdict is not None:
        print(f"\n=== Final verdict ===")
        print(f"Sufficient: {final.verdict.sufficient} ({final.verdict.confidence})")
        if final.verdict.reasoning:
            print(f"Reasoning: {final.verdict.reasoning}")


def _print_iteration_banner(result, max_iter: int) -> None:
    banner = f"\n[iteration {result.iteration + 1}/{max_iter}] query: {result.query_used!r} → {len(result.new_urls)} new URL(s)"
    print(banner)
    if result.audit_failed:
        print("  Auditor: FAILED — continuing without verdict")
        return
    if result.verdict is None:
        return
    v = result.verdict
    status = "sufficient" if v.sufficient else "insufficient"
    print(f"  Auditor: {status} ({v.confidence})")
    if v.missing_topics:
        print(f"    Missing: {', '.join(v.missing_topics)}")
    if not v.sufficient and v.recommended_queries:
        print(f"    Next query: {v.recommended_queries[0]!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Web research CLI tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract from a single URL")
    extract_parser.add_argument("url", help="URL to extract from")
    extract_parser.add_argument("--cleaner", default="trafilatura")
    extract_parser.add_argument("--model", default="qwen3:14b")
    extract_parser.add_argument("--prompt-type", default="open")
    extract_parser.add_argument("--focus")
    extract_parser.add_argument("--output-dir", default="output")
    extract_parser.add_argument("--fetcher", default="httpx", choices=["httpx", "firecrawl"])
    extract_parser.add_argument("--db", default="output/knowledge.db", help="Knowledge store path")
    extract_parser.add_argument("--no-db", action="store_true", help="Skip knowledge store")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search and extract from results")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=5, help="Search results to fetch")
    search_parser.add_argument("--top", type=int, default=3, help="Usable results to extract")
    search_parser.add_argument("--model", default="qwen3:14b")
    search_parser.add_argument("--prompt-type", default="open")
    search_parser.add_argument("--focus")
    search_parser.add_argument("--cleaner", default="trafilatura")
    search_parser.add_argument("--output-dir", default="output")
    search_parser.add_argument("--min-chars", type=int, default=200)
    search_parser.add_argument("--skip-domains", default="", help="Comma-separated extra domains to skip")
    search_parser.add_argument("--fetcher", default="httpx", choices=["httpx", "firecrawl"])
    search_parser.add_argument("--db", default="output/knowledge.db", help="Knowledge store path")
    search_parser.add_argument("--no-db", action="store_true", help="Skip knowledge store")
    search_parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Max audit-driven iterations (default 3)",
    )
    search_parser.add_argument(
        "--no-audit",
        action="store_true",
        help="Skip Auditor; run a single search+extract round",
    )

    args = parser.parse_args()

    store: KnowledgeStore | None = None
    if not args.no_db:
        store = KnowledgeStore(args.db)

    try:
        if args.command == "extract":
            extract_single_url(
                url=args.url,
                cleaner=args.cleaner,
                model=args.model,
                prompt_type=args.prompt_type,
                focus=args.focus,
                output_dir=args.output_dir,
                fetcher=args.fetcher,
                store=store,
            )
        elif args.command == "search":
            _run_search(args, store)
    finally:
        if store is not None:
            store.close()


if __name__ == "__main__":
    main()
