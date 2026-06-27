import { vi } from "vitest";
import type { BoardData } from "@/lib/kanban";

// A seeded, empty board matching what the backend returns for a new user.
export const emptyBoard: BoardData = {
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: [] },
    { id: "col-discovery", title: "Discovery", cardIds: [] },
    { id: "col-progress", title: "In Progress", cardIds: [] },
    { id: "col-review", title: "Review", cardIds: [] },
    { id: "col-done", title: "Done", cardIds: [] },
  ],
  cards: {},
};

// Stub global fetch: GET returns `board`; PUT echoes back the saved body.
export const stubFetch = (board: BoardData = emptyBoard) => {
  const fetchMock = vi.fn((_url: string, options?: RequestInit) => {
    const body =
      options?.method === "PUT" && typeof options.body === "string"
        ? JSON.parse(options.body)
        : board;
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(body),
    } as Response);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
};
