"""Cleaner implementations: trafilatura and html2text."""

from __future__ import annotations

import re

import html2text
import trafilatura

from web_research.extraction.protocols import CleanResult


class TrafilaturaCleaner:
    """Extracts main content using trafilatura. Strips boilerplate (nav, ads, footer)."""

    def clean(self, html: str) -> CleanResult:
        text = trafilatura.extract(
            html,
            include_links=True,
            include_tables=True,
            output_format="txt",
        )
        if text is None:
            text = ""

        links = _extract_links_from_html(html)
        return CleanResult(text=text, links=links)


class Html2TextCleaner:
    """Converts HTML to markdown using html2text. Preserves more structure but keeps boilerplate."""

    def __init__(self, body_width: int = 0):
        self._body_width = body_width

    def clean(self, html: str) -> CleanResult:
        converter = html2text.HTML2Text()
        converter.body_width = self._body_width
        converter.ignore_images = True
        converter.protect_links = True

        text = converter.handle(html)
        links = _extract_links_from_html(html)
        return CleanResult(text=text, links=links)


def _extract_links_from_html(html: str) -> list[str]:
    """Extract href URLs from raw HTML. Simple regex — not a full parser."""
    return re.findall(r'href=["\']([^"\']+)["\']', html)


CLEANERS: dict[str, type] = {
    "trafilatura": TrafilaturaCleaner,
    "html2text": Html2TextCleaner,
}


def get_cleaner(name: str) -> TrafilaturaCleaner | Html2TextCleaner:
    """Look up a cleaner by name."""
    cls = CLEANERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown cleaner: {name!r}. Available: {list(CLEANERS)}")
    return cls()
