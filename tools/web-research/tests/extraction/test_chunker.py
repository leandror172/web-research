"""Tests for text chunking utility."""

from __future__ import annotations

import pytest

from web_research.extraction.chunker import _split_large_block, chunk_text


class TestChunkText:
    def test_short_text_returned_as_single_chunk(self):
        result = chunk_text("Hello world", 100)
        assert result == ["Hello world"]

    def test_text_exactly_at_max_chars_is_single_chunk(self):
        text = "A" * 50
        result = chunk_text(text, 50)
        assert result == [text]

    def test_two_paragraphs_exceeding_max_split_correctly(self):
        # overlap=0 keeps this predictable: no tail prefix injected
        text = "\n\n".join(["A" * 30, "B" * 30])  # 62 chars total
        result = chunk_text(text, 50, overlap=0)
        assert len(result) == 2
        assert all(len(c) <= 50 for c in result)

    def test_overlap_tail_appears_at_start_of_next_chunk(self):
        # p1=100, p2=80, max=150, overlap=50
        # p1+"\n\n"+p2 = 182 > 150 → split after p1
        # prefix = "A"*50 + "\n\n" = 52 chars; 52+80=132 ≤ 150 → p2 gets prefix
        p1 = "A" * 100
        p2 = "B" * 80
        result = chunk_text(p1 + "\n\n" + p2, 150, overlap=50)
        assert len(result) == 2
        assert result[0].endswith("A" * 50)
        assert result[1].startswith("A" * 50)

    def test_empty_string_returns_single_empty_chunk(self):
        # Early return before strip-filter; callers guard via min_chars check
        assert chunk_text("", 100) == [""]

    def test_single_huge_paragraph_hard_cut(self):
        # No paragraph breaks — falls through to _split_large_block
        text = "A" * 200
        result = chunk_text(text, 100, overlap=0)
        assert all(len(c) <= 100 for c in result)

    def test_size_invariant_holds_for_all_chunks(self):
        # Multi-paragraph text with many splits
        paragraphs = [f"Paragraph {i}: " + "word " * 20 for i in range(10)]
        text = "\n\n".join(paragraphs)
        max_chars = 100
        chunks = chunk_text(text, max_chars, overlap=20)
        assert chunks  # not empty
        assert all(len(c) <= max_chars for c in chunks)


class TestSplitLargeBlock:
    def test_block_within_limit_returned_unchanged(self):
        result = _split_large_block("Hello world", 100)
        assert result == ["Hello world"]

    def test_split_at_sentence_boundary(self):
        # 14 + 16 = 30 chars; max_chars=20 forces split
        text = "First sentence. Second sentence."
        result = _split_large_block(text, 20)
        assert len(result) == 2
        assert all(len(c) <= 20 for c in result)

    def test_single_sentence_exceeding_limit_hard_cut(self):
        # 150 chars, max=50 → exactly 3 pieces
        text = "A" * 150
        result = _split_large_block(text, 50)
        assert len(result) == 3
        assert all(len(c) <= 50 for c in result)

    def test_empty_string_returns_single_empty_chunk(self):
        # Same early-return behaviour as chunk_text
        assert _split_large_block("", 100) == [""]
