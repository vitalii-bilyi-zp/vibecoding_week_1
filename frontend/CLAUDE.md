# Frontend

A Next.js Kanban board, statically exported (`output: "export"`) and served by the FastAPI
backend at `/`. A dummy login (`user` / `password`) gates the board. The board is loaded from
and persisted to the backend API, so changes survive reloads and restarts. The AI sidebar is
added in a later plan part.

## Stack

- Next.js 16 (App Router) + React 19
- TypeScript
- Tailwind CSS v4 (via `@tailwindcss/postcss`), config-less; theme tokens live in `src/app/globals.css`
- `@dnd-kit/core` + `@dnd-kit/sortable` for drag and drop
- Vitest + Testing Library (unit), Playwright (e2e)

## Layout

```
src/
  app/
    layout.tsx       Root layout; loads Space Grotesk (display) + Manrope (body) fonts, sets metadata
    page.tsx         Renders <App /> at /
    globals.css      Tailwind import + CSS custom properties (color tokens, fonts)
    favicon.ico
  components/
    App.tsx                Auth gate: shows LoginForm or KanbanBoard based on session (client)
    App.test.tsx           Auth gate flow tests (login, logout, persisted session)
    LoginForm.tsx          Dummy login form (user/password), shows error on bad creds
    LoginForm.test.tsx     LoginForm tests
    KanbanBoard.tsx        Top-level board; owns ALL board state and handlers; optional onLogout
    KanbanColumn.tsx       One column: droppable, editable title input, lists cards, hosts NewCardForm
    KanbanCard.tsx         One card: sortable/draggable, shows title + details, Remove button
    KanbanCardPreview.tsx  Static card visual used inside the drag overlay
    NewCardForm.tsx        Collapsible "Add a card" form (title + details)
    KanbanBoard.test.tsx   Component tests for the board
  lib/
    kanban.ts        Types + pure helpers (NO React). The data model and move logic.
    kanban.test.ts   Unit tests for moveCard / helpers
    auth.ts          Credential check + localStorage session helpers (client-side gate)
    auth.test.ts     Unit tests for auth helpers
    api.ts           fetchBoard / saveBoard - same-origin /api/board client
    api.test.ts      API client tests (mocked fetch)
  test/
    setup.ts         Vitest setup (jest-dom matchers)
    vitest.d.ts      Type augmentation for matchers
    helpers.ts       Test helpers: seeded empty board + stubFetch
tests/
  kanban.spec.ts     Playwright e2e (auth + board load/add/move + persistence across reload)
public/              Static assets
```

## Data model (`src/lib/kanban.ts`)

```ts
type Card = { id: string; title: string; details: string };
type Column = { id: string; title: string; cardIds: string[] };  // order is cardIds order
type BoardData = { columns: Column[]; cards: Record<string, Card> };  // cards keyed by id
```

- `moveCard(columns, activeId, overId)` - pure reorder/move; handles same-column reorder, move to another
  column, and dropping onto an empty column. Returns a new `columns` array; never mutates.
- `createId(prefix)` - generates `${prefix}-<random><time>` ids for new cards.

The board content comes from the backend (`GET /api/board`); there is no hardcoded seed in the
frontend anymore.

Note: column order is fixed (5 columns). Card order within a column is the array order of `cardIds`.

## State ownership and persistence

`KanbanBoard` is the only stateful component. It holds `board: BoardData | null` (null while
loading) and `activeCardId`, and passes handlers down: `onRename`, `onCommitRename`,
`onAddCard`, `onDeleteCard`, plus dnd-kit's `onDragStart`/`onDragEnd`. Children are
presentational.

On mount it loads the board via `fetchBoard()` (showing a loading then an error state as
needed). Mutations are optimistic: `update(next)` sets local state and fires `saveBoard(next)`
(full-board PUT). Column rename is the exception - it updates local state on each keystroke and
only persists on blur (`onCommitRename`), so typing a title does not PUT per character.

## Conventions

- Path alias `@/` -> `src/` (see `tsconfig.json`, `vitest.config.ts`).
- Colors/fonts referenced via CSS variables (`var(--primary-blue)`, `var(--font-display)`), defined in
  `globals.css`. Palette matches the project color scheme in the root CLAUDE.md.
- Components are arrow-function named exports. `KanbanBoard` is a client component (`"use client"`).

## Commands

```bash
npm install
npm run dev          # dev server on :3000
npm run build        # static export to ./out (output: "export")
npm run test:unit    # vitest run
npm run test:e2e     # playwright (auto-starts dev server)
npm run lint         # eslint
```

The build is a static export (`output: "export"` in `next.config.ts`), producing `out/`. The
Docker build (see `backend/Dockerfile`) builds this and copies `out/` into the backend's
`app/static`, so FastAPI serves it at `/`. SSR / Next route handlers must not be relied upon.

E2E against the running container: set `E2E_BASE_URL` (e.g. `http://127.0.0.1:8000`) and run
`npx playwright test` - Playwright then targets that URL instead of starting a dev server.

## Auth (MVP)

`lib/auth.ts` checks the hardcoded `user` / `password` and stores a session flag in
localStorage. `App` reads that flag after mount and renders `LoginForm` or `KanbanBoard`
(with a logout button). This is a client-side gate only; the backend board API is not yet
authenticated (single hardcoded user). Real enforcement is a future extension.

## Known gaps for the full app

- The backend board API is unauthenticated and uses one hardcoded user.
- No AI sidebar yet - added in the final plan part.
