"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAppSession } from "@/components/SessionProvider";
import { getBrief, getRun } from "@/lib/api-client";
import { PipelineStatusStream } from "@/components/PipelineStatusStream";
import { VariantGrid } from "@/components/VariantGrid";
import type { Brief, RunDetail } from "@/lib/types";

export default function BriefPage({ params }: { params: { briefId: string } }) {
  const { data: session } = useAppSession();
  const token = session?.accessToken;
  const [brief, setBrief] = useState<Brief | null>(null);
  const [run, setRun] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let active = true;
    const poll = async () => {
      try {
        const b = await getBrief(params.briefId, token);
        if (!active) return;
        setBrief(b);
        if (b.latest_run?.id || b.run_id) {
          const r = await getRun(String(b.latest_run?.id || b.run_id), token);
          if (!active) return;
          setRun(r);
        }
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : "Failed to load");
      }
    };
    poll();
    const id = setInterval(poll, 2000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [params.briefId, token]);

  if (error) return <main><p style={{ color: "var(--danger)" }}>{error}</p></main>;
  if (!brief) return <main><p>Loading brief...</p></main>;

  return (
    <main>
      <Link href="/dashboard">← Dashboard</Link>
      <h1 style={{ marginTop: "1rem" }}>{brief.brand_name}</h1>
      <p>{brief.brief_text}</p>
      <p>
        Status: <span className="badge">{brief.status}</span>
        {run && (
          <>
            {" "}· Run: <Link href={`/run/${run.id}`}>{run.id.slice(0, 8)}...</Link>
          </>
        )}
      </p>

      {run && <PipelineStatusStream run={run} />}

      {run?.status === "succeeded" && run.variants.length > 0 && (
        <div style={{ marginTop: "1.5rem" }}>
          <h2>Variants</h2>
          <VariantGrid variants={run.variants} runId={run.id} />
        </div>
      )}
    </main>
  );
}
