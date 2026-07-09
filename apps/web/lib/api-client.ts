const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

import { authHeaders, readHeaders } from "./api-auth";

export async function getHealth() {
  const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json() as Promise<{
    status: string;
    pipeline_mode: string;
    mock_mode: boolean;
  }>;
}

export async function listBriefs(token: string) {
  const res = await fetch(`${API_URL}/briefs`, {
    headers: readHeaders(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to list briefs: ${res.status}`);
  return res.json();
}

export async function createBrief(
  data: {
    brand_name: string;
    brief_text: string;
    reference_image_key?: string;
  },
  token: string,
) {
  const res = await fetch(`${API_URL}/briefs`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to create brief: ${res.status}`);
  return res.json();
}

export async function getBrief(id: string, token: string) {
  const res = await fetch(`${API_URL}/briefs/${id}`, {
    headers: readHeaders(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to get brief: ${res.status}`);
  return res.json();
}

export async function getRun(id: string, token: string) {
  const res = await fetch(`${API_URL}/runs/${id}`, {
    headers: readHeaders(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to get run: ${res.status}`);
  return res.json();
}

export async function verifyRun(id: string, token: string) {
  const res = await fetch(`${API_URL}/runs/${id}/verify`, {
    headers: readHeaders(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to verify run: ${res.status}`);
  return res.json();
}

export async function replayRun(id: string, token: string) {
  const res = await fetch(`${API_URL}/runs/${id}/replay`, {
    method: "POST",
    headers: readHeaders(token),
  });
  if (!res.ok) throw new Error(`Failed to replay run: ${res.status}`);
  return res.json();
}

export async function forkRun(id: string, overrides: Record<string, unknown>, token: string) {
  const res = await fetch(`${API_URL}/runs/${id}/fork`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ overrides }),
  });
  if (!res.ok) throw new Error(`Failed to fork run: ${res.status}`);
  return res.json();
}

export async function getLibrary(
  params: {
    page?: number;
    limit?: number;
    provider?: string;
    brand?: string;
  },
  token: string,
) {
  const q = new URLSearchParams();
  if (params.page) q.set("page", String(params.page));
  if (params.limit) q.set("limit", String(params.limit));
  if (params.provider) q.set("provider", params.provider);
  if (params.brand) q.set("brand", params.brand);
  const res = await fetch(`${API_URL}/library?${q}`, {
    headers: readHeaders(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to load library: ${res.status}`);
  return res.json();
}

export async function getManifestUrl(id: string, token: string) {
  const res = await fetch(`${API_URL}/runs/${id}/manifest`, {
    headers: readHeaders(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to get manifest: ${res.status}`);
  return res.json();
}
