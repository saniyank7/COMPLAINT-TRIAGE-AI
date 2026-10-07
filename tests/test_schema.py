import pytest

from app.schema import parse_and_validate

ALLOWED = ["Credit card", "Mortgage", "Debt collection"]
GOOD = '{"product": "Mortgage", "issue": "Payment misapplied", "summary": "Payment was not credited.", "urgent": false, "urgency_reason": ""}'


def test_valid_json_passes():
    r = parse_and_validate(GOOD, ALLOWED)
    assert r.product == "Mortgage" and r.urgent is False


def test_markdown_fences_are_stripped():
    assert parse_and_validate(f"```json\n{GOOD}\n```", ALLOWED).product == "Mortgage"


def test_product_outside_allowed_list_rejected():
    with pytest.raises(ValueError):
        parse_and_validate(GOOD.replace("Mortgage", "Crypto"), ALLOWED)


def test_malformed_json_rejected():
    with pytest.raises(ValueError):
        parse_and_validate("not json at all", ALLOWED)


def test_missing_field_rejected():
    with pytest.raises(ValueError):
        parse_and_validate('{"product": "Mortgage"}', ALLOWED)
