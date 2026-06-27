"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";
import { isAuthenticated, setAuthenticated } from "@/lib/auth";

export const App = () => {
  const [authed, setAuthed] = useState(false);
  const [checked, setChecked] = useState(false);

  // Read the persisted session after mount (localStorage is client-only).
  useEffect(() => {
    setAuthed(isAuthenticated());
    setChecked(true);
  }, []);

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
