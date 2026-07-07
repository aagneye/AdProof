"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BriefForm } from "@/components/BriefForm";
import { getBrief } from "@/lib/api-client";
import type { Brief } from "@/lib/types";

export default function DashboardPage() {
  const [briefs, setBriefs] = useState<Brief[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem("adproof_briefs");
    if (stored) {
      const ids: string[] = JSON.parse(stored);
      Promise.all(ids.map((id) => getBrief(id).catch(() => null))).then((results) => {
        setBriefs(results.filter(Boolean) as Brief[]);
      });
    }
  }, []);

  const onCreated = (brief: Brief) => {
    const stored = localStorage.getItem("adproof_briefs");
    const ids: string[] = stored ? JSON.parse(stored) : [];
    if (!ids.includes(brief.id)) ids.unshift(brief.id);
    localStorage.setItem("adproof_briefs", JSON.stringify(ids.slice(0, 20)));
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

      <h2>Recent Briefs</h2>
      {briefs.length === 0 ? (
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
