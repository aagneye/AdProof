export function PipelineStatusStream({ runId }: { runId: string }) {
  return <div>Live pipeline progress for run {runId} via SSE</div>;
}
