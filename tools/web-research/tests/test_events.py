"""Tests for the JSONL event log (Phase 3.2)."""

from __future__ import annotations

import json
import logging

from web_research.events import JsonlEventLog, NullEventLog, default_event_log


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


class TestNullEventLog:
    def test_emit_is_a_silent_noop(self):
        NullEventLog().emit({"event": "session_start"})


class TestEmit:
    def test_writes_one_json_line_per_event(self, tmp_path):
        log = JsonlEventLog(tmp_path / "events.jsonl")
        log.emit({"event": "session_start", "query": "test"})
        log.emit({"event": "session_end"})
        lines = read_lines(tmp_path / "events.jsonl")
        assert len(lines) == 2
        assert lines[0]["event"] == "session_start"
        assert lines[1]["event"] == "session_end"

    def test_preserves_event_payload_keys(self, tmp_path):
        log = JsonlEventLog(tmp_path / "events.jsonl")
        log.emit({"event": "audit_verdict", "sufficient": False, "iteration": 1})
        record = read_lines(tmp_path / "events.jsonl")[0]
        assert record["sufficient"] is False
        assert record["iteration"] == 1

    def test_stamps_iso_timestamp(self, tmp_path):
        log = JsonlEventLog(tmp_path / "events.jsonl")
        log.emit({"event": "session_start"})
        record = read_lines(tmp_path / "events.jsonl")[0]
        # ISO-8601: parseable by datetime.fromisoformat
        from datetime import datetime

        assert datetime.fromisoformat(record["ts"])

    def test_stamps_stable_session_id(self, tmp_path):
        log = JsonlEventLog(tmp_path / "events.jsonl")
        log.emit({"event": "a"})
        log.emit({"event": "b"})
        lines = read_lines(tmp_path / "events.jsonl")
        assert lines[0]["session_id"] == lines[1]["session_id"]
        assert lines[0]["session_id"]  # non-empty

    def test_distinct_instances_get_distinct_session_ids(self, tmp_path):
        a = JsonlEventLog(tmp_path / "a.jsonl")
        b = JsonlEventLog(tmp_path / "b.jsonl")
        a.emit({"event": "x"})
        b.emit({"event": "x"})
        id_a = read_lines(tmp_path / "a.jsonl")[0]["session_id"]
        id_b = read_lines(tmp_path / "b.jsonl")[0]["session_id"]
        assert id_a != id_b

    def test_creates_parent_directories(self, tmp_path):
        path = tmp_path / "nested" / "deep" / "events.jsonl"
        log = JsonlEventLog(path)
        log.emit({"event": "session_start"})
        assert path.exists()

    def test_appends_across_instances_with_same_path(self, tmp_path):
        path = tmp_path / "events.jsonl"
        JsonlEventLog(path).emit({"event": "first"})
        JsonlEventLog(path).emit({"event": "second"})
        assert len(read_lines(path)) == 2


class TestDefaultEventLog:
    def test_creates_file_under_events_subdir(self, tmp_path):
        log = default_event_log(tmp_path)
        log.emit({"event": "session_start"})
        files = list((tmp_path / "events").glob("events-*.jsonl"))
        assert len(files) == 1

    def test_filename_carries_the_session_id(self, tmp_path):
        log = default_event_log(tmp_path)
        log.emit({"event": "session_start"})
        (path,) = (tmp_path / "events").glob("events-*.jsonl")
        record = read_lines(path)[0]
        assert record["session_id"] in path.name

    def test_distinct_calls_produce_distinct_files(self, tmp_path):
        a = default_event_log(tmp_path)
        b = default_event_log(tmp_path)
        a.emit({"event": "x"})
        b.emit({"event": "x"})
        assert len(list((tmp_path / "events").glob("events-*.jsonl"))) == 2


class TestEmitNeverRaises:
    def test_unwritable_path_logs_warning_and_swallows(self, tmp_path, caplog):
        # A directory at the target path makes the open() fail.
        target = tmp_path / "events.jsonl"
        target.mkdir()
        log = JsonlEventLog(target)
        with caplog.at_level(logging.WARNING, logger="web_research.events"):
            log.emit({"event": "session_start"})  # must not raise
        assert any("event" in r.message.lower() for r in caplog.records)

    def test_unserializable_payload_logs_warning_and_swallows(self, tmp_path, caplog):
        log = JsonlEventLog(tmp_path / "events.jsonl")
        with caplog.at_level(logging.WARNING, logger="web_research.events"):
            log.emit({"event": "bad", "payload": object()})  # must not raise
        assert any(r.levelno == logging.WARNING for r in caplog.records)
