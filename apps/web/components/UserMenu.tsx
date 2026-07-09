"use client";

import { signOut } from "next-auth/react";

type UserMenuProps = {
  email?: string | null;
  image?: string | null;
};

export function UserMenu({ email, image }: UserMenuProps) {
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
      <button type="button" className="btn btn-secondary btn-sm" onClick={() => signOut({ callbackUrl: "/" })}>
        Sign out
      </button>
    </div>
  );
}
