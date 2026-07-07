# AdProof — Build Order

Day-by-day implementation plan for the hackathon. Follow this sequence.

---

## Day 1 — Infrastructure

**Goal:** Local dev environment and cloud storage ready.

| # | Task | Files | Done When |
|---|------|-------|-----------|
| 1 | Docker Compose (Postgres + Redis) | `infra/docker-compose.yml` | `docker compose up` works |
| 2 | B2 bucket setup script | `infra/b2-bucket-setup.py` | Bucket created, Object Lock + lifecycle configured |
| 3 | Alembic migration for schema | `apps/worker/db/migrations/` | `alembic upgrade head` creates all tables |
| 4 | SQLAlchemy models | `apps/worker/db/models.py` | Models match [database.md](./database.md) |
| 5 | B2 client + key layout | `apps/worker/storage/` | Can upload/download with correct keys |
| 6 | `.env.example` + local `.env` | `.env.example` | All vars documented |

**Exit criteria:** Postgres running, B2 bucket configured, schema migrated.

---

## Day 2 — Pipeline in Isolation

**Goal:** One brief in → one variant out, manifests in B2.

| # | Task | Files | Done When |
|---|------|-------|-----------|
| 7 | Genblaze pipeline definition | `pipeline/ad_pipeline.py` | 5 steps defined with fallbacks |
| 8 | Step modules | `pipeline/steps/*.py` | Each step produces output + manifest |
| 9 | Fallback config | `pipeline/fallback_config.py` | Fallback chains per step |
| 10 | Isolation test script | `pipeline/ad_pipeline.py` CLI | `python -m pipeline.ad_pipeline --brief "..."` works |
| 11 | Manifest writing | Per-step + run-level + variant | All JSON files in correct B2 keys |
| 12 | Object Lock on manifests | `storage/b2_client.py` | Manifests uploaded with governance lock |

**Exit criteria:** Run pipeline script, see `final.mp4` + `manifest.json` in B2 console.

---

## Day 3 — Backend API + Job Queue

**Goal:** Wrap pipeline in FastAPI, persist state to DB.

| # | Task | Files | Done When |
|---|------|-------|-----------|
| 13 | FastAPI app skeleton | `main.py` | `/health` returns 200 |
| 14 | Briefs API | `api/briefs.py` | POST/GET /briefs works |
| 15 | Runs API | `api/runs.py` | GET /runs/{id} returns steps + variants |
| 16 | Job queue | `jobs/queue.py`, `jobs/worker.py` | POST /briefs enqueues, worker runs pipeline |
| 17 | DB writes per step | Worker callbacks | `run_steps` rows populated during run |
| 18 | Library API | `api/library.py` | GET /library paginated |
| 19 | Verify endpoint | `manifest/verify.py`, `api/runs.py` | GET /runs/{id}/verify works |

**Exit criteria:** `curl POST /briefs` → poll GET /runs/{id} → see completed run with steps.

---

## Day 4 — Frontend Skeleton

**Goal:** Brief form → progress → variant grid talking to real API.

| # | Task | Files | Done When |
|---|------|-------|-----------|
| 20 | Next.js scaffold | `apps/web/` | `npm run dev` works |
| 21 | API client + types | `lib/api-client.ts`, `lib/types.ts` | Typed calls to backend |
| 22 | Dashboard + BriefForm | `app/dashboard/`, `components/BriefForm.tsx` | Can submit brief |
| 23 | Brief progress page | `app/brief/[briefId]/` | Shows run status (polling OK for now) |
| 24 | VariantGrid | `components/VariantGrid.tsx` | Shows thumbnails when done |
| 25 | PipelineStatusStream | `components/PipelineStatusStream.tsx` | Live step updates |

**Exit criteria:** Submit brief in UI → see progress → see variants.

---

## Day 5 — Provenance Viewer (Differentiator)

**Goal:** The screen that wins judging. Do not skip or defer.

| # | Task | Files | Done When |
|---|------|-------|-----------|
| 26 | Provenance page | `app/run/[runId]/page.tsx` | Full run detail rendered |
| 27 | ProvenanceTimeline | `components/ProvenanceTimeline.tsx` | Step chain + parent_run_id lineage |
| 28 | ManifestCard + CostBadge | `components/` | Per-step provider, cost, fallback flag |
| 29 | Verify button | Calls GET /runs/{id}/verify | Green check or mismatch warning |
| 30 | Fork/replay UI | `app/run/[runId]/replay/` | Override one model, POST /runs/{id}/fork |
| 31 | Replay endpoint | `manifest/replay.py` | POST /runs/{id}/replay creates child run |

**Exit criteria:** View provenance, verify manifest, fork with model swap, see new run linked.

---

## Day 6 — Real-Time + B2 Webhooks

**Goal:** No polling — B2 events drive frontend updates.

| # | Task | Files | Done When |
|---|------|-------|-----------|
| 32 | B2 event notification config | `infra/b2-bucket-setup.py` | Points to Vercel webhook |
| 33 | Webhook route | `app/api/webhooks/b2/route.ts` | Receives B2 PUT events |
| 34 | SSE broadcast | Backend or Next.js route | Frontend receives run-complete event |
| 35 | Wire PipelineStatusStream to SSE | `components/PipelineStatusStream.tsx` | Variant grid appears without refresh |

**Exit criteria:** Submit brief → watch live progress → variants appear automatically.

---

## Day 7 — Deploy + Demo

**Goal:** Production deployment and hackathon submission.

| # | Task | Files | Done When |
|---|------|-------|-----------|
| 36 | Deploy frontend to Vercel | — | Live URL works |
| 37 | Deploy backend to Render/Railway/Fly | `infra/Dockerfile.worker` | API + worker running |
| 38 | Managed Postgres + Redis | — | Production DB migrated |
| 39 | Library page | `app/library/page.tsx` | Browse all variants |
| 40 | Landing page | `app/(marketing)/page.tsx` | Pitch + CTA |
| 41 | README | `README.md` | Providers, B2 usage, Genblaze usage (submission fields) |
| 42 | Demo video | — | Record end-to-end flow including verify + fork |

**Exit criteria:** Live demo URL, README complete, demo video recorded.

---

## Priority Matrix

| Priority | Feature | Why |
|----------|---------|-----|
| P0 | Pipeline end-to-end | Nothing works without it |
| P0 | B2 manifests + Object Lock | Core differentiator |
| P0 | Provenance viewer + verify | Judging criteria |
| P1 | Fork/replay | Shows Genblaze replay + lineage |
| P1 | B2 webhooks → SSE | Demo polish |
| P2 | Library page | Nice to have |
| P2 | Landing page polish | Submission presentation |
| P3 | Auth | Skip for hackathon MVP |

---

## Parallel Work Streams

If multiple teammates:

| Teammate | Focus | Days |
|----------|-------|------|
| A | Infra + B2 + DB | 1 |
| B | Pipeline + Genblaze | 1–2 |
| C | Backend API + queue | 3 |
| D | Frontend (brief → variants) | 4 |
| E | Provenance viewer + fork | 5 |
| Any | Deploy + demo | 6–7 |
