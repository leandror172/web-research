"""Tests for auditor.model_checker."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from web_research.auditor.model_checker import ModelChecker, SufficiencyVerdict
from web_research.auditor.signals import AuditSignals


class _StubRenderer:
    def render(self, signals: AuditSignals) -> str:
        return "STUB_SIGNALS"


@pytest.fixture
def stub_renderer() -> _StubRenderer:
    return _StubRenderer()


@pytest.fixture
def template_path(tmp_path: Path) -> Path:
    p = tmp_path / "t.md"
    p.write_text("Q={query}\nS={signals}\nE={entries}")
    return p


@pytest.fixture
def posted(mocker, stub_renderer, template_path):
    """Patches httpx.post once. Returns {'call': runner, 'mock': the post mock}."""
    mock_response = mocker.Mock()
    state = {"payload": {
        "sufficient": True,
        "confidence": "high",
        "reasoning": "ok",
        "missing_topics": [],
        "recommended_queries": [],
    }}

    def _json_side_effect() -> dict:
        return {"message": {"content": json.dumps(state["payload"])}}

    mock_response.json.side_effect = _json_side_effect
    mock_post = mocker.patch("httpx.post", return_value=mock_response)

    def run(
        *,
        signals: AuditSignals | None = None,
        entries: list[dict] | None = None,
        model: str = "test-model",
        base_url: str = "http://localhost:11434",
        response_payload: dict | None = None,
    ) -> tuple[dict, SufficiencyVerdict]:
        if response_payload is not None:
            state["payload"] = response_payload
        if signals is None:
            signals = AuditSignals("q", 0, [], None, None)
        checker = ModelChecker(
            model=model,
            template_path=template_path,
            renderer=stub_renderer,
            base_url=base_url,
        )
        verdict = checker.check(signals, entries or [])
        payload = mock_post.call_args.kwargs["json"]
        return payload, verdict

    return {"run": run, "mock": mock_post}


class TestSufficiencyVerdict:
    def test_is_frozen(self):
        v = SufficiencyVerdict(
            sufficient=True,
            confidence="high",
            reasoning="ok",
            missing_topics=[],
            recommended_queries=[],
        )
        with pytest.raises(Exception, match="cannot assign"):
            v.sufficient = False


class TestCheck:
    def test_posts_to_chat_endpoint(self, posted):
        posted["run"]()
        assert posted["mock"].call_args.args[0] == "http://localhost:11434/api/chat"

    def test_sends_model_name(self, posted):
        payload, _ = posted["run"](model="custom-model")
        assert payload["model"] == "custom-model"

    def test_includes_format_schema(self, posted):
        payload, _ = posted["run"]()
        assert payload["format"]["type"] == "object"

    def test_fills_query_slot(self, posted):
        signals = AuditSignals("search term", 0, [], None, None)
        payload, _ = posted["run"](signals=signals)
        assert "search term" in payload["messages"][0]["content"]

    def test_fills_signals_slot(self, posted):
        payload, _ = posted["run"]()
        assert "STUB_SIGNALS" in payload["messages"][0]["content"]

    def test_fills_entries_slot(self, posted):
        entries = [{"url": "https://example.com/a"}, {"url": "https://other.org/b"}]
        payload, _ = posted["run"](entries=entries)
        assert "https://example.com/a" in payload["messages"][0]["content"]
        assert "https://other.org/b" in payload["messages"][0]["content"]

    def test_parses_sufficient_true(self, posted):
        _, verdict = posted["run"](response_payload={
            "sufficient": True,
            "confidence": "high",
            "reasoning": "enough info",
            "missing_topics": [],
            "recommended_queries": [],
        })
        assert verdict.sufficient is True
        assert verdict.confidence == "high"
        assert verdict.reasoning == "enough info"

    def test_parses_missing_topics_and_queries(self, posted):
        _, verdict = posted["run"](response_payload={
            "sufficient": False,
            "confidence": "medium",
            "reasoning": "gaps",
            "missing_topics": ["t1", "t2"],
            "recommended_queries": ["q1", "q2"],
        })
        assert verdict.sufficient is False
        assert verdict.missing_topics == ["t1", "t2"]
        assert verdict.recommended_queries == ["q1", "q2"]

    def test_custom_base_url(self, posted):
        posted["run"](base_url="http://other:99")
        assert posted["mock"].call_args.args[0] == "http://other:99/api/chat"
