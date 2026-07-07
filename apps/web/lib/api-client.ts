const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  const res = await fetch(`${API_URL}/briefs/${id}`);
  if (!res.ok) throw new Error(`Failed to get brief: ${res.status}`);
  return res.json();
}

export async function getRun(id: string) {
  const res = await fetch(`${API_URL}/runs/${id}`);
  if (!res.ok) throw new Error(`Failed to get run: ${res.status}`);
  return res.json();
}

export async function verifyRun(id: string) {
  const res = await fetch(`${API_URL}/runs/${id}/verify`);
  if (!res.ok) throw new Error(`Failed to verify run: ${res.status}`);
  return res.json();
}
