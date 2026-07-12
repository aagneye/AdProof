"use client";

import Link from "next/link";
import { MockModeBadge } from "./MockModeBadge";
import { UserMenu } from "./UserMenu";
import { useAppSession } from "./SessionProvider";

export function NavHeader() {
  const { data: session, status } = useAppSession();

  return (
    <header style={{ borderBottom: "1px solid var(--border)" }}>
      <div
        style={{
          maxWidth: 1100,
          margin: "0 auto",
          padding: "1rem 1.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "1rem",
        }}
      >
        <nav className="nav" style={{ margin: 0, padding: 0, border: "none" }}>
          <Link href="/"><strong>AdProof</strong></Link>
          {status === "authenticated" && (
            <>
              <Link href="/dashboard">Dashboard</Link>
              <Link href="/library">Library</Link>
            </>
          )}
        </nav>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <MockModeBadge />
          {status === "authenticated" ? (
            <UserMenu email={session.user?.email} image={session.user?.image} />
          ) : (
            <>
              <Link href="/login" className="btn btn-secondary btn-sm">
                Log in
              </Link>
              <Link href="/signup" className="btn btn-sm">
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
