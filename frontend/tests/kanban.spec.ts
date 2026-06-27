import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

// A known board state used to isolate board tests from each other and from
// previous runs (the backend persists data). Backlog holds one seed card.
const RESET_BOARD = {
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-seed"] },
    { id: "col-discovery", title: "Discovery", cardIds: [] },
    { id: "col-progress", title: "In Progress", cardIds: [] },
    { id: "col-review", title: "Review", cardIds: [] },
    { id: "col-done", title: "Done", cardIds: [] },
  ],
  cards: {
    "card-seed": { id: "card-seed", title: "Seed task", details: "Starting point." },
  },
};

const resetBoard = (request: APIRequestContext) =>
  request.put("/api/board", { data: RESET_BOARD });

const login = async (page: Page) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.locator('[data-testid^="column-"]').first()).toBeVisible();
};

test.describe("authentication", () => {
  test("shows login and hides the board before signing in", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);
  });

  test("rejects invalid credentials", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Username").fill("user");
    await page.getByLabel("Password").fill("wrong");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByText(/invalid username or password/i)).toBeVisible();
    await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);
  });

  test("logs in and back out", async ({ page }) => {
    await login(page);
    await page.getByRole("button", { name: /log out/i }).click();
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);
  });

  test("keeps the session after a reload", async ({ page }) => {
    await login(page);
    await page.reload();
    await expect(page.locator('[data-testid^="column-"]').first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "Sign in" })).toHaveCount(0);
  });
});

test.describe("kanban board", () => {
  test.beforeEach(async ({ page, request }) => {
    await resetBoard(request);
    await login(page);
  });

  test("loads the board from the backend", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
    await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
    await expect(page.getByText("Seed task")).toBeVisible();
  });

  test("adds a card to a column", async ({ page }) => {
    const firstColumn = page.locator('[data-testid^="column-"]').first();
    await firstColumn.getByRole("button", { name: /add a card/i }).click();
    await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
    await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
    await firstColumn.getByRole("button", { name: /add card/i }).click();
    await expect(firstColumn.getByText("Playwright card")).toBeVisible();
  });

  test("moves a card between columns", async ({ page }) => {
    const card = page.getByTestId("card-card-seed");
    const targetColumn = page.getByTestId("column-col-review");
    const cardBox = await card.boundingBox();
    const columnBox = await targetColumn.boundingBox();
    if (!cardBox || !columnBox) {
      throw new Error("Unable to resolve drag coordinates.");
    }

    await page.mouse.move(
      cardBox.x + cardBox.width / 2,
      cardBox.y + cardBox.height / 2
    );
    await page.mouse.down();
    await page.mouse.move(
      columnBox.x + columnBox.width / 2,
      columnBox.y + 120,
      { steps: 12 }
    );
    await page.mouse.up();
    await expect(targetColumn.getByTestId("card-card-seed")).toBeVisible();
  });

  test("persists a new card across a reload", async ({ page }) => {
    const firstColumn = page.locator('[data-testid^="column-"]').first();
    await firstColumn.getByRole("button", { name: /add a card/i }).click();
    await firstColumn.getByPlaceholder("Card title").fill("Persisted card");
    await firstColumn.getByPlaceholder("Details").fill("via backend");

    // Wait for the save to reach the backend before reloading.
    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes("/api/board") &&
          response.request().method() === "PUT" &&
          response.ok()
      ),
      firstColumn.getByRole("button", { name: /add card/i }).click(),
    ]);

    await page.reload();
    await expect(page.getByText("Persisted card")).toBeVisible();
  });
});
