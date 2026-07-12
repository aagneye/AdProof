"use client";

import { useAppSession } from "@/components/SessionProvider";

export function useAccessToken(): string | undefined {
  const { data: session } = useAppSession();
  return session?.accessToken;
}
