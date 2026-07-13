"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Session as SupabaseSession } from "@supabase/supabase-js";
import { getSupabaseClient } from "@/lib/supabase-client";
import { syncSupabaseUser } from "@/lib/sync-user";

export type AppSession = {
  accessToken: string;
  userId: string;
  user: {
    id?: string;
    email?: string | null;
    name?: string | null;
    image?: string | null;
  };
};

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  data: AppSession | null;
  status: AuthStatus;
  refresh: () => Promise<void>;
  signOut: () => Promise<void>;
};

const SESSION_STORAGE_KEY = "adproof.session";
const AUTH_COOKIE = "adproof_token";

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredSession(): AppSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const stored = window.localStorage.getItem(SESSION_STORAGE_KEY);
    return stored ? (JSON.parse(stored) as AppSession) : null;
  } catch {
    return null;
  }
}

function persistStoredSession(session: AppSession | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (session) {
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
    document.cookie = `${AUTH_COOKIE}=${encodeURIComponent(session.accessToken)}; path=/; max-age=604800; SameSite=Lax`;
  } else {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    document.cookie = `${AUTH_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
  }
}

function toAppSession(session: SupabaseSession): Promise<AppSession> {
  return syncSupabaseUser({
    email: session.user.email || "",
    provider_user_id: session.user.id,
    name: session.user.user_metadata?.full_name || session.user.user_metadata?.name || session.user.email || null,
    picture: session.user.user_metadata?.avatar_url || session.user.user_metadata?.picture || null,
  }).then((synced) => ({
    accessToken: synced.access_token,
    userId: synced.user_id,
    user: {
      id: synced.user_id,
      email: synced.email,
      name: synced.name || session.user.user_metadata?.full_name || session.user.email,
      image: synced.avatar_url || session.user.user_metadata?.avatar_url || session.user.user_metadata?.picture || null,
    },
  }));
}

export function AppSessionProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<AppSession | null>(() => readStoredSession());
  const [status, setStatus] = useState<AuthStatus>(() => (readStoredSession() ? "authenticated" : "loading"));

  const applySupabaseSession = useCallback(async (session: SupabaseSession | null) => {
    console.log("[SessionProvider] applySupabaseSession called with session:", session?.user.email);
    
    if (!session) {
      console.log("[SessionProvider] No session, setting unauthenticated");
      setData(null);
      setStatus("unauthenticated");
      persistStoredSession(null);
      return;
    }

    setStatus("loading");
    try {
      console.log("[SessionProvider] Converting Supabase session to app session");
      const nextSession = await toAppSession(session);
      console.log("[SessionProvider] Converted successfully, setting authenticated");
      setData(nextSession);
      setStatus("authenticated");
      persistStoredSession(nextSession);
    } catch (error) {
      console.error("[SessionProvider] Failed to sync Supabase session:", error);
      setData(null);
      setStatus("unauthenticated");
      persistStoredSession(null);
    }
  }, []);

  const refresh = useCallback(async () => {
    const supabase = getSupabaseClient();
    const { data: authData } = await supabase.auth.getSession();
    await applySupabaseSession(authData.session);
  }, [applySupabaseSession]);

  const signOut = useCallback(async () => {
    const supabase = getSupabaseClient();
    await supabase.auth.signOut();
    setData(null);
    setStatus("unauthenticated");
    persistStoredSession(null);
  }, []);

  useEffect(() => {
    let active = true;
    let subscription: { unsubscribe: () => void } | null = null;

    const initialize = async () => {
      try {
        const supabase = getSupabaseClient();
        const { data: authData } = await supabase.auth.getSession();
        if (!active) {
          return;
        }

        if (authData.session) {
          await applySupabaseSession(authData.session);
        } else {
          setStatus(readStoredSession() ? "authenticated" : "unauthenticated");
        }

        const { data: authListener } = supabase.auth.onAuthStateChange(async (_event, nextSession) => {
          if (active) {
            await applySupabaseSession(nextSession);
          }
        });
        subscription = authListener.subscription;
      } catch (error) {
        if (active) {
          console.error("Failed to initialize Supabase auth", error);
          setStatus("unauthenticated");
        }
      }
    };

    void initialize();

    return () => {
      active = false;
      subscription?.unsubscribe();
    };
  }, [applySupabaseSession]);

  const value = useMemo<AuthContextValue>(() => ({ data, status, refresh, signOut }), [data, status, refresh, signOut]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAppSession() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAppSession must be used within AppSessionProvider");
  }
  return value;
}
