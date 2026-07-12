"use client";

/**
 * Supabase OAuth callback handler.
 * Supabase redirects here after Google sign-in. The SessionProvider
 * detects the session from the URL fragment and sets the auth cookie,
 * then this page redirects to the original destination.
 */

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAppSession } from "@/components/SessionProvider";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { status } = useAppSession();

  useEffect(() => {
    if (status === "authenticated") {
      const next = searchParams.get("next") ?? "/dashboard";
      router.replace(next);
    } else if (status === "unauthenticated") {
      router.replace("/login");
    }
    // while "loading", keep waiting
  }, [status, router, searchParams]);

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
      <p>Signing you in…</p>
    </div>
  );
}
