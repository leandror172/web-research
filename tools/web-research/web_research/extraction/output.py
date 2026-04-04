"""Output writer that saves extraction results as JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from web_research.extraction.protocols import CleanResult, ExtractionResult


class JsonOutputWriter:
    """Saves cleaned text and extraction results to files."""

    def __init__(self, output_dir: str = "output"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, url: str, clean: CleanResult, extraction: ExtractionResult) -> str:
        url_slug = self._slugify(url)
        model_slug = self._sanitize(extraction.model)
        slug = f"{url_slug}--{model_slug}--{extraction.prompt_type}"
        raw_path = self._output_dir / f"{slug}-raw.md"
        json_path = self._output_dir / f"{slug}-extracted.json"

        raw_path.write_text(clean.text)

        json_data = {
            "url": url,
            "model": extraction.model,
            "prompt_type": extraction.prompt_type,
            "duration_seconds": extraction.duration_seconds,
            "data": extraction.data,
            "links": clean.links,
        }
        json_path.write_text(json.dumps(json_data, indent=2))

        return str(json_path)

    def _slugify(self, url: str) -> str:
        parsed = urlparse(url)
        raw = f"{parsed.netloc}{parsed.path}"
        slug = re.sub(r"[^a-zA-Z0-9]", "-", raw).strip("-").lower()
        return slug[:80]

    def _sanitize(self, name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9._-]", "-", name).strip("-").lower()
