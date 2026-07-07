import type { RunDetail } from "@/lib/types";
import { ManifestCard } from "./ManifestCard";

export function ProvenanceTimeline({ run }: { run: RunDetail }) {
  return (
    <div className="timeline">
      {run.parent_run_id && (
        <div className="card" style={{ marginBottom: "0.75rem" }}>
          <p style={{ margin: 0 }}>
            Forked from parent run: <code>{run.parent_run_id}</code>
          </p>
        </div>
      )}
      {run.steps.map((step) => (
        <div key={step.id} className="timeline-item">
          <div className={`timeline-dot ${step.status === "succeeded" || step.status === "fallback_used" ? "done" : "failed"}`} />
          <div style={{ flex: 1 }}>
            <strong style={{ textTransform: "capitalize" }}>{step.step_name}</strong>
            <div style={{ marginTop: "0.35rem" }}>
              <ManifestCard step={step} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
