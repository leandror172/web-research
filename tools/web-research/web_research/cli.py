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
) -> None:
    """Search the web and extract from top results."""
    engine = FirecrawlSearchEngine()
    print(f"Searching for '{query}'...")
    results = engine.search(query, limit)

    if not results:
        print("No results found.")
        return

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
        return

    usable_count = 0
    for i, r in enumerate(filtered):
        if usable_count >= top:
            break

        print(f"{'='*60}")
        print(f"[{i + 1}/{len(filtered)}] {r.title}")
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
            )
            usable_count += 1
        except ThinContentError:
            print(f"Skipping — thin content: {r.url}")
        except Exception as e:
            print(f"Error extracting {r.url}: {e}")

    print(f"\n{'='*60}")
    print(f"Done. Extracted {usable_count} usable pages for query: {query}")


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

    args = parser.parse_args()

    if args.command == "extract":
        extract_single_url(
            url=args.url,
            cleaner=args.cleaner,
            model=args.model,
            prompt_type=args.prompt_type,
            focus=args.focus,
            output_dir=args.output_dir,
            fetcher=args.fetcher,
        )
    elif args.command == "search":
        search_and_extract(
            query=args.query,
            limit=args.limit,
            top=args.top,
            model=args.model,
            prompt_type=args.prompt_type,
            focus=args.focus,
            cleaner=args.cleaner,
            output_dir=args.output_dir,
            min_chars=args.min_chars,
            skip_domains=frozenset(d.strip() for d in args.skip_domains.split(",") if d.strip()),
            fetcher=args.fetcher,
        )


if __name__ == "__main__":
    main()
