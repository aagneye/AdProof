import Link from "next/link";

export function HeroSection() {
  return (
    <section className="hero">
      <p className="hero-eyebrow">Cryptographic provenance for AI ads</p>
      <h1>Prove every ad is real.</h1>
      <p className="hero-lead">
        AdProof is an open AI ad pipeline with verifiable manifests on Backblaze B2.
        Generate variants, verify hashes, and fork runs with full lineage.
      </p>
      <div className="hero-actions">
        <Link href="/signup" className="btn">
          Get started free
        </Link>
        <Link href="/login" className="btn btn-secondary">
          Log in
        </Link>
      </div>
    </section>
  );
}
