"use client";

import { getSupabaseClient } from "@/lib/supabase-client";

type UserMenuProps = {
  email?: string | null;
  image?: string | null;
};

export function UserMenu({ email, image }: UserMenuProps) {
  const handleSignOut = async () => {
    const supabase = getSupabaseClient();
    await supabase.auth.signOut();
    window.location.href = "/";
  };

  return (
    <div className="user-menu">
      {image ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={image} alt="" className="user-avatar" />
      ) : (
        <span className="user-avatar user-avatar-fallback">
          {(email || "?").slice(0, 1).toUpperCase()}
        </span>
      )}
      <span className="user-email">{email}</span>
      <button type="button" className="btn btn-secondary btn-sm" onClick={() => void handleSignOut()}>
        Sign out
      </button>
    </div>
  );
}
