"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getSupabaseClient } from "@/lib/supabase-client";
import { useAppSession } from "@/components/SessionProvider";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { status, refresh } = useAppSession();
  const [message, setMessage] = useState("Signing you in…");

  // Step 1: Exchange the OAuth code for a session
  useEffect(() => {
    const code = searchParams.get("code");
    const error = searchParams.get("error");
    const errorDescription = searchParams.get("error_description");

    if (error) {
      console.error("[AuthCallback] OAuth error:", error, errorDescription);
      setMessage(`Sign-in failed: ${errorDescription ?? error}`);
      setTimeout(() => router.replace("/login"), 3000);
      return;
    }

    if (code) {
      console.log("[AuthCallback] Exchanging OAuth code for session");
      setMessage("Completing sign-in…");
      const supabase = getSupabaseClient();
      supabase.auth.exchangeCodeForSession(code).then(({ error: exchangeError }) => {
        if (exchangeError) {
          console.error("[AuthCallback] Code exchange failed:", exchangeError.message);
          setMessage(`Sign-in failed: ${exchangeError.message}`);
          setTimeout(() => router.replace("/login"), 3000);
        } else {
          console.log("[AuthCallback] Code exchanged successfully, refreshing session");
          void refresh();
        }
      });
    } else {
      // No code param — might be a fragment-based flow, refresh to pick it up
      console.log("[AuthCallback] No code param, refreshing session");
      void refresh();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Step 2: Once session is ready, redirect
  useEffect(() => {
    console.log("[AuthCallback] Status:", status);
    if (status === "authenticated") {
      console.log("[AuthCallback] Authenticated! Redirecting to dashboard");
      const next = searchParams.get("next") ?? "/dashboard";
      router.replace(next);
    }
  }, [status, router, searchParams]);

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", flexDirection: "column", gap: "12px" }}>
      <p>{message}</p>
      {process.env.NODE_ENV === "development" && (
        <small style={{ color: "#888" }}>Status: {status}</small>
      )}
    </div>
  );
}
