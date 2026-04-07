"""Tests for cleaner implementations."""

from __future__ import annotations

import pytest

from web_research.extraction.cleaners import (
    Html2TextCleaner,
    TrafilaturaCleaner,
    _extract_links_from_html,
    get_cleaner,
)
from web_research.extraction.protocols import CleanResult

SIMPLE_HTML = (
    "<html><body><h1>Title</h1><p>Some content here.</p>"
    "<a href='https://example.com'>Link</a></body></html>"
)


class TestExtractLinks:
    def test_single_link_double_quotes(self):
        links = _extract_links_from_html('<a href="https://example.com">Link</a>')
        assert links == ["https://example.com"]

    def test_single_link_single_quotes(self):
        links = _extract_links_from_html("<a href='https://example.com'>Link</a>")
        assert links == ["https://example.com"]

    def test_multiple_links(self):
        html = '<a href="https://a.com">A</a><a href="https://b.com">B</a>'
        assert _extract_links_from_html(html) == ["https://a.com", "https://b.com"]

    def test_no_hrefs_returns_empty_list(self):
        assert _extract_links_from_html("<p>No links here.</p>") == []


class TestTrafilaturaCleaner:
    def test_clean_returns_clean_result(self):
        result = TrafilaturaCleaner().clean(SIMPLE_HTML)
        assert isinstance(result, CleanResult)

    def test_clean_text_is_string(self):
        result = TrafilaturaCleaner().clean(SIMPLE_HTML)
        assert isinstance(result.text, str)

    def test_clean_links_is_list(self):
        result = TrafilaturaCleaner().clean(SIMPLE_HTML)
        assert isinstance(result.links, list)


class TestHtml2TextCleaner:
    def test_clean_returns_clean_result(self):
        result = Html2TextCleaner().clean(SIMPLE_HTML)
        assert isinstance(result, CleanResult)

    def test_clean_text_contains_visible_text(self):
        result = Html2TextCleaner().clean(SIMPLE_HTML)
        assert "Title" in result.text
        assert "Some content here." in result.text

    def test_clean_links_is_list(self):
        result = Html2TextCleaner().clean(SIMPLE_HTML)
        assert isinstance(result.links, list)


class TestGetCleaner:
    def test_returns_trafilatura_cleaner(self):
        assert isinstance(get_cleaner("trafilatura"), TrafilaturaCleaner)

    def test_returns_html2text_cleaner(self):
        assert isinstance(get_cleaner("html2text"), Html2TextCleaner)

    def test_unknown_name_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown cleaner"):
            get_cleaner("unknown")
