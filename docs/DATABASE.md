# Database design (SQLite)

Proposed schema for the Kanban app. This document is for sign-off in Part 5; the wiring
happens in Part 6. SQLite file lives at `DATABASE_PATH` (default `./data/kanban.db`) and is
created if missing.

## Goals

- Support multiple users (even though the MVP logs in a single hardcoded user).
- One board per user for the MVP, but the schema does not prevent more later.
- Columns are ordered and renamable (a fixed set of 5 for the MVP).
- Cards have a title, details, and an order within their column.
- Round-trip cleanly to/from the frontend `BoardData` JSON shape with no data loss.

## Frontend shape we must represent

From `frontend/src/lib/kanban.ts`:

```ts
type Card = { id: string; title: string; details: string };
type Column = { id: string; title: string; cardIds: string[] };   // order = array order
type BoardData = { columns: Column[]; cards: Record<string, Card> }; // cards keyed by id
```

Ordering is implicit in array order: `columns[]` order is the column order, and each
`column.cardIds[]` order is the card order within that column.

## Tables

Four tables, normalized. IDs are stored as TEXT to preserve the frontend's string ids
(`col-backlog`, `card-1`, and generated ids like `card-ab12cd34`).

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE users (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  username   TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE boards (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name       TEXT NOT NULL DEFAULT 'My Board',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_boards_user_id ON boards(user_id);

CREATE TABLE columns (
  id         TEXT PRIMARY KEY,
  board_id   INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
  title      TEXT NOT NULL,
  position   INTEGER NOT NULL
);
CREATE INDEX idx_columns_board_id ON columns(board_id);

CREATE TABLE cards (
  id         TEXT PRIMARY KEY,
  column_id  TEXT NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
  title      TEXT NOT NULL,
  details    TEXT NOT NULL DEFAULT '',
  position   INTEGER NOT NULL
);
CREATE INDEX idx_cards_column_id ON cards(column_id);
```

## Relationships

```
users (1) --- (N) boards (1) --- (N) columns (1) --- (N) cards
```

`ON DELETE CASCADE` means deleting a user removes their boards, columns, and cards; deleting
a board removes its columns and cards, and so on.

## Ordering

- Column order: `columns.position` (0-based) within a board.
- Card order: `cards.position` (0-based) within a column.

Positions are dense integers assigned from the frontend array index on save. We do not try
to keep them sparse/gapped - on every save we rewrite positions from the incoming array
order, which keeps the model trivial.

## Mapping to/from `BoardData`

Read (DB -> JSON) for a board:

```sql
-- columns in order
SELECT id, title FROM columns WHERE board_id = :board_id ORDER BY position;
-- card ids per column, in order
SELECT id FROM cards WHERE column_id = :column_id ORDER BY position;
-- all cards for the board (to build the `cards` map)
SELECT c.id, c.title, c.details
FROM cards c JOIN columns col ON c.column_id = col.id
WHERE col.board_id = :board_id;
```

Then assemble:
- `columns` = ordered columns, each with `cardIds` = its ordered card ids.
- `cards` = `{ [card.id]: { id, title, details } }`.

Write (JSON -> DB): the chosen approach for the MVP is full-replace via `PUT /api/board` -
the frontend sends a full `BoardData` and the backend rewrites it inside a transaction:
1. For the user's board, delete existing columns (cascades to cards).
2. Insert each `column` with `position` = its index in `columns[]`.
3. For each column, insert each card (looked up in the `cards` map by id) with `position` =
   its index in that column's `cardIds[]`.
4. Touch `boards.updated_at`.

Because the MVP board is small (5 columns, a handful of cards) a full replace per save is
simple and fast. Finer-grained routes are intentionally out of scope for the MVP.

### Example

`BoardData`:

```json
{
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"] },
    { "id": "col-done", "title": "Done", "cardIds": [] }
  ],
  "cards": {
    "card-1": { "id": "card-1", "title": "Align roadmap", "details": "..." },
    "card-2": { "id": "card-2", "title": "Gather signals", "details": "..." }
  }
}
```

Rows:

```
columns: (col-backlog, board=1, "Backlog", pos=0), (col-done, board=1, "Done", pos=1)
cards:   (card-1, col-backlog, "Align roadmap", "...", pos=0),
         (card-2, col-backlog, "Gather signals", "...", pos=1)
```

## Seeding a new board

When a user has no board yet, create one seeded with the 5 fixed columns and **no cards**:
Backlog, Discovery, In Progress, Review, Done (positions 0-4). The user fills it themselves.
The seed definition lives in backend code (Part 6) as the single source of truth.

Note: the frontend's in-memory `initialData` still contains 8 demo cards today; once the
frontend reads the board from the API (Part 7), a fresh user will see the 5 empty columns
instead.

## API JSON representation

The API speaks the frontend `BoardData` shape directly - no separate DTO:
- `GET /api/board` -> `BoardData` (seeded if the user has none).
- `PUT /api/board` accepts a `BoardData` and persists it via the full-replace write above.

This keeps the frontend and backend on one shared contract.

## MVP vs future (not built now)

- Authentication: the MVP login is hardcoded and client-side, so `users` has no password
  column yet. A `password_hash` column (and a real login route) is the natural future
  extension - additive, no redesign.
- Multiple boards per user: already possible (boards.user_id is not unique); the MVP just
  uses the first board.
- The fixed 5-column rule is a product constraint, not a DB constraint - the schema allows
  any number of columns.

### Known limitation: globally-unique column/card ids

`columns.id` and `cards.id` are global TEXT primary keys, and a new board is seeded with the
fixed ids `col-backlog`...`col-done`. With a single user (the MVP) this is fine. But if two
users each got a seeded board, both would try to insert `col-backlog` and collide on the
primary key. True multi-user support therefore needs the client-facing id to be unique
*per board* rather than globally - e.g. give `columns`/`cards` a surrogate integer primary
key and store the string id in a `client_id` column with `UNIQUE(board_id, client_id)`.
This is an additive change (the API shape does not change) and is intentionally deferred.
