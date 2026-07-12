"use client";

import { getSupabaseClient } from "@/lib/supabase-client";

type GoogleAuthButtonProps = {
  label?: string;
  callbackUrl?: string;
};

export function GoogleAuthButton({
  label = "Continue with Google",
  callbackUrl = "/dashboard",
}: GoogleAuthButtonProps) {
  const handleSignIn = async () => {
    const supabase = getSupabaseClient();
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}${callbackUrl}`,
      },
    });

    if (error) {
      throw error;
    }
  };

  return (
    <button
      type="button"
      className="btn btn-google"
      onClick={() => {
        void handleSignIn().catch((error) => {
          console.error("Supabase sign-in failed", error);
        });
      }}
    >
      <GoogleIcon />
      {label}
    </button>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path
        fill="#FFC107"
        d="M43.611 20.083H42V20H24v8h11.303C33.654 32.657 29.083 36 24 36c-5.522 0-10-4.478-10-10s4.478-10 10-10c2.52 0 4.847.94 6.616 2.484l5.657-5.657C33.64 9.64 28.98 8 24 8 12.955 8 4 16.955 4 28s8.955 20 20 20 20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z"
      />
      <path
        fill="#FF3D00"
        d="M6.306 14.691l6.571 4.819C14.655 16.108 18.961 13 24 13c2.52 0 4.847.94 6.616 2.484l5.657-5.657C33.64 9.64 28.98 8 24 8 16.318 8 9.656 12.337 6.306 14.691z"
      />
      <path
        fill="#4CAF50"
        d="M24 48c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238C29.211 39.091 26.715 40 24 40c-5.078 0-9.398-3.343-10.835-7.965l-6.52 5.02C9.505 43.99 16.227 48 24 48z"
      />
      <path
        fill="#1976D2"
        d="M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 0 1-4.087 5.571l.003-.002 6.19 5.238C36.971 39.205 44 34 44 28c0-1.341-.138-2.65-.389-3.917z"
      />
    </svg>
  );
}
