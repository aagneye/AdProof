# AdProof — REST API Specification

**Base URL (dev):** `http://localhost:8000`  
**Base URL (prod):** `https://api.<your-domain>`  
**OpenAPI:** `/docs` (Swagger UI), `/redoc`

All routes except `GET /health` and `POST /auth/google` require:

```
Authorization: Bearer <access_token>
```

Obtain a token by signing in with Google on the frontend (NextAuth syncs via `POST /auth/google`).

---

## 0. Auth

### `POST /auth/google`

Upsert user from Google OAuth profile (called by NextAuth server).

**Request:**

```json
{
  "email": "user@example.com",
  "google_id": "google-sub-id",
  "name": "Jane Doe",
  "picture": "https://..."
}
```

**Response `200`:**

```json
{
  "access_token": "jwt...",
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "Jane Doe",
  "avatar_url": "https://..."
}
```

### `GET /auth/me`

Returns the authenticated user profile. Requires bearer token.

---

## 1. Briefs

### `POST /briefs`

Create a brief and enqueue a pipeline run.

**Request:**

```json
{
  "brand_name": "ColdBrew Co",
  "brief_text": "30-sec ad for cold brew brand, upbeat, TikTok-native",
  "reference_image_key": "briefs/{brief_id}/reference-image.jpg"
}
```

Optional: multipart upload for reference image (returns `reference_image_key`).

**Response `201`:**

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "brand_name": "ColdBrew Co",
  "brief_text": "...",
  "reference_image_key": null,
  "status": "pending",
  "created_at": "2026-07-07T12:00:00Z",
  "run_id": "uuid"
}
```

Side effects: creates `briefs` row, creates `runs` row (`status=queued`), enqueues job. Requires bearer token; brief is owned by authenticated user.

---

### `GET /briefs`

List briefs for the authenticated user (newest first, max 50).

**Response `200`:**

```json
{
  "items": [ { "id": "uuid", "brand_name": "...", "status": "done", "...": "..." } ],
  "total": 3
}
```

---

### `GET /briefs/{id}`

Get brief with latest run status.

**Response `200`:**

```json
{
  "id": "uuid",
  "brand_name": "ColdBrew Co",
  "brief_text": "...",
  "status": "running",
  "created_at": "2026-07-07T12:00:00Z",
  "latest_run": {
    "id": "uuid",
    "status": "running",
    "started_at": "2026-07-07T12:00:05Z",
    "total_cost_usd": null
  }
}
```

---

## 2. Runs

### `GET /runs/{id}`

Full run detail: steps, providers, costs, manifest keys.

**Response `200`:**

```json
{
  "id": "uuid",
  "brief_id": "uuid",
  "parent_run_id": null,
  "status": "succeeded",
  "started_at": "2026-07-07T12:00:05Z",
  "finished_at": "2026-07-07T12:05:30Z",
  "total_cost_usd": "1.2345",
  "steps": [
    {
      "id": "uuid",
      "step_name": "storyboard",
      "provider": "gmicloud",
      "model": "seedream-5.0-lite",
      "status": "succeeded",
      "fallback_triggered": false,
      "cost_usd": "0.0500",
      "latency_ms": 3200,
      "manifest_key": "runs/{run_id}/steps/storyboard/{step_id}.manifest.json",
      "asset_key": "runs/{run_id}/steps/storyboard/{step_id}.png"
    }
  ],
  "variants": [
    {
      "id": "uuid",
      "asset_key": "runs/{run_id}/variants/{variant_id}/final.mp4",
      "thumbnail_key": "runs/{run_id}/variants/{variant_id}/thumbnail.jpg",
      "manifest_key": "runs/{run_id}/variants/{variant_id}/manifest.json",
      "sha256_hash": "abc123...",
      "provider_summary": "kling + elevenlabs + minimax",
      "selected": false
    }
  ]
}
```

---

### `POST /runs/{id}/replay`

Replay a run via Genblaze using stored manifest. Creates new run with `parent_run_id` set.

**Request:** (empty body)

**Response `201`:**

```json
{
  "id": "new-run-uuid",
  "parent_run_id": "original-run-uuid",
  "status": "queued"
}
```

---

### `POST /runs/{id}/fork`

Replay with one step's provider/model overridden.

**Request:**

```json
{
  "overrides": {
    "animate": {
      "provider": "runway",
      "model": "runway-gen4-turbo"
    }
  }
}
```

**Response `201`:** Same as replay.

---

### `GET /runs/{id}/manifest`

Returns a signed URL to the rolled-up `manifest.json`.

**Response `200`:**

```json
{
  "manifest_key": "runs/{run_id}/variants/{variant_id}/manifest.json",
  "signed_url": "https://s3...",
  "expires_at": "2026-07-07T13:00:00Z"
}
```

---

### `GET /runs/{id}/verify`

Re-computes SHA-256 of final asset and compares with manifest claim.

**Response `200`:**

```json
{
  "match": true,
  "expected_sha256": "abc123...",
  "actual_sha256": "abc123...",
  "manifest_key": "runs/{run_id}/variants/{variant_id}/manifest.json",
  "verified_at": "2026-07-07T12:10:00Z"
}
```

**Response `200` (mismatch):**

```json
{
  "match": false,
  "expected_sha256": "abc123...",
  "actual_sha256": "def456...",
  "manifest_key": "...",
  "verified_at": "..."
}
```

---

## 3. Library

### `GET /library`

Paginated browse of all variants across briefs.

**Query params:**

| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page number (default 1) |
| `limit` | int | Items per page (default 20, max 100) |
| `provider` | string | Filter by provider in `provider_summary` |
| `brand` | string | Filter by brand name (partial match) |
| `from` | ISO date | Created after |
| `to` | ISO date | Created before |

**Response `200`:**

```json
{
  "items": [
    {
      "variant_id": "uuid",
      "run_id": "uuid",
      "brief_id": "uuid",
      "brand_name": "ColdBrew Co",
      "thumbnail_url": "https://signed...",
      "provider_summary": "kling + elevenlabs + minimax",
      "sha256_hash": "abc123...",
      "total_cost_usd": "1.2345",
      "created_at": "2026-07-07T12:05:30Z"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 42
}
```

---

## 4. Webhooks

### `POST /webhooks/provider`

Provider async callbacks (if any step uses webhook-based completion).

**Request:** Provider-specific payload.

**Response `200`:** `{ "received": true }`

---

## 5. Health

### `GET /health`

**Response `200`:**

```json
{
  "status": "ok",
  "db": "connected",
  "redis": "connected"
}
```

---

## 6. Error Responses

Standard format:

```json
{
  "detail": "Brief not found",
  "status_code": 404
}
```

| Code | When |
|------|------|
| 400 | Invalid fork overrides |
| 404 | Brief/run not found |
| 422 | Validation error on POST /briefs |
| 500 | Pipeline failure, B2 error |
| 503 | DB/Redis unavailable |

---

## 7. CORS

Allow origins:

- `http://localhost:3000` (dev)
- `https://<vercel-domain>` (prod)

---

## 8. Auth (MVP)

Hackathon MVP may skip auth. When added:

- `Authorization: Bearer <token>` header
- All briefs scoped to authenticated `user_id`
