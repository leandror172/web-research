#!/usr/bin/env python3
"""Show how a URL's content is chunked for a given model."""

import argparse
import sys

from web_research.extraction.chunker import chunk_text
from web_research.extraction.cleaners import get_cleaner
from web_research.extraction.fetcher import HttpxFetcher
from web_research.extraction.models import max_extract_chars


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect chunk breakdown for a URL + model")
    parser.add_argument("url", help="URL to fetch and chunk")
    parser.add_argument("--model", default="qwen3:14b")
    parser.add_argument("--cleaner", default="trafilatura")
    args = parser.parse_args()

    try:
        page = HttpxFetcher().fetch(args.url)
        content = get_cleaner(args.cleaner).clean(page.html)
        text = content.text
        max_chars = max_extract_chars(args.model)
        chunks = chunk_text(text, max_chars)

        print(f"total chars : {len(text)}")
        print(f"max per chunk: {max_chars}  (model: {args.model})")
        print(f"chunks       : {len(chunks)}")
        for i, chunk in enumerate(chunks):
            print(f"  [{i+1}] {len(chunk)} chars | {chunk[:80]!r}")

    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
