import "./globals.css";
import Link from "next/link";

export const metadata = {
  title: "AdProof",
  description: "AI ads with cryptographic provenance",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header style={{ borderBottom: "1px solid var(--border)" }}>
          <div style={{ maxWidth: 1100, margin: "0 auto", padding: "1rem 1.5rem" }}>
            <nav className="nav" style={{ margin: 0, padding: 0, border: "none" }}>
              <Link href="/"><strong>AdProof</strong></Link>
              <Link href="/dashboard">Dashboard</Link>
              <Link href="/library">Library</Link>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
