"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getLibrary } from "@/lib/api-client";
import type { LibraryItem } from "@/lib/types";

export default function LibraryPage() {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [brand, setBrand] = useState("");
  const [provider, setProvider] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getLibrary({ brand: brand || undefined, provider: provider || undefined })
      .then((res) => setItems(res.items))
      .finally(() => setLoading(false));
  }, [brand, provider]);

  return (
    <main>
      <h1>Library</h1>
      <p>All generated variants with provenance links.</p>

      <div className="grid grid-2" style={{ margin: "1rem 0" }}>
        <input
          className="input"
          placeholder="Filter by brand"
          value={brand}
          onChange={(e) => setBrand(e.target.value)}
        />
        <input
          className="input"
          placeholder="Filter by provider"
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
        />
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : items.length === 0 ? (
        <p>No variants yet. Create a brief from the dashboard.</p>
      ) : (
        <div className="grid grid-2">
          {items.map((item) => (
            <div key={String(item.variant_id)} className="card">
              {item.thumbnail_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={item.thumbnail_url} alt="" style={{ width: "100%", borderRadius: 8, marginBottom: "0.75rem" }} />
              )}
              <strong>{item.brand_name}</strong>
              <p>{item.provider_summary}</p>
              <p style={{ fontSize: "0.8rem" }}>SHA: {item.sha256_hash.slice(0, 16)}...</p>
              <Link href={`/run/${item.run_id}`} className="btn btn-secondary" style={{ marginTop: "0.5rem" }}>
                View Provenance
              </Link>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
