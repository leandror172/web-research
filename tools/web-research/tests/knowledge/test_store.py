"""Tests for KnowledgeStore."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from web_research.knowledge.store import KnowledgeStore


class TestInit:
    def test_creates_db_file(self, tmp_db):
        store = KnowledgeStore(tmp_db)
        assert Path(tmp_db).exists()
        store.close()

    def test_creates_parent_directories(self, tmp_path):
        db_path = tmp_path / "nested" / "deep" / "knowledge.db"
        store = KnowledgeStore(db_path)
        assert db_path.exists()
        store.close()


class TestSave:
    def test_returns_row_id(self, tmp_db, sample_clean, sample_extraction):
        with KnowledgeStore(tmp_db) as store:
            row_id = store.save("https://example.com", sample_clean, sample_extraction)
        assert isinstance(row_id, int)

    def test_is_retrievable_via_has_url(self, tmp_db, sample_clean, sample_extraction):
        with KnowledgeStore(tmp_db) as store:
            store.save("https://example.com", sample_clean, sample_extraction)
            assert store.has_url("https://example.com")

    def test_saves_query_and_focus(self, tmp_db, sample_clean, sample_extraction):
        with KnowledgeStore(tmp_db) as store:
            store.save(
                "https://example.com",
                sample_clean,
                sample_extraction,
                query="Python web scraping",
                focus="automation",
            )
            record = store.recent(1)[0]
        assert record["query"] == "Python web scraping"
        assert record["focus"] == "automation"

    def test_upsert_same_url_updates_record(self, tmp_db, sample_clean, sample_extraction):
        updated = dataclasses.replace(
            sample_extraction,
            data={**sample_extraction.data, "name": "UpdatedTool"},
        )
        with KnowledgeStore(tmp_db) as store:
            store.save("https://example.com", sample_clean, sample_extraction, query="first")
            store.save("https://example.com", sample_clean, updated, query="second")
            rows = store.recent(5)
        assert len(rows) == 1
        assert rows[0]["data"]["name"] == "UpdatedTool"
        assert rows[0]["query"] == "second"

    def test_data_and_links_round_trip(self, tmp_db, sample_clean, sample_extraction):
        with KnowledgeStore(tmp_db) as store:
            store.save("https://example.com", sample_clean, sample_extraction)
            row = store.recent(1)[0]
        assert row["data"] == sample_extraction.data
        assert row["links"] == sample_clean.links


class TestHasUrl:
    def test_returns_true_for_saved_url(self, tmp_db, sample_clean, sample_extraction):
        with KnowledgeStore(tmp_db) as store:
            store.save("https://example.com", sample_clean, sample_extraction)
            assert store.has_url("https://example.com")

    def test_returns_false_for_unsaved_url(self, tmp_db):
        with KnowledgeStore(tmp_db) as store:
            assert not store.has_url("https://example.com")


class TestQuery:
    def test_matches_on_url(self, tmp_db, sample_clean, sample_extraction):
        with KnowledgeStore(tmp_db) as store:
            store.save("https://example.com/python-scraping", sample_clean, sample_extraction)
            results = store.query("python-scraping")
        assert len(results) == 1
        assert results[0]["url"] == "https://example.com/python-scraping"

    def test_matches_on_data_content(self, tmp_db, sample_clean, sample_extraction):
        extraction = dataclasses.replace(
            sample_extraction,
            data={**sample_extraction.data, "summary": "A tool for scraping Python websites"},
        )
        with KnowledgeStore(tmp_db) as store:
            store.save("https://example.com", sample_clean, extraction)
            results = store.query("scraping Python")
        assert len(results) == 1

    def test_returns_empty_list_when_no_match(self, tmp_db):
        with KnowledgeStore(tmp_db) as store:
            results = store.query("nonexistent_xyz")
        assert results == []

    def test_sql_special_chars_do_not_raise(self, tmp_db, sample_clean, sample_extraction):
        with KnowledgeStore(tmp_db) as store:
            store.save("https://example.com", sample_clean, sample_extraction)
            assert isinstance(store.query("%"), list)
            assert isinstance(store.query("_"), list)


class TestRecent:
    def test_returns_at_most_n_records(self, tmp_db, sample_clean, sample_extraction):
        with KnowledgeStore(tmp_db) as store:
            for i in range(5):
                store.save(f"https://example.com/{i}", sample_clean, sample_extraction)
            results = store.recent(3)
        assert len(results) == 3

    def test_returns_newest_first(self, tmp_db, sample_clean, sample_extraction):
        with KnowledgeStore(tmp_db) as store:
            store.save("https://example.com/1", sample_clean, sample_extraction)
            store.save("https://example.com/2", sample_clean, sample_extraction)
            results = store.recent(5)
        assert results[0]["url"] == "https://example.com/2"
        assert results[1]["url"] == "https://example.com/1"

    def test_returns_empty_list_on_empty_store(self, tmp_db):
        with KnowledgeStore(tmp_db) as store:
            assert store.recent(5) == []


class TestContextManager:
    def test_usable_inside_with_block(self, tmp_db, sample_clean, sample_extraction):
        with KnowledgeStore(tmp_db) as store:
            store.save("https://example.com", sample_clean, sample_extraction)
            assert store.has_url("https://example.com")

    def test_connection_closed_after_exit(self, tmp_db):
        with KnowledgeStore(tmp_db) as store:
            pass
        with pytest.raises(Exception, match="closed"):
            store.recent(1)
