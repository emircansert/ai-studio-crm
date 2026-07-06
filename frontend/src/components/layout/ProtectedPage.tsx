"use client";

import { AppShell } from "@/components/layout/AppShell";

export function ProtectedPage({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
