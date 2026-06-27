"""SQLite access for the Kanban board.

Uses the stdlib sqlite3 driver (no ORM - the model is tiny). The schema follows
docs/DATABASE.md. A fresh connection is opened per request; the database file and
its tables are created on demand.
"""

import os
import sqlite3
from pathlib import Path

from app.models import BoardData

DEFAULT_DB_PATH = "./data/kanban.db"
HARDCODED_USERNAME = "user"

# Seed columns for a new board: the five fixed columns, no cards.
SEED_COLUMNS = [
    ("col-backlog", "Backlog"),
    ("col-discovery", "Discovery"),
    ("col-progress", "In Progress"),
    ("col-review", "Review"),
    ("col-done", "Done"),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  username   TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS boards (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name       TEXT NOT NULL DEFAULT 'My Board',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);

CREATE TABLE IF NOT EXISTS columns (
  id         TEXT PRIMARY KEY,
  board_id   INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
  title      TEXT NOT NULL,
  position   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_columns_board_id ON columns(board_id);

CREATE TABLE IF NOT EXISTS cards (
  id         TEXT PRIMARY KEY,
  column_id  TEXT NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
  title      TEXT NOT NULL,
  details    TEXT NOT NULL DEFAULT '',
  position   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cards_column_id ON cards(column_id);
"""


def get_db_path() -> str:
    return os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)


def connect() -> sqlite3.Connection:
    path = get_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _get_or_create_user(conn: sqlite3.Connection, username: str) -> int:
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if row is not None:
        return row["id"]
    cursor = conn.execute("INSERT INTO users (username) VALUES (?)", (username,))
    conn.commit()
    return cursor.lastrowid


def _seed_board(conn: sqlite3.Connection, board_id: int) -> None:
    for position, (column_id, title) in enumerate(SEED_COLUMNS):
        conn.execute(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            (column_id, board_id, title, position),
        )


def _get_or_create_board(conn: sqlite3.Connection, user_id: int) -> int:
    row = conn.execute(
        "SELECT id FROM boards WHERE user_id = ? ORDER BY id LIMIT 1", (user_id,)
    ).fetchone()
    if row is not None:
        return row["id"]
    cursor = conn.execute("INSERT INTO boards (user_id) VALUES (?)", (user_id,))
    board_id = cursor.lastrowid
    _seed_board(conn, board_id)
    conn.commit()
    return board_id


def get_board_id_for_user(conn: sqlite3.Connection, username: str = HARDCODED_USERNAME) -> int:
    """Return the user's board id, creating (and seeding) the user/board if needed."""
    user_id = _get_or_create_user(conn, username)
    return _get_or_create_board(conn, user_id)


def read_board(conn: sqlite3.Connection, board_id: int) -> dict:
    """Assemble the board into the frontend BoardData shape."""
    columns: list[dict] = []
    cards: dict[str, dict] = {}

    column_rows = conn.execute(
        "SELECT id, title FROM columns WHERE board_id = ? ORDER BY position", (board_id,)
    ).fetchall()

    for column in column_rows:
        card_rows = conn.execute(
            "SELECT id, title, details FROM cards WHERE column_id = ? ORDER BY position",
            (column["id"],),
        ).fetchall()
        card_ids: list[str] = []
        for card in card_rows:
            cards[card["id"]] = {
                "id": card["id"],
                "title": card["title"],
                "details": card["details"],
            }
            card_ids.append(card["id"])
        columns.append({"id": column["id"], "title": column["title"], "cardIds": card_ids})

    return {"columns": columns, "cards": cards}


def save_board(conn: sqlite3.Connection, board_id: int, board: BoardData) -> None:
    """Full-replace the board's columns and cards inside a transaction."""
    try:
        # Deleting the columns cascades to their cards.
        conn.execute("DELETE FROM columns WHERE board_id = ?", (board_id,))
        for column_position, column in enumerate(board.columns):
            conn.execute(
                "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
                (column.id, board_id, column.title, column_position),
            )
            for card_position, card_id in enumerate(column.cardIds):
                card = board.cards[card_id]
                conn.execute(
                    "INSERT INTO cards (id, column_id, title, details, position) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (card.id, column.id, card.title, card.details, card_position),
                )
        conn.execute(
            "UPDATE boards SET updated_at = datetime('now') WHERE id = ?", (board_id,)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
