"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAppSession } from "@/components/SessionProvider";
import { forkRun, getRun, replayRun, verifyRun } from "@/lib/api-client";
import { ProvenanceTimeline } from "@/components/ProvenanceTimeline";
import type { RunDetail, VerifyResult } from "@/lib/types";

export default function RunPage({ params }: { params: { runId: string } }) {
  const { data: session } = useAppSession();
  const token = session?.accessToken;
  const [run, setRun] = useState<RunDetail | null>(null);
  const [verify, setVerify] = useState<VerifyResult | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let active = true;
    const load = async () => {
      try {
        const r = await getRun(params.runId, token);
        if (active) setRun(r);
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : "Failed to load run");
      }
    };
    load();
    const id = setInterval(load, 3000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [params.runId, token]);

  async function onVerify() {
    if (!token) return;
    setVerifying(true);
    try {
      const result = await verifyRun(params.runId, token);
      setVerify(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Verify failed");
    } finally {
      setVerifying(false);
    }
  }

  async function onReplay() {
    if (!token) return;
    const child = await replayRun(params.runId, token);
    window.location.href = `/run/${child.id}`;
  }

  if (error) return <main><p style={{ color: "var(--danger)" }}>{error}</p></main>;
  if (!run) return <main><p>Loading run...</p></main>;

  return (
    <main>
      <Link href={`/brief/${run.brief_id}`}>← Back to brief</Link>
      <h1 style={{ marginTop: "1rem" }}>Provenance Viewer</h1>
      <p>
        Run <code>{run.id}</code> · Status: <span className="badge">{run.status}</span>
      </p>

      <div style={{ display: "flex", gap: "0.75rem", margin: "1rem 0", flexWrap: "wrap" }}>
        <button className="btn" onClick={onVerify} disabled={verifying || run.status !== "succeeded"}>
          {verifying ? "Verifying..." : "Verify Manifest"}
        </button>
        <button className="btn btn-secondary" onClick={onReplay}>
          Replay Run
        </button>
        <Link href={`/run/${run.id}/replay`} className="btn btn-secondary">
          Fork (swap model)
        </Link>
      </div>

      {verify && (
        <div className={`card ${verify.match ? "badge-success" : ""}`} style={{ marginBottom: "1rem", borderColor: verify.match ? "rgba(34,197,94,0.4)" : "rgba(239,68,68,0.4)" }}>
          <strong>{verify.match ? "✓ Verified — manifest matches asset" : "✗ Mismatch detected"}</strong>
          <p style={{ fontSize: "0.85rem", wordBreak: "break-all" }}>
            Expected: {verify.expected_sha256}<br />
            Actual: {verify.actual_sha256}
          </p>
        </div>
      )}

      <ProvenanceTimeline run={run} />

      {run.variants[0]?.asset_url && (
        <div className="card" style={{ marginTop: "1rem" }}>
          <h3>Final Asset</h3>
          <video src={run.variants[0].asset_url} controls style={{ width: "100%", borderRadius: 8 }} />
        </div>
      )}
    </main>
  );
}
