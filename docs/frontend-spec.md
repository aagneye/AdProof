# AdProof — Frontend Specification

**Stack:** Next.js 14+ (App Router), TypeScript, deployed to **Vercel**.

---

## 1. App Structure

```
apps/web/
├── app/
│   ├── (marketing)/
│   │   └── page.tsx              # Landing page
│   ├── dashboard/
│   │   ├── page.tsx              # Brief list + "New Brief" CTA
│   │   └── layout.tsx            # Dashboard shell (nav, auth)
│   ├── brief/[briefId]/
│   │   ├── page.tsx              # Generation progress + variant picker
│   │   └── loading.tsx           # Skeleton while loading
│   ├── run/[runId]/
│   │   ├── page.tsx              # Provenance viewer (differentiator)
│   │   └── replay/page.tsx       # Fork/replay UI
│   ├── library/
│   │   └── page.tsx              # Versioned asset library
│   └── api/
│       └── webhooks/b2/route.ts  # B2 event notification receiver
├── components/
├── lib/
│   ├── api-client.ts
│   └── types.ts
└── package.json
```

---

## 2. Pages

### 2.1 Landing (`/`)

Marketing page. Pitch line, feature highlights (provenance, multi-provider, self-serve), CTA to dashboard.

### 2.2 Dashboard (`/dashboard`)

- List all briefs for the current user (brand name, status, created date)
- "New Brief" button → brief form modal or inline form
- Status badges: `pending` | `running` | `done` | `failed`

### 2.3 New Brief (form on dashboard or `/dashboard/new`)

| Field | Type | Required |
|-------|------|----------|
| Brand name | text | yes |
| Brief text | textarea | yes |
| Reference image | file upload | no |

On submit: `POST /briefs` → redirect to `/brief/[briefId]`.

### 2.4 Brief Progress (`/brief/[briefId]`)

Live step-by-step status powered by SSE (not polling):

```
storyboard ✓ → animating (3 models) → voiceover → score → compose
```

Shows:

- `PipelineStatusStream` — real-time progress via SSE/WebSocket
- When done: `VariantGrid` with thumbnails, provider badges, cost, "Select" button

### 2.5 Provenance Viewer (`/run/[runId]`) — **Priority Screen**

The screen that wins judging criteria. Must include:

| Element | Component | Behavior |
|---------|-----------|----------|
| Step timeline | `ProvenanceTimeline` | Visual chain of steps; `parent_run_id` lineage |
| Provider used per step | `ManifestCard` | Actual provider post-fallback; flag if fallback triggered |
| Cost per step | `CostBadge` | Provider + USD per variant |
| Verify button | — | `GET /runs/{id}/verify` → green check or mismatch warning |
| Fork button | — | Navigate to `/run/[runId]/replay` |
| Manifest download | — | Signed URL from `GET /runs/{id}/manifest` |

### 2.6 Fork / Replay (`/run/[runId]/replay`)

- Show current run's step config
- Allow overriding one step's provider/model (e.g. swap Kling → Runway)
- `POST /runs/{id}/fork` → new run with `parent_run_id` set
- Redirect to new brief/run progress page

### 2.7 Library (`/library`)

Searchable/filterable grid of all generated variants:

- Filters: provider, date range, brand name
- Each card: thumbnail, brand, provider summary, cost, link to provenance viewer
- `GET /library?page=1&provider=kling&brand=...`

---

## 3. Components

| Component | Purpose |
|-----------|---------|
| `BriefForm` | Brand name, brief text, optional image upload |
| `VariantGrid` | Grid of finished variants with select action |
| `ProvenanceTimeline` | Parent_run_id chain visual; step status icons |
| `ManifestCard` | Single step manifest summary (provider, model, SHA-256, latency) |
| `CostBadge` | Provider name + cost USD for a step or variant |
| `PipelineStatusStream` | Live progress via SSE; subscribes to run events |

---

## 4. API Client (`lib/api-client.ts`)

Base URL from `NEXT_PUBLIC_API_URL`.

```typescript
// Key methods (implement against backend api-spec.md)
createBrief(data: CreateBriefRequest): Promise<Brief>
getBrief(id: string): Promise<BriefWithRun>
getRun(id: string): Promise<RunDetail>
replayRun(id: string): Promise<Run>
forkRun(id: string, overrides: ForkOverrides): Promise<Run>
verifyRun(id: string): Promise<VerifyResult>
getManifestUrl(id: string): Promise<string>
getLibrary(params: LibraryQuery): Promise<PaginatedVariants>
```

Types in `lib/types.ts` mirror backend Pydantic schemas (or import from `packages/shared-types`).

---

## 5. Real-Time Updates (SSE)

Flow:

1. B2 fires event notification on `variants/*/final.mp4` PUT
2. `app/api/webhooks/b2/route.ts` receives webhook
3. Webhook handler updates brief status (via backend or direct DB — prefer backend callback)
4. SSE channel pushes update to connected clients on `/brief/[briefId]`
5. `PipelineStatusStream` re-renders → variant grid appears

Alternative during dev: poll `GET /briefs/{id}` every 5s until `status=done`.

---

## 6. B2 Webhook Route (`app/api/webhooks/b2/route.ts`)

- Receives B2 event notification payload (S3-compatible JSON)
- Validates source (optional: shared secret header)
- On `PutObject` for `variants/*/final.mp4`:
  - Extract `run_id` / `variant_id` from key
  - Notify backend or flip brief status
  - Broadcast SSE event

---

## 7. Environment Variables (Frontend)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000   # dev
NEXT_PUBLIC_API_URL=https://api.adproof.app # prod
B2_WEBHOOK_SECRET=                          # optional validation
```

---

## 8. Build & Deploy

```bash
npm run build    # production build
npm run start    # production server (local test)
```

**Production host: Vercel**

- Connect Git repo, set root directory to `apps/web`
- Add env vars in Vercel dashboard
- B2 webhook URL: `https://<your-domain>/api/webhooks/b2`

See [deployment.md](./deployment.md) for full hosting guide.

---

## 9. UI Priorities (Build Order)

1. Brief form → progress page → variant grid (MVP flow)
2. Provenance viewer + verify button (differentiator — do not defer)
3. Fork/replay UI
4. Library page
5. Landing page polish
