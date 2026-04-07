"""Tests for extraction models."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from web_research.extraction.models import _get_ollama_context_length, _load_config, max_extract_chars


@pytest.fixture(autouse=True)
def clear_caches():
    max_extract_chars.cache_clear()
    _load_config.cache_clear()


def _make_config(context: int = 8000, reserve: int = 2000, cpt: int = 4, models: dict | None = None) -> dict:
    return {
        "defaults": {"context_tokens": context, "prompt_reserve_tokens": reserve, "chars_per_token": cpt},
        "models": models or {},
    }


class TestMaxExtractChars:
    def test_uses_json_override_without_ollama(self, monkeypatch):
        config = _make_config(models={"test-model": {"context_tokens": 10000}})
        monkeypatch.setattr("web_research.extraction.models._load_config", lambda: config)
        assert max_extract_chars("test-model") == (10000 - 2000) * 4

    def test_falls_back_to_ollama_when_not_in_config(self, monkeypatch):
        monkeypatch.setattr("web_research.extraction.models._load_config", lambda: _make_config())
        monkeypatch.setattr("web_research.extraction.models._get_ollama_context_length", lambda m: 12000)
        assert max_extract_chars("test-model") == (12000 - 2000) * 4

    def test_falls_back_to_default_when_ollama_returns_none(self, monkeypatch):
        monkeypatch.setattr("web_research.extraction.models._load_config", lambda: _make_config())
        monkeypatch.setattr("web_research.extraction.models._get_ollama_context_length", lambda m: None)
        assert max_extract_chars("test-model") == (8000 - 2000) * 4

    def test_formula_correct(self, monkeypatch):
        config = _make_config(context=4000, reserve=500, cpt=3, models={"m": {"context_tokens": 4000}})
        monkeypatch.setattr("web_research.extraction.models._load_config", lambda: config)
        assert max_extract_chars("m") == (4000 - 500) * 3


class TestGetOllamaContextLength:
    def test_returns_context_length_from_model_info(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"model_info": {"llama.context_length": 32768}}
        mock_resp.raise_for_status.return_value = None
        with patch("web_research.extraction.models.httpx.post", return_value=mock_resp):
            assert _get_ollama_context_length("qwen3:14b") == 32768

    def test_returns_none_when_request_error(self):
        with patch("web_research.extraction.models.httpx.post", side_effect=httpx.RequestError("timeout")):
            assert _get_ollama_context_length("qwen3:14b") is None

    def test_returns_none_when_no_context_length_key(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"model_info": {"other.key": "value"}}
        mock_resp.raise_for_status.return_value = None
        with patch("web_research.extraction.models.httpx.post", return_value=mock_resp):
            assert _get_ollama_context_length("qwen3:14b") is None
