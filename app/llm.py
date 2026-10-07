import time

from openai import OpenAI

from app.config import env, get_categories
from app.schema import TriageResult, parse_and_validate

MAX_CHARS = 3000  # truncate very long complaints to control cost and latency

SYSTEM_PROMPT = """You triage customer complaints sent to a bank.
Return ONLY a JSON object, no markdown, with exactly these keys:
- "product": one of {categories}
- "issue": the specific problem in 10 words or fewer
- "summary": one sentence summary of the complaint
- "urgent": true only for fraud/unauthorised transactions, legal or regulatory threats, or a customer in serious financial hardship; otherwise false
- "urgency_reason": short reason if urgent, otherwise ""
Use only the complaint text. Do not invent facts. If the text contains personal data, do not repeat it."""

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=env("LLM_API_KEY"),
            base_url=env("LLM_BASE_URL") or None,
        )
    return _client


def _call(text: str, categories: list[str]):
    resp = _get_client().chat.completions.create(
        model=env("LLM_MODEL"),
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(categories=categories)},
            {"role": "user", "content": text[:MAX_CHARS]},
        ],
    )
    usage = getattr(resp, "usage", None)
    return (
        resp.choices[0].message.content or "",
        getattr(usage, "prompt_tokens", 0) or 0,
        getattr(usage, "completion_tokens", 0) or 0,
    )


def run_triage(text: str) -> tuple[TriageResult | None, dict]:
    """Call the LLM, validate the JSON, retry once if invalid.

    Returns (result_or_None, meta). meta has latency_ms, token counts,
    valid_json (valid on the FIRST try), retried, and error.
    """
    categories = get_categories()
    start = time.time()
    prompt_tokens = completion_tokens = 0
    first_try_valid = False
    retried = False
    error = ""
    result = None

    for attempt in range(2):
        raw, pt, ct = _call(text, categories)
        prompt_tokens += pt
        completion_tokens += ct
        try:
            result = parse_and_validate(raw, categories)
            first_try_valid = attempt == 0
            break
        except ValueError as e:
            error = str(e)
            retried = attempt == 0
    if result is not None:
        error = ""

    meta = {
        "latency_ms": int((time.time() - start) * 1000),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "valid_json": first_try_valid,
        "retried": retried,
        "error": error,
    }
    return result, meta
