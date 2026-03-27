"""Extraction prompts and JSON schemas."""

from __future__ import annotations

OPEN_EXTRACTION_PROMPT = """\
Given the following web page content, extract structured information.

- name: What is this tool/project/library?
- summary: What does it do? (2-3 sentences)
- key_features: List of main capabilities (max 8)
- use_cases: What is it used for?
- technical_details: Language, license, dependencies, hosting model
- links: Important links found (docs, repo, API reference)
- limitations: Any noted limitations or caveats

Page content:
{content}"""

FOCUSED_EXTRACTION_PROMPT = """\
Given the following web page content, extract information relevant to: {focus}

- relevant_facts: Facts from this page relevant to the focus area
- key_details: Specific technical details related to the focus
- links: Links worth following for more information about the focus
- assessment: How relevant is this page to the focus? (high/medium/low with reason)

Focus: {focus}
Page content:
{content}"""

EXTRACTION_SCHEMA: dict = {
    "type": "object",
    "required": ["name", "summary", "key_features"],
    "properties": {
        "name": {"type": "string"},
        "summary": {"type": "string"},
        "key_features": {"type": "array", "items": {"type": "string"}},
        "use_cases": {"type": "array", "items": {"type": "string"}},
        "technical_details": {
            "type": "object",
            "properties": {
                "language": {"type": "string"},
                "license": {"type": "string"},
                "hosting": {"type": "string"},
            },
        },
        "links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
}

FOCUSED_SCHEMA: dict = {
    "type": "object",
    "required": ["relevant_facts", "key_details", "links", "assessment"],
    "properties": {
        "relevant_facts": {"type": "array", "items": {"type": "string"}},
        "key_details": {"type": "array", "items": {"type": "string"}},
        "links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
        "assessment": {"type": "string"},
    },
}


def build_prompt(
    content: str,
    prompt_type: str = "open",
    focus: str | None = None,
) -> tuple[str, dict]:
    """Build prompt text and matching JSON schema.

    Returns (prompt_text, json_schema) for the given extraction type.
    """
    if prompt_type == "focused":
        if focus is None:
            raise ValueError("focus is required when prompt_type='focused'")
        return FOCUSED_EXTRACTION_PROMPT.format(focus=focus, content=content), FOCUSED_SCHEMA
    if prompt_type == "open":
        return OPEN_EXTRACTION_PROMPT.format(content=content), EXTRACTION_SCHEMA
    raise ValueError(f"Unknown prompt_type: {prompt_type!r}. Use 'open' or 'focused'.")
