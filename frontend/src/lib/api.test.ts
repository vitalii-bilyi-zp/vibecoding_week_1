import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchBoard, saveBoard } from "@/lib/api";
import { emptyBoard } from "@/test/helpers";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("fetchBoard GETs /api/board and returns the json", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(emptyBoard) } as Response)
    );
    vi.stubGlobal("fetch", fetchMock);

    const board = await fetchBoard();

    expect(fetchMock).toHaveBeenCalledWith("/api/board");
    expect(board).toEqual(emptyBoard);
  });

  it("fetchBoard throws on a non-ok response", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: false, status: 500 } as Response)));
    await expect(fetchBoard()).rejects.toThrow(/500/);
  });

  it("saveBoard PUTs the board as json", async () => {
    const fetchMock = vi.fn(() => Promise.resolve({ ok: true } as Response));
    vi.stubGlobal("fetch", fetchMock);

    await saveBoard(emptyBoard);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/board",
      expect.objectContaining({
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(emptyBoard),
      })
    );
  });

  it("saveBoard throws on a non-ok response", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: false, status: 400 } as Response)));
    await expect(saveBoard(emptyBoard)).rejects.toThrow(/400/);
  });
});
