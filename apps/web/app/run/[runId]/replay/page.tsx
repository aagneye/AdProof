"use client";

import { useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { forkRun } from "@/lib/api-client";

const ANIMATE_MODELS = [
  "kling-image2video-v2.1-master",
  "wan2.6-i2v",
  "pixverse-v5.6-i2v",
  "runway-gen4-turbo",
  "luma-ray-2",
];

export default function ReplayPage({ params }: { params: { runId: string } }) {
  const { data: session } = useSession();
  const token = session?.accessToken;
  const [model, setModel] = useState(ANIMATE_MODELS[1]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFork() {
    if (!token) {
      setError("You must be signed in to fork a run.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const child = await forkRun(
        params.runId,
        {
          animate: { provider: "gmicloud", model },
        },
        token,
      );
      window.location.href = `/run/${child.id}`;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fork failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <Link href={`/run/${params.runId}`}>← Back to provenance</Link>
      <h1 style={{ marginTop: "1rem" }}>Fork Run</h1>
      <p>Replay this run but override the animate step model. Child run gets <code>parent_run_id</code> set.</p>

      <div className="card" style={{ marginTop: "1rem" }}>
        <div className="field">
          <label className="label">Animate model override</label>
          <select className="select" value={model} onChange={(e) => setModel(e.target.value)}>
            {ANIMATE_MODELS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
        <button className="btn" onClick={handleFork} disabled={loading}>
          {loading ? "Forking..." : "Fork & Re-run Pipeline"}
        </button>
      </div>
    </main>
  );
}
