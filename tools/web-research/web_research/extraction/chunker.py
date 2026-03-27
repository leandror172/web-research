"""Text chunking utility for LLM extraction."""

from __future__ import annotations


def _split_large_block(block: str, max_chars: int) -> list[str]:
    """Split an oversized block on sentence boundaries, then hard-cut if needed."""
    if len(block) <= max_chars:
        return [block]

    sentences = block.split(". ")
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = current + (". " if current else "") + sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If a single sentence exceeds max_chars, hard-cut it
            if len(sentence) > max_chars:
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i : i + max_chars])
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]


def chunk_text(text: str, max_chars: int, overlap: int = 200) -> list[str]:
    """Split text into chunks for LLM extraction.

    Args:
        text: Input text to be chunked.
        max_chars: Maximum characters per chunk.
        overlap: Characters to overlap between chunks for context continuity.

    Returns:
        List of text chunks, each at most max_chars long.
    """
    if len(text) <= max_chars:
        return [text]

    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        # Check if adding this paragraph (with separator) fits
        candidate = current + ("\n\n" if current else "") + paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue

        # Doesn't fit — flush current chunk
        if current:
            chunks.append(current)

        # Start new chunk: overlap from previous chunk's tail
        if chunks and overlap > 0:
            tail = chunks[-1][-overlap:]
            prefix = tail + "\n\n"
        else:
            prefix = ""

        # If the paragraph itself (with prefix) fits, use it
        if len(prefix) + len(paragraph) <= max_chars:
            current = prefix + paragraph
        else:
            # Oversized paragraph — split it, no overlap on internal splits
            sub_blocks = _split_large_block(paragraph, max_chars - len(prefix))
            if sub_blocks:
                # First sub-block gets the overlap prefix
                chunks.append(prefix + sub_blocks[0] if prefix else sub_blocks[0])
                # Remaining sub-blocks stand alone
                chunks.extend(sub_blocks[1:])
            current = ""

    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]
