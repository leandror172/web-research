"""JSONL event log — structured audit trail for Conductor research sessions."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class EventLog(Protocol):
    """Sink for structured research-session events."""

    def emit(self, event: dict[str, Any]) -> None: ...


class JsonlEventLog:
    """EventLog that appends one JSON object per line to a file."""

    def __init__(self, path: str | Path, session_id: str | None = None) -> None:
        self.path = Path(path)
        self.session_id = session_id or uuid.uuid4().hex

    def emit(self, event: dict[str, Any]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)

            stamped_event = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "session_id": self.session_id,
                **event,
            }

            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(stamped_event) + "\n")

        except Exception as e:
            logger.warning(
                "Failed to emit event %r: %s", event.get("event", "unknown"), str(e)
            )


def default_event_log(output_dir: str | Path) -> JsonlEventLog:
    """Build the standard per-session event log under <output_dir>/events/.

    The filename carries the session id, so a replay tool can go from a
    session_id in any record straight to its file.
    """
    session_id = uuid.uuid4().hex[:12]
    path = Path(output_dir) / "events" / f"events-{session_id}.jsonl"
    return JsonlEventLog(path, session_id=session_id)
