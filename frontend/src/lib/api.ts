import type { BoardData } from "@/lib/kanban";

// Same-origin API: in production FastAPI serves both the static site and /api.

export const fetchBoard = async (): Promise<BoardData> => {
  const response = await fetch("/api/board");
  if (!response.ok) {
    throw new Error(`Failed to load board (${response.status})`);
  }
  return response.json();
};

export const saveBoard = async (board: BoardData): Promise<void> => {
  const response = await fetch("/api/board", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(board),
  });
  if (!response.ok) {
    throw new Error(`Failed to save board (${response.status})`);
  }
};
