// MVP auth: credentials are hardcoded and the session is a flag in localStorage.
// This is a client-side gate only; it is acceptable for the MVP because the board
// is still in-memory. Real enforcement moves to the backend once the API exists.

const AUTH_KEY = "pm-auth";
const VALID_USERNAME = "user";
const VALID_PASSWORD = "password";

export const checkCredentials = (username: string, password: string): boolean =>
  username === VALID_USERNAME && password === VALID_PASSWORD;

export const isAuthenticated = (): boolean =>
  typeof window !== "undefined" &&
  window.localStorage.getItem(AUTH_KEY) === "true";

export const setAuthenticated = (value: boolean): void => {
  if (typeof window === "undefined") {
    return;
  }
  if (value) {
    window.localStorage.setItem(AUTH_KEY, "true");
  } else {
    window.localStorage.removeItem(AUTH_KEY);
  }
};
