import json
import re

from pydantic import BaseModel, Field, ValidationError


class TriageResult(BaseModel):
    product: str
    issue: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=400)
    urgent: bool
    urgency_reason: str = ""


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def parse_and_validate(raw: str, allowed: list[str]) -> TriageResult:
    """Parse the model's raw text into a TriageResult.

    Raises ValueError if the JSON is malformed, a field is missing,
    or the product is not in the allowed list.
    """
    try:
        data = json.loads(_strip_fences(raw))
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("JSON is not an object")
    try:
        result = TriageResult(**data)
    except (ValidationError, TypeError) as e:
        raise ValueError(f"schema error: {e}") from e
    if result.product not in allowed:
        raise ValueError(f"product '{result.product}' not in allowed list")
    return result
