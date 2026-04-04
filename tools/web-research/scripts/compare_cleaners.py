#!/usr/bin/env python3
"""Compare output of trafilatura and html2text cleaners for a URL."""

import argparse
import sys

from web_research.extraction.cleaners import Html2TextCleaner, TrafilaturaCleaner
from web_research.extraction.fetcher import HttpxFetcher
from web_research.extraction.protocols import CleanResult


def _print_result(name: str, result: CleanResult) -> None:
    chars = len(result.text)
    preview = result.text[:200] if chars > 0 else "EMPTY"
    print(f"\n{name}:")
    print(f"  chars : {chars}")
    print(f"  links : {len(result.links)}")
    print(f"  preview: {preview}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare trafilatura vs html2text cleaners")
    parser.add_argument("url", help="URL to fetch and compare")
    args = parser.parse_args()

    try:
        page = HttpxFetcher().fetch(args.url)
        print(f"status : {page.status_code}")
        print(f"content-type: {page.content_type}")

        _print_result("trafilatura", TrafilaturaCleaner().clean(page.html))
        _print_result("html2text  ", Html2TextCleaner().clean(page.html))

    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
