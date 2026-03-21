"""Main spike script: fetch → clean → extract → save."""

from __future__ import annotations

import argparse
from pathlib import Path

from spike.cleaners import get_cleaner
from spike.extractor import OllamaExtractor
from spike.fetcher import HttpxFetcher
from spike.output import JsonOutputWriter
from spike.protocols import ExtractionConfig


def run(
    url: str,
    cleaner: str = "trafilatura",
    model: str = "qwen3.5:9b",
    prompt_type: str = "open",
    focus: str | None = None,
    output_dir: str = "spike/output",
) -> None:
    """Run the full extraction pipeline for a single URL."""
    print(f"Fetching {url}...")
    page = HttpxFetcher().fetch(url)

    print(f"Cleaning ({cleaner})...")
    content = get_cleaner(cleaner).clean(page.html)

    MAX_CHARS = 6000
    text = content.text
    if len(text) > MAX_CHARS:
        print(f"Truncating {len(text)} → {MAX_CHARS} chars")
        text = text[:MAX_CHARS]

    config = ExtractionConfig(
        model=model, prompt_type=prompt_type, focus=focus,
    )
    print(f"Extracting ({model})...")
    result = OllamaExtractor().extract(text, config)

    path = JsonOutputWriter(output_dir).save(url, content, result)
    print(f"Saved to {path}")

    print(f"\n--- Summary ---")
    print(f"Model: {result.model}")
    print(f"Duration: {result.duration_seconds:.1f}s")
    if "key_features" in result.data:
        print(f"Key features: {len(result.data['key_features'])}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extraction spike")
    parser.add_argument("url", nargs="?", help="URL to extract from")
    parser.add_argument("--urls-file", help="File with URLs (one per line, # = comment)")
    parser.add_argument("--cleaner", default="trafilatura")
    parser.add_argument("--model", default="qwen3.5:9b")
    parser.add_argument("--prompt-type", default="open")
    parser.add_argument("--focus")
    parser.add_argument("--output-dir", default="spike/output")
    args = parser.parse_args()

    if not args.url and not args.urls_file:
        parser.error("provide a URL or --urls-file")

    urls: list[str] = []
    if args.urls_file:
        for line in Path(args.urls_file).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    if args.url:
        urls.insert(0, args.url)

    for url in urls:
        print(f"\n{'='*60}")
        run(
            url=url,
            cleaner=args.cleaner,
            model=args.model,
            prompt_type=args.prompt_type,
            focus=args.focus,
            output_dir=args.output_dir,
        )


if __name__ == "__main__":
    main()
