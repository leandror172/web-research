"""Tests for event-log wiring in the CLI search loop (Phase 3.2)."""

from __future__ import annotations

import argparse
import json

import web_research.cli as cli


def _args(tmp_path, **overrides) -> argparse.Namespace:
    defaults = dict(
        query="q",
        limit=5,
        top=3,
        model="qwen3:14b",
        prompt_type="open",
        focus=None,
        cleaner="trafilatura",
        output_dir=str(tmp_path),
        min_chars=200,
        skip_domains="",
        fetcher="httpx",
        no_audit=True,
        max_iterations=3,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def read_events(tmp_path):
    (path,) = (tmp_path / "events").glob("events-*.jsonl")
    return [json.loads(line) for line in path.read_text().splitlines()]


class TestRunSearchEventLog:
    def test_writes_event_file_with_full_lifecycle(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cli, "search_and_extract", lambda **kwargs: ["u1"])

        cli._run_search(_args(tmp_path), store=None)

        events = read_events(tmp_path)
        assert events[0]["event"] == "session_start"
        assert events[0]["query"] == "q"
        assert events[-1]["event"] == "session_end"

    def test_no_audit_session_ends_as_single_pass(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cli, "search_and_extract", lambda **kwargs: ["u1"])

        cli._run_search(_args(tmp_path, no_audit=True), store=None)

        assert read_events(tmp_path)[-1]["stop_reason"] == "single_pass"
