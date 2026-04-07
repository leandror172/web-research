"""Tests for JsonOutputWriter."""

from __future__ import annotations

import json
from pathlib import Path

from web_research.extraction.output import JsonOutputWriter


class TestJsonOutputWriter:
    def test_save_creates_json_and_raw_files(self, tmp_path, sample_clean, sample_extraction):
        writer = JsonOutputWriter(str(tmp_path))
        json_path = writer.save("https://example.com/test", sample_clean, sample_extraction)
        assert Path(json_path).exists()
        raw_files = list(tmp_path.glob("*-raw.md"))
        assert len(raw_files) == 1

    def test_json_contains_required_keys(self, tmp_path, sample_clean, sample_extraction):
        writer = JsonOutputWriter(str(tmp_path))
        json_path = writer.save("https://example.com/test", sample_clean, sample_extraction)
        data = json.loads(Path(json_path).read_text())
        for key in ("url", "model", "prompt_type", "duration_seconds", "data", "links"):
            assert key in data

    def test_json_values_match_inputs(self, tmp_path, sample_clean, sample_extraction):
        writer = JsonOutputWriter(str(tmp_path))
        url = "https://example.com/test"
        json_path = writer.save(url, sample_clean, sample_extraction)
        data = json.loads(Path(json_path).read_text())
        assert data["url"] == url
        assert data["model"] == sample_extraction.model
        assert data["prompt_type"] == sample_extraction.prompt_type
        assert data["duration_seconds"] == sample_extraction.duration_seconds
        assert data["data"] == sample_extraction.data
        assert data["links"] == sample_clean.links

    def test_two_different_urls_create_separate_files(self, tmp_path, sample_clean, sample_extraction):
        writer = JsonOutputWriter(str(tmp_path))
        p1 = writer.save("https://example.com/page1", sample_clean, sample_extraction)
        p2 = writer.save("https://example.com/page2", sample_clean, sample_extraction)
        assert p1 != p2
        assert Path(p1).exists()
        assert Path(p2).exists()

    def test_creates_output_dir_if_missing(self, tmp_path, sample_clean, sample_extraction):
        output_dir = tmp_path / "nested" / "output"
        writer = JsonOutputWriter(str(output_dir))
        writer.save("https://example.com", sample_clean, sample_extraction)
        assert output_dir.exists()
