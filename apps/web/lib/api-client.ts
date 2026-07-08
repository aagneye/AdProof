const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getHealth() {
  const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json() as Promise<{
    status: string;
    pipeline_mode: string;
    mock_mode: boolean;
  }>;
}

export async function createBrief(data: {
  brand_name: string;
  brief_text: string;
  reference_image_key?: string;
}) {
  const res = await fetch(`${API_URL}/briefs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to create brief: ${res.status}`);
  return res.json();
}

export async function getBrief(id: string) {
  const res = await fetch(`${API_URL}/briefs/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to get brief: ${res.status}`);
  return res.json();
}

export async function getRun(id: string) {
  const res = await fetch(`${API_URL}/runs/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to get run: ${res.status}`);
  return res.json();
}

export async function verifyRun(id: string) {
  const res = await fetch(`${API_URL}/runs/${id}/verify`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to verify run: ${res.status}`);
  return res.json();
}

export async function replayRun(id: string) {
  const res = await fetch(`${API_URL}/runs/${id}/replay`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to replay run: ${res.status}`);
  return res.json();
}

export async function forkRun(id: string, overrides: Record<string, unknown>) {
  const res = await fetch(`${API_URL}/runs/${id}/fork`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ overrides }),
  });
  if (!res.ok) throw new Error(`Failed to fork run: ${res.status}`);
  return res.json();
}

export async function getLibrary(params: {
  page?: number;
  limit?: number;
  provider?: string;
  brand?: string;
}) {
  const q = new URLSearchParams();
  if (params.page) q.set("page", String(params.page));
  if (params.limit) q.set("limit", String(params.limit));
  if (params.provider) q.set("provider", params.provider);
  if (params.brand) q.set("brand", params.brand);
  const res = await fetch(`${API_URL}/library?${q}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load library: ${res.status}`);
  return res.json();
}

export async function getManifestUrl(id: string) {
  const res = await fetch(`${API_URL}/runs/${id}/manifest`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to get manifest: ${res.status}`);
  return res.json();
}
