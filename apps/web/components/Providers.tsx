"use client";

import type { ReactNode } from "react";
import { AppSessionProvider } from "./SessionProvider";

export function Providers({ children }: { children: ReactNode }) {
  return <AppSessionProvider>{children}</AppSessionProvider>;
}
