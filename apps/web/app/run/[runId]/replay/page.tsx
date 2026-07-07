export default function ReplayPage({ params }: { params: { runId: string } }) {
  return (
    <main>
      <h1>Fork / Replay — Run {params.runId}</h1>
      <p>Override one step provider/model and re-run</p>
    </main>
  );
}
