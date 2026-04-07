"""Tests for the merger module."""

from __future__ import annotations

import pytest

from web_research.extraction.merger import (
    _dedup_links,
    _dedup_lists,
    _highest_assessment,
    _merge_dicts,
    merge_results,
)
from web_research.extraction.protocols import ExtractionResult


def _result(data: dict, prompt_type: str = "open", duration: float = 1.0) -> ExtractionResult:
    return ExtractionResult(data=data, model="qwen3:14b", prompt_type=prompt_type, duration_seconds=duration)


class TestMergeResults:
    def test_single_result_returns_unchanged(self, sample_extraction):
        result = merge_results([sample_extraction])
        assert result == sample_extraction

    def test_empty_list_raises_value_error(self):
        with pytest.raises(ValueError, match="Cannot merge empty list"):
            merge_results([])

    def test_unknown_prompt_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown prompt_type"):
            merge_results([_result({})], "invalid")

    def test_duration_summed_across_results(self, sample_extraction):
        second = _result({**sample_extraction.data}, duration=3.0)
        result = merge_results([sample_extraction, second], "open")
        assert result.duration_seconds == sample_extraction.duration_seconds + 3.0

    def test_model_and_prompt_type_from_first_result(self, sample_extraction):
        second = _result({**sample_extraction.data}, duration=1.0)
        result = merge_results([sample_extraction, second], "open")
        assert result.model == sample_extraction.model
        assert result.prompt_type == sample_extraction.prompt_type


class TestMergeOpen:
    def test_key_features_deduplicated(self):
        r1 = _result({"key_features": ["fast", "clean"]})
        r2 = _result({"key_features": ["fast", "cheap"]})
        result = merge_results([r1, r2], "open")
        assert result.data["key_features"] == ["fast", "clean", "cheap"]

    def test_use_cases_merged(self):
        r1 = _result({"use_cases": ["research"]})
        r2 = _result({"use_cases": ["research", "monitoring"]})
        result = merge_results([r1, r2], "open")
        assert result.data["use_cases"] == ["research", "monitoring"]

    def test_technical_details_later_overwrites_earlier(self):
        r1 = _result({"technical_details": {"language": "Python"}})
        r2 = _result({"technical_details": {"language": "Python", "version": "3.9"}})
        result = merge_results([r1, r2], "open")
        assert result.data["technical_details"] == {"language": "Python", "version": "3.9"}

    def test_links_deduplicated_by_url(self):
        link = {"url": "https://example.com", "text": "Docs"}
        r1 = _result({"links": [link]})
        r2 = _result({"links": [link]})
        result = merge_results([r1, r2], "open")
        assert len(result.data["links"]) == 1

    def test_links_different_urls_both_kept(self):
        r1 = _result({"links": [{"url": "https://a.com", "text": "A"}]})
        r2 = _result({"links": [{"url": "https://b.com", "text": "B"}]})
        result = merge_results([r1, r2], "open")
        assert len(result.data["links"]) == 2


class TestMergeFocused:
    def test_relevant_facts_deduplicated(self):
        r1 = _result({"relevant_facts": ["fact1", "fact2"]}, prompt_type="focused")
        r2 = _result({"relevant_facts": ["fact2", "fact3"]}, prompt_type="focused")
        result = merge_results([r1, r2], "focused")
        assert result.data["relevant_facts"] == ["fact1", "fact2", "fact3"]

    def test_assessment_high_beats_medium(self):
        r1 = _result({"assessment": "medium"}, prompt_type="focused")
        r2 = _result({"assessment": "high"}, prompt_type="focused")
        result = merge_results([r1, r2], "focused")
        assert result.data["assessment"] == "high"

    def test_assessment_medium_beats_low(self):
        r1 = _result({"assessment": "low"}, prompt_type="focused")
        r2 = _result({"assessment": "medium"}, prompt_type="focused")
        result = merge_results([r1, r2], "focused")
        assert result.data["assessment"] == "medium"


class TestDedupLists:
    def test_preserves_insertion_order(self):
        results = [_result({"k": ["c", "b", "a"]}), _result({"k": ["d", "b", "e"]})]
        assert _dedup_lists(results, "k") == ["c", "b", "a", "d", "e"]

    def test_missing_key_treated_as_empty(self):
        results = [_result({}), _result({"k": ["x"]})]
        assert _dedup_lists(results, "k") == ["x"]


class TestMergeDicts:
    def test_keys_merged_from_all_results(self):
        results = [_result({"td": {"a": 1}}), _result({"td": {"b": 2}})]
        assert _merge_dicts(results, "td") == {"a": 1, "b": 2}

    def test_later_result_overwrites_earlier_on_conflict(self):
        results = [_result({"td": {"k": "old"}}), _result({"td": {"k": "new"}})]
        assert _merge_dicts(results, "td") == {"k": "new"}


class TestHighestAssessment:
    def test_high_beats_all(self):
        results = [_result({"assessment": a}) for a in ["low", "high", "medium"]]
        assert _highest_assessment(results) == "high"

    def test_medium_beats_low(self):
        results = [_result({"assessment": a}) for a in ["low", "medium"]]
        assert _highest_assessment(results) == "medium"

    def test_no_assessment_returns_low(self):
        assert _highest_assessment([_result({})]) == "low"
