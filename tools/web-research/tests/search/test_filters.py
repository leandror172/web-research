"""Tests for search filters."""

from __future__ import annotations

import json

import pytest

from web_research.search import filters
from web_research.search.filters import is_blacklisted, load_domain_blacklist


@pytest.fixture(autouse=True)
def clear_cache():
    load_domain_blacklist.cache_clear()
    yield
    load_domain_blacklist.cache_clear()


class TestIsBlacklisted:
    def test_exact_domain_match(self):
        assert is_blacklisted("https://example.com", extra=frozenset(["example.com"]))

    def test_subdomain_match(self):
        assert is_blacklisted("https://sub.example.com", extra=frozenset(["example.com"]))

    def test_www_prefix_stripped(self):
        assert is_blacklisted("https://www.example.com", extra=frozenset(["example.com"]))

    def test_no_hostname_empty_url(self):
        assert is_blacklisted("", extra=frozenset())

    def test_no_hostname_malformed_url(self):
        assert is_blacklisted("not-a-url", extra=frozenset())

    def test_domain_not_in_list(self, monkeypatch):
        monkeypatch.setattr(filters, "_CONFIG_PATH", filters._CONFIG_PATH.parent / "__nonexistent__.json")
        assert not is_blacklisted("https://example.com", extra=frozenset(["other.com"]))

    def test_parent_domain_walking(self):
        assert is_blacklisted("https://sub.reddit.com", extra=frozenset(["reddit.com"]))


class TestLoadDomainBlacklist:
    def test_returns_frozenset(self):
        result = load_domain_blacklist()
        assert isinstance(result, frozenset)

    def test_handles_missing_file_gracefully(self, monkeypatch):
        monkeypatch.setattr(filters, "_CONFIG_PATH", filters._CONFIG_PATH.parent / "__nonexistent__.json")
        result = load_domain_blacklist()
        assert result == frozenset()

    def test_loads_from_json_file(self, monkeypatch, tmp_path):
        config_file = tmp_path / "domain_blacklist.json"
        config_file.write_text(json.dumps({"blacklist": ["example.com", "test.org"]}))
        monkeypatch.setattr(filters, "_CONFIG_PATH", config_file)
        result = load_domain_blacklist()
        assert result == frozenset(["example.com", "test.org"])

    def test_handles_invalid_json(self, monkeypatch, tmp_path):
        config_file = tmp_path / "domain_blacklist.json"
        config_file.write_text("not valid json {{{")
        monkeypatch.setattr(filters, "_CONFIG_PATH", config_file)
        result = load_domain_blacklist()
        assert result == frozenset()
