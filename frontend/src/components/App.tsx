"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";
import { isAuthenticated, setAuthenticated } from "@/lib/auth";

export const App = () => {
  // `checked` is false until the persisted session is read after mount.
  const [session, setSession] = useState({ authed: false, checked: false });
  const { authed, checked } = session;

  // localStorage is client-only, so the session must be read after mount; for a
  // static export, reading it during render would cause a hydration mismatch.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional one-time client read
    setSession({ authed: isAuthenticated(), checked: true });
  }, []);

  const setAuthed = (value: boolean) =>
    setSession({ authed: value, checked: true });

  if (!checked) {
    return null;
  }

  if (!authed) {
    return (
      <LoginForm
        onSuccess={() => {
          setAuthenticated(true);
          setAuthed(true);
        }}
      />
    );
  }

  return (
    <KanbanBoard
      onLogout={() => {
        setAuthenticated(false);
        setAuthed(false);
      }}
    />
  );
};
