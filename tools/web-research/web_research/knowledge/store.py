"""SQLite-backed knowledge store for web extraction results."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from web_research.extraction.protocols import CleanResult, ExtractionResult


class KnowledgeStore:
    """Persistent storage for extraction results with query and topic-based retrieval."""

    def __init__(self, db_path: str | Path = "output/knowledge.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS extractions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                url             TEXT NOT NULL UNIQUE,
                query           TEXT,
                model           TEXT NOT NULL,
                prompt_type     TEXT NOT NULL,
                focus           TEXT,
                extracted_at    TEXT NOT NULL,
                duration_seconds REAL,
                clean_chars     INTEGER,
                data            TEXT NOT NULL,
                links           TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_url          ON extractions(url);
            CREATE INDEX IF NOT EXISTS idx_query        ON extractions(query);
            CREATE INDEX IF NOT EXISTS idx_extracted_at ON extractions(extracted_at);
        """)

    def save(
        self,
        url: str,
        clean: CleanResult,
        extraction: ExtractionResult,
        query: str | None = None,
        focus: str | None = None,
    ) -> int:
        cursor = self._conn.execute(
            """
            INSERT OR REPLACE INTO extractions
                (url, query, model, prompt_type, focus, extracted_at,
                 duration_seconds, clean_chars, data, links)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                url,
                query,
                extraction.model,
                extraction.prompt_type,
                focus,
                datetime.now(timezone.utc).isoformat(),
                extraction.duration_seconds,
                len(clean.text),
                json.dumps(extraction.data),
                json.dumps(clean.links),
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    def has_url(self, url: str) -> bool:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM extractions WHERE url = ?", (url,)
        ).fetchone()
        return row[0] > 0

    def query(self, topic: str, limit: int = 10) -> list[dict[str, Any]]:
        pattern = f"%{topic}%"
        rows = self._conn.execute(
            """
            SELECT * FROM extractions
            WHERE url LIKE ? OR query LIKE ? OR data LIKE ?
            ORDER BY extracted_at DESC
            LIMIT ?
            """,
            (pattern, pattern, pattern, limit),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def recent(self, n: int = 10) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM extractions ORDER BY extracted_at DESC LIMIT ?", (n,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> KnowledgeStore:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        d["data"] = json.loads(d["data"])
        d["links"] = json.loads(d["links"])
        return d
