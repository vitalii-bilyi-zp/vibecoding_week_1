# Frontend (existing demo)

A frontend-only Next.js demo of the Kanban board. State lives in React memory only -
there is no backend, no auth, and no persistence yet. Reloading the page resets the board
to `initialData`. Later plan parts wire this to the FastAPI backend, add auth, and add the AI sidebar.

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
    page.tsx         Renders <KanbanBoard /> at /
    globals.css      Tailwind import + CSS custom properties (color tokens, fonts)
    favicon.ico
  components/
    KanbanBoard.tsx        Top-level board; owns ALL board state and handlers (client component)
    KanbanColumn.tsx       One column: droppable, editable title input, lists cards, hosts NewCardForm
    KanbanCard.tsx         One card: sortable/draggable, shows title + details, Remove button
    KanbanCardPreview.tsx  Static card visual used inside the drag overlay
    NewCardForm.tsx        Collapsible "Add a card" form (title + details)
    KanbanBoard.test.tsx   Component tests for the board
  lib/
    kanban.ts        Types + pure helpers (NO React). The data model and move logic.
    kanban.test.ts   Unit tests for moveCard / helpers
  test/
    setup.ts         Vitest setup (jest-dom matchers)
    vitest.d.ts      Type augmentation for matchers
tests/
  kanban.spec.ts     Playwright e2e (load board, add card, move card)
public/              Static assets
```

## Data model (`src/lib/kanban.ts`)

```ts
type Card = { id: string; title: string; details: string };
type Column = { id: string; title: string; cardIds: string[] };  // order is cardIds order
type BoardData = { columns: Column[]; cards: Record<string, Card> };  // cards keyed by id
```

- `initialData` - seed board with 5 columns (Backlog, Discovery, In Progress, Review, Done) and 8 cards.
- `moveCard(columns, activeId, overId)` - pure reorder/move; handles same-column reorder, move to another
  column, and dropping onto an empty column. Returns a new `columns` array; never mutates.
- `createId(prefix)` - generates `${prefix}-<random><time>` ids for new cards.

Note: column order is fixed (5 columns). Card order within a column is the array order of `cardIds`.

## State ownership

`KanbanBoard` is the only stateful component. It holds `board: BoardData` and `activeCardId`, and passes
handlers down: `onRename`, `onAddCard`, `onDeleteCard`, plus dnd-kit's `onDragStart`/`onDragEnd`.
Children are presentational and call these handlers. When backend persistence is added, these handlers are
the integration points to swap local `setBoard` updates for API calls.

## Conventions

- Path alias `@/` -> `src/` (see `tsconfig.json`, `vitest.config.ts`).
- Colors/fonts referenced via CSS variables (`var(--primary-blue)`, `var(--font-display)`), defined in
  `globals.css`. Palette matches the project color scheme in the root CLAUDE.md.
- Components are arrow-function named exports. `KanbanBoard` is a client component (`"use client"`).

## Commands

```bash
npm install
npm run dev          # dev server on :3000
npm run build        # production build (currently a Next server build, not static export)
npm run test:unit    # vitest run
npm run test:e2e     # playwright (auto-starts dev server)
npm run lint         # eslint
```

## Known gaps for the full app

- Build is a standard Next server build. Plan Part 3 switches to `output: 'export'` so FastAPI can serve
  static files. SSR / Next route handlers must not be relied upon.
- No backend, no API client, no auth, no persistence, no AI sidebar - all added in later plan parts.
