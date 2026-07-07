"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createBrief } from "@/lib/api-client";
import type { Brief } from "@/lib/types";

export function BriefForm({ onCreated }: { onCreated?: (brief: Brief) => void }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const form = new FormData(e.currentTarget);
    try {
      const brief = await createBrief({
        brand_name: String(form.get("brand_name")),
        brief_text: String(form.get("brief_text")),
      });
      onCreated?.(brief);
      router.push(`/brief/${brief.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create brief");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="field">
        <label className="label">Brand Name</label>
        <input className="input" type="text" name="brand_name" required placeholder="ColdBrew Co" />
      </div>
      <div className="field">
        <label className="label">Brief</label>
        <textarea
          className="textarea"
          name="brief_text"
          required
          placeholder="30-sec ad for cold brew brand, upbeat, TikTok-native"
        />
      </div>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      <button className="btn" type="submit" disabled={loading}>
        {loading ? "Creating..." : "Create Brief & Run Pipeline"}
      </button>
    </form>
  );
}
