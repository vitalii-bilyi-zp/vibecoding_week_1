# Project Plan: Project Management MVP

A single-board Kanban web app with AI chat, built incrementally in 10 parts.
Each part below is self-contained: an agent can execute one part using only its
checklist, then verify it against the listed tests and success criteria before moving on.

## How to use this document

- Work one part at a time, top to bottom. Do not start a part until the previous part's
  success criteria are met.
- Check off each `[ ]` substep as it is completed.
- A part is "done" only when every test passes AND every success criterion is met.
- Follow the root `CLAUDE.md` coding standards: latest idiomatic libraries, keep it simple,
  no over-engineering, no emojis, find root cause before fixing.

## Target architecture (reference)

- One Docker container runs FastAPI (via `uv`).
- FastAPI serves the statically-exported Next.js site at `/` and exposes the API under `/api/*`.
- SQLite database file lives on the local host, bind-mounted into the container at `DATABASE_PATH`
  (default `./data/kanban.db`), so data survives container rebuilds. DB is created if missing.
- AI calls go through OpenRouter using model `openai/gpt-oss-120b`; key in root `.env`.

## Conventions for all parts

- Backend: Python + FastAPI, package manager `uv`. Code in `backend/`.
- Frontend: Next.js in `frontend/` (see `frontend/CLAUDE.md`).
- API prefix: `/api`. Health check: `GET /api/health` -> `{"status": "ok"}`.
- Tests: backend uses `pytest`; frontend uses Vitest (unit) + Playwright (e2e).
- Secrets/config come from `.env` (gitignored). Never hardcode the API key.

---

## Part 1: Plan - DONE

Goal: produce a detailed, agent-runnable plan and document the existing frontend.

- [x] Enrich this document with detailed checklists, tests, and success criteria per part.
- [x] Create `frontend/CLAUDE.md` describing the existing frontend code.
- [x] Create a `.env` stub at the project root with the needed keys.
- [ ] User reviews and approves this plan.

Success criteria:
- This document lists all 10 parts with substep checklists, tests, and success criteria.
- `frontend/CLAUDE.md` exists and accurately describes the current frontend.
- `.env` stub exists at project root.
- User has explicitly approved before Part 2 begins.

---

## Part 2: Scaffolding - DONE

Goal: stand up the Docker + FastAPI skeleton and start/stop scripts. Serve a placeholder
static page and one example API call. No Kanban yet.

Substeps:
- [x] Create `backend/` FastAPI app: entry `backend/app/main.py` with a FastAPI instance.
- [x] Add `GET /api/health` returning `{"status": "ok"}`.
- [x] Add `GET /api/hello` returning `{"message": "hello world"}` (the example API call).
- [x] Mount a static directory so `GET /` serves a placeholder `index.html` ("Hello from FastAPI").
- [x] Set up `uv` in the backend: `backend/pyproject.toml` with deps (`fastapi`, `uvicorn[standard]`),
      and `uv.lock`.
- [x] Write `backend/Dockerfile` using `uv` to install deps and run uvicorn; expose port 8000.
- [x] Add `docker-compose.yml` (or documented `docker run`) wiring port 8000 and bind-mounting
      `./data` for future SQLite.
- [x] Write start/stop scripts in `scripts/`: `start.sh`/`stop.sh` (Mac/Linux) and `start.ps1`/`stop.ps1` (PC).
- [x] Update `backend/CLAUDE.md` describing the backend structure.
- [x] Add `backend/tests/test_health.py` with pytest tests for `/api/health` and `/api/hello`.

Tests:
- `pytest` in `backend/` passes (health + hello endpoints).
- Manual: `scripts/start` builds and runs the container; `curl localhost:8000/api/health` -> `{"status":"ok"}`;
  `curl localhost:8000/api/hello` -> `{"message":"hello world"}`; browser at `localhost:8000/` shows the placeholder page.
- `scripts/stop` stops and removes the container cleanly.

Success criteria:
- Container builds and runs locally with one start script command.
- Both API endpoints respond correctly and `/` serves static HTML, all from the single container.
- Start/stop scripts exist for Mac, Linux, and PC and work.

---

## Part 3: Add in Frontend - DONE

Goal: statically build the existing Next.js demo and have FastAPI serve it at `/`, so the
demo Kanban board (in-memory) is displayed.

Substeps:
- [x] Set `output: 'export'` in `frontend/next.config.ts` and confirm a static export works
      (`next build` produces an `out/` directory). Remove/avoid any SSR-only features.
- [x] Verify drag-and-drop and add/remove still work as a static export (client-only is fine).
- [x] Wire the build: produce the static site and place it where FastAPI serves it (e.g. copy `out/`
      into the backend static dir during Docker build).
- [x] Update `backend/Dockerfile` (multi-stage: Node build of frontend, then Python runtime) so the
      container builds the frontend and serves it.
- [x] FastAPI serves the exported site at `/` (and static assets), keeping `/api/*` working.
- [x] Keep existing frontend unit tests passing; keep/extend Playwright e2e to run against the
      served static site (via `E2E_BASE_URL`).

Tests:
- Frontend: `npm run test:unit` and `npm run test:e2e` pass.
- Backend: `pytest` still passes.
- Manual: start container; `localhost:8000/` shows the Kanban board with 5 columns and seed cards;
  drag a card between columns; add and remove a card.

Success criteria:
- The demo Kanban board renders at `/` served by FastAPI from the static export.
- Drag-and-drop, add card, remove card, rename column all work in the served app.
- Unit and integration (e2e) tests are comprehensive and pass.

---

## Part 4: Fake user sign in - DONE

Goal: gate the board behind a dummy login (`user` / `password`) with logout. Still in-memory board.

Substeps:
- [x] Add a login screen shown on first visit to `/` when not authenticated.
- [x] Accept only `user` / `password`; show an error on wrong credentials.
- [x] On success, show the Kanban board; persist auth across reloads (e.g. localStorage or cookie/session).
- [x] Add a logout control that returns to the login screen.
- [x] Decide and document where auth is enforced (client-side gate for MVP is acceptable since the board
      is still in-memory; note this clearly). Documented in `frontend/CLAUDE.md` and `lib/auth.ts`.
- [x] Frontend unit tests for the login form (success, failure, logout).
- [x] Playwright e2e: cannot see board before login; login reveals board; logout hides it.

Tests:
- Frontend: `npm run test:unit` and `npm run test:e2e` pass, including new auth tests.
- Manual: visiting `/` shows login; wrong creds rejected; correct creds show board; reload stays logged in;
  logout returns to login.

Success criteria:
- Board is only visible after logging in with `user` / `password`.
- Logout works and auth state behaves correctly across reloads.
- Comprehensive tests cover the auth flow.

---

## Part 5: Database modeling - DONE

Goal: design the SQLite schema for the Kanban (multi-user capable) and get sign-off. No code wiring yet.

Substeps:
- [x] Propose a relational schema supporting: multiple users; one board per user (MVP) but extensible to many;
      columns (ordered, renamable, fixed set for MVP); cards (title, details, position within column).
- [x] Represent the board state so it can be serialized to/from the frontend `BoardData` JSON shape
      (`columns[]` with ordered `cardIds`, `cards` keyed by id).
- [x] Document the schema and rationale in `docs/DATABASE.md` (tables, columns, types, keys, relationships,
      how ordering is stored, how it maps to the frontend JSON).
- [x] Include the seed/initial board definition strategy (what a new user's board looks like).
- [x] Note the JSON representation used by the API.
- [x] Get explicit user sign-off on `docs/DATABASE.md` before Part 6.

Decisions (signed off): save via full-replace `PUT /api/board`; a new board seeds 5 empty
columns (Backlog, Discovery, In Progress, Review, Done) with no cards.

Tests:
- No automated tests (design only). Validation = the documented schema can represent the existing
  `initialData` board without loss.

Success criteria:
- `docs/DATABASE.md` exists with a clear, simple schema and JSON mapping.
- Schema supports multiple users and round-trips the frontend board shape.
- User has signed off on the schema.

---

## Part 6: Backend API for the Kanban - DONE

Goal: implement API routes to read and modify a user's Kanban, backed by SQLite. DB auto-created.

Substeps:
- [x] Add SQLite access in the backend (lightweight; create DB + tables if missing at startup, using
      `DATABASE_PATH`).
- [x] Implement the schema from `docs/DATABASE.md` as migrations or create-table-on-startup.
- [x] `GET /api/board` - return the current user's board as `BoardData` JSON (create a seeded board if none).
- [x] `PUT /api/board` - replace/update the current user's board from `BoardData` JSON.
- [x] Chose the simpler approach: a single full-replace board `PUT` (signed off in Part 5); no
      finer-grained routes.
- [x] Identify the user for MVP (single hardcoded user is acceptable; keep multi-user-ready).
- [x] Backend unit tests (`pytest`) covering: empty DB seeds a board; read; update; move a card; rename a
      column; persistence across requests; DB file auto-created when absent.

Tests:
- `pytest` in `backend/` passes, including DB CRUD and auto-creation tests (use a temp DB path in tests).
- Manual: delete the DB file, start container, hit `GET /api/board` -> seeded board; `PUT` a change ->
  `GET` reflects it; restart container -> change persists.

Success criteria:
- API reads and writes the board to SQLite; DB is created if it does not exist.
- Changes persist across restarts (bind-mounted DB file).
- Backend tests are thorough and pass.

---

## Part 7: Frontend uses the Backend - DONE

Goal: replace in-memory board state with real API calls so the board is persistent.

Substeps:
- [x] Add a small API client in the frontend (`fetch` wrapper) for `GET`/`PUT /api/board`.
- [x] On load (after login), fetch the board from the API instead of using `initialData`
      (the hardcoded seed was removed from the frontend).
- [x] Route the existing handlers (`onRename`, `onAddCard`, `onDeleteCard`, drag move) through the API so
      changes persist; keep optimistic UI smooth (rename persists on blur).
- [x] Handle loading and error states minimally (no over-engineering).
- [x] Ensure the static-export build still works (client-side fetch to same-origin `/api`).
- [x] Update tests: frontend unit tests for the API client and updated handlers (mock fetch); Playwright
      e2e against the running container verifying persistence (change, reload, change is still there).

Tests:
- Frontend: `npm run test:unit` and `npm run test:e2e` pass.
- Backend: `pytest` passes.
- Manual: log in, move/add/edit a card, reload the page -> changes persist; restart container -> still there.

Success criteria:
- The board is fully backed by the API; reloading and restarting preserve state.
- Drag-and-drop, add/edit/delete card, rename column all persist via the backend.
- Tests are thorough and pass.

---

## Part 8: AI connectivity

Goal: prove the backend can call the AI via OpenRouter. Minimal "2+2" smoke test.

Substeps:
- [ ] Add an OpenRouter client in the backend using `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` from `.env`.
- [ ] Add a temporary/internal endpoint or script that asks the model "what is 2+2?" and returns the answer.
- [ ] Confirm the model id `openai/gpt-oss-120b` works via OpenRouter.
- [ ] Add error handling for missing/invalid API key (clear message, no crash loop).
- [ ] Add a test that exercises the AI path. Use a mocked OpenRouter response for CI determinism; keep a
      separate, manually-run live smoke test (skipped by default) for the real "2+2" check.

Tests:
- `pytest` passes with the mocked AI test.
- Manual (live): run the smoke test/endpoint with a real key -> response contains "4".

Success criteria:
- Backend can successfully call OpenRouter and get a model response.
- The "2+2" smoke test returns a correct answer with a real key.
- Missing-key case fails gracefully with a clear error.

---

## Part 9: AI over the Kanban with Structured Outputs

Goal: the AI receives the board JSON + the user's question + conversation history, and returns a
structured response containing a reply to the user and an optional board update.

Substeps:
- [ ] Define the structured output schema: `{ reply: string, board_update?: BoardData | null }`
      (or a documented diff form). Pick the shape that is simplest for the frontend to apply.
- [ ] Add `POST /api/chat` accepting `{ message: string, history: Message[] }`; the backend loads the
      current board, builds the prompt (board JSON + history + message), and calls the model with
      Structured Outputs.
- [ ] Validate the model's structured response; if it includes a `board_update`, persist it via the
      Part 6 board logic.
- [ ] Return `{ reply, board_changed: boolean }` (and the new board, or let the frontend re-fetch).
- [ ] Guardrails: validate the update against the schema before saving; reject malformed updates safely.
- [ ] Tests: `pytest` with mocked structured responses covering: reply only; reply + valid board update
      (persisted); malformed update (rejected, board unchanged). Document one live manual test.

Tests:
- `pytest` passes for all chat scenarios (mocked).
- Manual (live): ask "add a card 'Buy milk' to Backlog" -> reply returned and board updated in DB.

Success criteria:
- `/api/chat` always sends the board + question + history and returns a valid structured output.
- Valid board updates persist; invalid ones are rejected without corrupting the board.
- Tests are thorough and pass.

---

## Part 10: AI chat sidebar UI

Goal: a polished chat sidebar where the user talks to the AI; AI-driven board updates refresh the UI.

Substeps:
- [ ] Add a chat sidebar widget to the board UI, styled to the project color scheme (see root CLAUDE.md).
- [ ] Show conversation history (user + AI messages), an input box, and a send action with a pending state.
- [ ] Wire send to `POST /api/chat`, passing message + history; render the AI reply.
- [ ] When the response indicates the board changed, refresh the board automatically (re-fetch `GET /api/board`
      or apply the returned board) so the UI updates without a manual reload.
- [ ] Handle loading/empty/error states minimally and cleanly.
- [ ] Tests: frontend unit tests for the chat widget (render history, send, auto-refresh on board change,
      mock fetch); Playwright e2e: send a message that adds a card -> the new card appears on the board.

Tests:
- Frontend: `npm run test:unit` and `npm run test:e2e` pass, including chat tests.
- Backend: `pytest` passes.
- Manual (live): open the app, ask the AI to add/move a card -> reply appears and the board updates live.

Success criteria:
- A beautiful, working chat sidebar lets the user converse with the AI.
- AI-initiated board changes (from Structured Outputs) refresh the board automatically.
- The full MVP works end-to-end in the single Docker container: login -> persistent Kanban -> AI chat
  that can read and modify the board.
- Tests are comprehensive and pass.

---

## Final acceptance (whole app)

- One Docker container: `scripts/start` brings up login -> Kanban -> AI sidebar.
- Sign in with `user` / `password`; board persists in SQLite across restarts.
- AI chat reads the board and can create/edit/move one or more cards, with the UI refreshing automatically.
- All backend (`pytest`) and frontend (Vitest + Playwright) tests pass.
- Code follows the root CLAUDE.md standards (simple, idiomatic, no emojis, minimal README).
