const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SyncedUser {
  access_token: string;
  user_id: string;
  email: string;
  name?: string | null;
  avatar_url?: string | null;
}

export async function syncSupabaseUser(input: {
  email: string;
  provider_user_id: string;
  name?: string | null;
  picture?: string | null;
}): Promise<SyncedUser> {
  console.log("[syncSupabaseUser] Syncing user:", input.email);
  const res = await fetch(`${API_URL}/auth/supabase`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: input.email,
      provider_user_id: input.provider_user_id,
      name: input.name,
      picture: input.picture,
    }),
    cache: "no-store",
  });
  if (!res.ok) {
    const errorText = await res.text();
    console.error(`[syncSupabaseUser] Failed: ${res.status}`, errorText);
    throw new Error(`Failed to sync user: ${res.status} ${errorText}`);
  }
  const data = await res.json();
  console.log("[syncSupabaseUser] Success, user_id:", data.user_id);
  return data;
}
