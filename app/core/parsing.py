from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any


def load_json_object(raw_output: str) -> dict[str, Any]:
    text = raw_output.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
    except JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Expected a JSON object in model output.") from None
        parsed = json.loads(text[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("Expected a top-level JSON object in model output.")

    return parsed
