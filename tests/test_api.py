from fastapi.testclient import TestClient

import app.main as main
from app.schema import TriageResult

client = TestClient(main.app)
META = {"latency_ms": 5, "prompt_tokens": 10, "completion_tokens": 5, "valid_json": True, "retried": False, "error": ""}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_triage_success(monkeypatch):
    res = TriageResult(product="Mortgage", issue="Late fee", summary="Charged a late fee.", urgent=False)
    monkeypatch.setattr(main, "run_triage", lambda text: (res, META))
    r = client.post("/triage", json={"text": "I was charged a late fee on my mortgage."})
    assert r.status_code == 200 and r.json()["product"] == "Mortgage"


def test_invalid_model_output_returns_422(monkeypatch):
    bad = {**META, "valid_json": False, "retried": True, "error": "invalid JSON"}
    monkeypatch.setattr(main, "run_triage", lambda text: (None, bad))
    r = client.post("/triage", json={"text": "Some complaint text here."})
    assert r.status_code == 422


def test_short_text_rejected():
    assert client.post("/triage", json={"text": "hi"}).status_code == 422


def test_stats_endpoint():
    assert "n" in client.get("/stats").json()
