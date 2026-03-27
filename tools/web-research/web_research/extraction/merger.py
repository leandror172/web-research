"""Merge multiple extraction results into a single result."""

from __future__ import annotations

from web_research.extraction.protocols import ExtractionResult


def merge_results(results: list[ExtractionResult], prompt_type: str = "open") -> ExtractionResult:
    """Combine multiple ExtractionResult objects into one."""
    if not results:
        raise ValueError("Cannot merge empty list of results")

    if prompt_type == "open":
        return _merge_open(results)
    if prompt_type == "focused":
        return _merge_focused(results)
    raise ValueError(f"Unknown prompt_type: {prompt_type!r}. Use 'open' or 'focused'.")


def _merge_open(results: list[ExtractionResult]) -> ExtractionResult:
    first = results[0]
    merged_data = {
        "name": first.data.get("name"),
        "summary": first.data.get("summary"),
        "key_features": _dedup_lists(results, "key_features"),
        "use_cases": _dedup_lists(results, "use_cases"),
        "technical_details": _merge_dicts(results, "technical_details"),
        "links": _dedup_links(results),
        "limitations": _dedup_lists(results, "limitations"),
    }
    return _build_result(first, merged_data, results)


def _merge_focused(results: list[ExtractionResult]) -> ExtractionResult:
    first = results[0]
    merged_data = {
        "relevant_facts": _dedup_lists(results, "relevant_facts"),
        "key_details": _dedup_lists(results, "key_details"),
        "links": _dedup_links(results),
        "assessment": _highest_assessment(results),
    }
    return _build_result(first, merged_data, results)


def _build_result(first: ExtractionResult, data: dict, results: list[ExtractionResult]) -> ExtractionResult:
    return ExtractionResult(
        data=data,
        model=first.model,
        prompt_type=first.prompt_type,
        duration_seconds=sum(r.duration_seconds for r in results),
    )


def _dedup_lists(results: list[ExtractionResult], key: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for result in results:
        for item in result.data.get(key, []):
            if item not in seen:
                out.append(item)
                seen.add(item)
    return out


def _merge_dicts(results: list[ExtractionResult], key: str) -> dict:
    merged: dict = {}
    for result in results:
        details = result.data.get(key, {})
        if isinstance(details, dict):
            merged.update(details)
    return merged


def _dedup_links(results: list[ExtractionResult]) -> list[dict]:
    seen_urls: set[str] = set()
    out: list[dict] = []
    for result in results:
        for link in result.data.get("links", []):
            if isinstance(link, dict) and "url" in link:
                if link["url"] not in seen_urls:
                    out.append(link)
                    seen_urls.add(link["url"])
    return out


_RELEVANCE = {"high": 2, "medium": 1, "low": 0}


def _highest_assessment(results: list[ExtractionResult]) -> str:
    assessments = [
        r.data.get("assessment", "")
        for r in results
        if r.data.get("assessment")
    ]
    if not assessments:
        return "low"
    return max(assessments, key=lambda a: _RELEVANCE.get(a, 0))
