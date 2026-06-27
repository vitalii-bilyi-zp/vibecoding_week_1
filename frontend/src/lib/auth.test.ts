import { afterEach, describe, expect, it } from "vitest";
import { checkCredentials, isAuthenticated, setAuthenticated } from "@/lib/auth";

afterEach(() => {
  window.localStorage.clear();
});

describe("checkCredentials", () => {
  it("accepts the hardcoded credentials", () => {
    expect(checkCredentials("user", "password")).toBe(true);
  });

  it("rejects anything else", () => {
    expect(checkCredentials("user", "wrong")).toBe(false);
    expect(checkCredentials("admin", "password")).toBe(false);
    expect(checkCredentials("", "")).toBe(false);
  });
});

describe("session helpers", () => {
  it("is unauthenticated by default", () => {
    expect(isAuthenticated()).toBe(false);
  });

  it("persists and clears the session flag", () => {
    setAuthenticated(true);
    expect(isAuthenticated()).toBe(true);
    setAuthenticated(false);
    expect(isAuthenticated()).toBe(false);
  });
});
