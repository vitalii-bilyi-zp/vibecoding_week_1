import os

import pytest
from fastapi.testclient import TestClient

from app import ai
from app.main import app

client = TestClient(app)


def test_ai_check_returns_answer(monkeypatch):
    monkeypatch.setattr(ai, "ask", lambda prompt: "4")
    response = client.get("/api/ai/check")
    assert response.status_code == 200
    assert response.json()["answer"] == "4"


def test_ai_check_reports_missing_key(monkeypatch):
    def raise_missing(prompt: str) -> str:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    monkeypatch.setattr(ai, "ask", raise_missing)
    response = client.get("/api/ai/check")
    assert response.status_code == 500
    assert "OPENROUTER_API_KEY" in response.json()["detail"]


def test_ai_check_reports_upstream_failure(monkeypatch):
    def raise_upstream(prompt: str) -> str:
        raise Exception("boom")

    monkeypatch.setattr(ai, "ask", raise_upstream)
    response = client.get("/api/ai/check")
    assert response.status_code == 502


def test_get_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        ai.get_client()


@pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_AI"),
    reason="set RUN_LIVE_AI=1 (and OPENROUTER_API_KEY) to run the live OpenRouter test",
)
def test_live_two_plus_two():
    answer = ai.ask("What is 2+2? Reply with just the number.")
    assert "4" in answer
