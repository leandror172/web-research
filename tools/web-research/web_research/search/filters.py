"""Search result filtering — domain blacklist loaded from domain_blacklist.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

_CONFIG_PATH = Path(__file__).parent / "domain_blacklist.json"


@lru_cache(maxsize=1)
def load_domain_blacklist() -> frozenset[str]:
    """Load domain blacklist from domain_blacklist.json, or return a hardcoded fallback."""
    if not _CONFIG_PATH.exists():
        return frozenset()
    try:
        data = json.loads(_CONFIG_PATH.read_text())
        return frozenset(data.get("blacklist", []))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: failed to load domain_blacklist.json: {e}. No domains blacklisted.")
        return frozenset()


def is_blacklisted(url: str, extra: frozenset[str] = frozenset()) -> bool:
    """Return True if the URL's domain appears in the blacklist or extra domains."""
    hostname = urlparse(url).hostname
    if not hostname:
        return True

    if hostname.startswith("www."):
        hostname = hostname[4:]

    combined = load_domain_blacklist() | extra
    domain_parts = hostname.split(".")
    for i in range(len(domain_parts)):
        if ".".join(domain_parts[i:]) in combined:
            return True

    return False
