import Link from "next/link";

export default function MarketingPage() {
  return (
    <main>
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h1>AdProof</h1>
        <p style={{ fontSize: "1.15rem", color: "var(--text)" }}>
          Absurd for everyone, and every ad it makes can prove it&apos;s real.
        </p>
        <p>
          Open, self-serve AI ad pipeline with cryptographic provenance on Backblaze B2.
          Generate 30–60s video variants, verify manifests, fork runs with full lineage.
        </p>
        <Link href="/dashboard" className="btn" style={{ marginTop: "1rem" }}>
          Open Dashboard
        </Link>
      </div>
      <div className="grid grid-2">
        <div className="card">
          <h3>Multi-provider pipeline</h3>
          <p>Storyboard → animate (concurrent fan-out) → voiceover → score → compose</p>
        </div>
        <div className="card">
          <h3>Provenance manifests</h3>
          <p>SHA-256 per step, Object Lock on B2, verify anytime</p>
        </div>
        <div className="card">
          <h3>Fork & replay</h3>
          <p>Swap providers and trace parent_run_id lineage</p>
        </div>
      </div>
    </main>
  );
}
