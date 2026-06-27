import os

import pytest

from app import ai
from app.models import (
    AIBoardUpdate,
    AICard,
    AIChatResponse,
    AIColumn,
    BoardData,
    ai_to_board,
    board_to_ai,
)


def test_chat_reply_only_leaves_board_unchanged(client, monkeypatch):
    monkeypatch.setattr(
        ai,
        "chat_with_board",
        lambda message, history, board: AIChatResponse(reply="Hello!", board_update=None),
    )

    response = client.post("/api/chat", json={"message": "hi", "history": []})
    assert response.status_code == 200
    assert response.json() == {"reply": "Hello!", "board_changed": False}

    board = client.get("/api/board").json()
    assert board["cards"] == {}


def test_chat_applies_and_persists_a_board_update(client, monkeypatch):
    update = AIBoardUpdate(
        columns=[
            AIColumn(
                id="col-backlog",
                title="Backlog",
                cards=[AICard(id="card-new", title="Buy milk", details="2 litres")],
            ),
            AIColumn(id="col-discovery", title="Discovery", cards=[]),
            AIColumn(id="col-progress", title="In Progress", cards=[]),
            AIColumn(id="col-review", title="Review", cards=[]),
            AIColumn(id="col-done", title="Done", cards=[]),
        ]
    )
    monkeypatch.setattr(
        ai,
        "chat_with_board",
        lambda message, history, board: AIChatResponse(reply="Added it.", board_update=update),
    )

    response = client.post(
        "/api/chat", json={"message": "add Buy milk to Backlog", "history": []}
    )
    assert response.status_code == 200
    assert response.json() == {"reply": "Added it.", "board_changed": True}

    board = client.get("/api/board").json()
    backlog = next(c for c in board["columns"] if c["id"] == "col-backlog")
    assert backlog["cardIds"] == ["card-new"]
    assert board["cards"]["card-new"]["title"] == "Buy milk"


def test_chat_rejects_malformed_response_and_leaves_board_unchanged(client, monkeypatch):
    def raise_invalid(message, history, board):
        raise ValueError("model returned invalid JSON")

    monkeypatch.setattr(ai, "chat_with_board", raise_invalid)

    response = client.post("/api/chat", json={"message": "do something", "history": []})
    assert response.status_code == 502

    board = client.get("/api/board").json()
    assert board["cards"] == {}


def test_chat_reports_missing_key(client, monkeypatch):
    def raise_missing(message, history, board):
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    monkeypatch.setattr(ai, "chat_with_board", raise_missing)

    response = client.post("/api/chat", json={"message": "hi", "history": []})
    assert response.status_code == 500
    assert "OPENROUTER_API_KEY" in response.json()["detail"]


def test_board_ai_shape_round_trips():
    board = BoardData.model_validate(
        {
            "columns": [
                {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]},
                {"id": "col-done", "title": "Done", "cardIds": []},
            ],
            "cards": {"card-1": {"id": "card-1", "title": "Task", "details": "Do it"}},
        }
    )
    assert ai_to_board(board_to_ai(board)) == board


@pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_AI"),
    reason="set RUN_LIVE_AI=1 (and OPENROUTER_API_KEY) to run the live chat test",
)
def test_live_chat_adds_a_card(client):
    response = client.post(
        "/api/chat",
        json={
            "message": "Add a card titled 'Live test' to the Backlog column.",
            "history": [],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["reply"], str) and body["reply"]
