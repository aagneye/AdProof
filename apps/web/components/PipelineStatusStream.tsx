import type { RunDetail } from "@/lib/types";
import { CostBadge } from "./CostBadge";
import { ManifestCard } from "./ManifestCard";

const STEP_ORDER = ["storyboard", "animate", "voiceover", "score", "compose"];

export function PipelineStatusStream({ run }: { run: RunDetail }) {
  const stepsByName = Object.fromEntries(run.steps.map((s) => [s.step_name, s]));

  return (
    <div className="card" style={{ marginTop: "1rem" }}>
      <h3>Pipeline Progress</h3>
      <div className="timeline">
        {STEP_ORDER.map((name) => {
          const step = stepsByName[name];
          const done = !!step;
          const running = !done && run.status === "running" && !run.steps.find((s) => !STEP_ORDER.slice(0, STEP_ORDER.indexOf(name)).includes(s.step_name) && s.step_name !== name);
          return (
            <div key={name} className="timeline-item">
              <div className={`timeline-dot ${done ? "done" : running ? "" : ""}`} />
              <div style={{ flex: 1 }}>
                <strong style={{ textTransform: "capitalize" }}>{name}</strong>
                {step ? (
                  <div style={{ marginTop: "0.35rem" }}>
                    <ManifestCard step={step} />
                    {step.cost_usd && step.provider && (
                      <div style={{ marginTop: "0.25rem" }}>
                        <CostBadge provider={step.provider} cost={step.cost_usd} />
                      </div>
                    )}
                  </div>
                ) : (
                  <p style={{ margin: "0.25rem 0 0" }}>
                    {run.status === "running" ? "Waiting..." : "Pending"}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
      {run.total_cost_usd && (
        <p style={{ marginTop: "1rem" }}>
          Total cost: <strong>${run.total_cost_usd}</strong>
        </p>
      )}
    </div>
  );
}
