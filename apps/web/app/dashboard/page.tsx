"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BriefForm } from "@/components/BriefForm";
import { useAppSession } from "@/components/SessionProvider";
import { listBriefs } from "@/lib/api-client";
import type { Brief } from "@/lib/types";

export default function DashboardPage() {
  const { data: session } = useAppSession();
  const token = session?.accessToken;
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    listBriefs(token)
      .then((res) => setBriefs(res.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load briefs"))
      .finally(() => setLoading(false));
  }, [token]);

  const onCreated = (brief: Brief) => {
    setBriefs((prev) => [brief, ...prev.filter((b) => b.id !== brief.id)]);
  };

  return (
    <main>
      <h1>Dashboard</h1>
      <p>Create a brief and watch the pipeline generate verifiable ad variants.</p>

      <div className="card" style={{ margin: "1.5rem 0" }}>
        <h2>New Brief</h2>
        <BriefForm onCreated={onCreated} />
      </div>

      <h2>Your Briefs</h2>
      {loading ? (
        <p>Loading your briefs...</p>
      ) : error ? (
        <p style={{ color: "var(--danger)" }}>{error}</p>
      ) : briefs.length === 0 ? (
        <p>No briefs yet. Submit your first ad brief above.</p>
      ) : (
        <div className="grid" style={{ gap: "0.75rem" }}>
          {briefs.map((b) => (
            <Link key={b.id} href={`/brief/${b.id}`} className="card">
              <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
                <div>
                  <strong>{b.brand_name}</strong>
                  <p style={{ margin: "0.35rem 0 0" }}>{b.brief_text.slice(0, 100)}...</p>
                </div>
                <span className={`badge badge-${b.status === "done" ? "success" : b.status === "running" ? "running" : ""}`}>
                  {b.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
