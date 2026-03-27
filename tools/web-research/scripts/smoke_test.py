#!/usr/bin/env python3
"""Smoke test: fetch → clean → chunk without calling Ollama."""

import argparse
import sys
import time

from web_research.extraction.chunker import chunk_text
from web_research.extraction.cleaners import get_cleaner
from web_research.extraction.fetcher import HttpxFetcher
from web_research.extraction.models import max_extract_chars


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test pipeline up to extraction")
    parser.add_argument("url", help="URL to process")
    parser.add_argument("--model", default="qwen3:14b")
    parser.add_argument("--cleaner", default="trafilatura")
    args = parser.parse_args()

    try:
        t0 = time.monotonic()
        print(f"Fetching {args.url}...")
        page = HttpxFetcher().fetch(args.url)
        print(f"  status {page.status_code} in {time.monotonic()-t0:.2f}s")

        t1 = time.monotonic()
        print(f"Cleaning ({args.cleaner})...")
        content = get_cleaner(args.cleaner).clean(page.html)
        print(f"  {len(content.text)} chars, {len(content.links)} links in {time.monotonic()-t1:.2f}s")

        t2 = time.monotonic()
        max_chars = max_extract_chars(args.model)
        chunks = chunk_text(content.text, max_chars)
        print(f"Chunking (model={args.model}, max={max_chars})...")
        print(f"  {len(chunks)} chunk(s) in {time.monotonic()-t2:.2f}s")

        print(f"\nPipeline ready — {len(chunks)} chunk(s) would be sent to Ollama")

    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
