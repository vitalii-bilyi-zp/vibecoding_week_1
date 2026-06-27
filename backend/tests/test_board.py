from fastapi.testclient import TestClient

from app.main import app

SEED_TITLES = ["Backlog", "Discovery", "In Progress", "Review", "Done"]


def board_with_one_card(column_id: str):
    """A board where `column_id` holds a single card and the rest are empty."""
    columns = []
    for cid, title in [
        ("col-backlog", "Backlog"),
        ("col-discovery", "Discovery"),
        ("col-progress", "In Progress"),
        ("col-review", "Review"),
        ("col-done", "Done"),
    ]:
        columns.append(
            {
                "id": cid,
                "title": title,
                "cardIds": ["card-1"] if cid == column_id else [],
            }
        )
    return {
        "columns": columns,
        "cards": {"card-1": {"id": "card-1", "title": "Task", "details": "Do it"}},
    }


def test_get_board_seeds_five_empty_columns(client):
    response = client.get("/api/board")
    assert response.status_code == 200
    data = response.json()
    assert [c["title"] for c in data["columns"]] == SEED_TITLES
    assert all(column["cardIds"] == [] for column in data["columns"])
    assert data["cards"] == {}


def test_db_file_created_on_demand(client, tmp_path):
    client.get("/api/board")
    assert (tmp_path / "test.db").exists()


def test_put_then_get_roundtrips(client):
    response = client.put("/api/board", json=board_with_one_card("col-backlog"))
    assert response.status_code == 200

    data = client.get("/api/board").json()
    backlog = next(c for c in data["columns"] if c["id"] == "col-backlog")
    assert backlog["cardIds"] == ["card-1"]
    assert data["cards"]["card-1"] == {
        "id": "card-1",
        "title": "Task",
        "details": "Do it",
    }


def test_move_card_between_columns(client):
    client.put("/api/board", json=board_with_one_card("col-backlog"))
    client.put("/api/board", json=board_with_one_card("col-done"))

    data = client.get("/api/board").json()
    backlog = next(c for c in data["columns"] if c["id"] == "col-backlog")
    done = next(c for c in data["columns"] if c["id"] == "col-done")
    assert backlog["cardIds"] == []
    assert done["cardIds"] == ["card-1"]


def test_rename_column(client):
    board = board_with_one_card("col-backlog")
    board["columns"][0]["title"] = "Renamed"
    client.put("/api/board", json=board)

    data = client.get("/api/board").json()
    assert data["columns"][0]["title"] == "Renamed"


def test_persists_across_restart(client):
    client.put("/api/board", json=board_with_one_card("col-progress"))

    # Re-entering the app lifespan with the same DATABASE_PATH simulates a restart.
    with TestClient(app) as restarted:
        data = restarted.get("/api/board").json()
        progress = next(c for c in data["columns"] if c["id"] == "col-progress")
        assert progress["cardIds"] == ["card-1"]
        assert data["cards"]["card-1"]["title"] == "Task"


def test_invalid_put_unknown_cardid_is_rejected(client):
    board = {
        "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": ["ghost"]}],
        "cards": {},
    }
    response = client.put("/api/board", json=board)
    assert response.status_code == 422

    # The board is unchanged (still the seeded empty board).
    data = client.get("/api/board").json()
    assert data["cards"] == {}


def test_invalid_put_card_key_mismatch_is_rejected(client):
    board = {
        "columns": [],
        "cards": {"card-1": {"id": "card-2", "title": "x", "details": ""}},
    }
    response = client.put("/api/board", json=board)
    assert response.status_code == 422
