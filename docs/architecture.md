# AdProof — System Architecture

> **Hackathon:** Backblaze Generative Media Hackathon (Genblaze + B2)  
---

## 1. Business Model


| Dimension || AdProof |
|-----------|--------|---------|
| Access | Closed, agency-style — they run the pipeline | Open, self-serve — the pipeline **is** the product |
| Provenance | None | Every output carries a cryptographic proof of how it was made |
| Storage | Opaque | Provenance manifest — embeddable, verifiable, tamper-evident on B2 via Object Lock |

### Target Users

Small business owners, solo marketers, and indie brands who need:

- 30–60s ad or UGC-style video variants fast, without an agency
- C2PA-style labeling as platforms begin to require or reward it

### Why Provenance Is the Wedge

C2PA / Content Credentials adoption is at production scale across OpenAI, Google, Adobe, and Microsoft. AI media labeling is moving from "nice to have" to platform/regulatory requirement (EU AI Act Article 50 transparency rules). No AI ad generator leads with this — it is AdProof's differentiation for judges.

### Monetization (Pitch Deck — Not MVP)

| Tier | Description |
|------|-------------|
| Free | B2 free 10 GB + a handful of generations |
| Usage-based | Cost-plus on top of provider spend |
| Team | Private B2 bucket + Object Lock retention policy for brand compliance/legal |

---

## 2. High-Level Architecture

```
┌─────────────────┐      ┌──────────────────────┐      ┌───────────────────┐
│   Frontend       │ REST │  Backend (FastAPI)   │      │  Genblaze Pipeline │
│   Next.js        │◄────►│  Orchestration API    │◄────►│  (Python SDK)      │
│   (Vercel)       │  WS  │  + Job Queue          │      │  multi-provider    │
└─────────────────┘      └──────────────────────┘      └─────────┬──────────┘
                                    │                              │
                                    ▼                              ▼
                          ┌──────────────────┐          ┌────────────────────┐
                          │ Postgres          │          │  Backblaze B2       │
                          │ (jobs, runs,      │          │  (assets, manifests,│
                          │  manifests,       │          │  thumbnails, logs)  │
                          │  users, briefs)   │          └────────────────────┘
                          └──────────────────┘
```

### Core Principle

**Postgres holds pointers and state** — job status, provider used, cost, relationships between runs.

**B2 holds everything heavy** — video/image/audio bytes, manifests, thumbnails.

**Never store binary blobs in Postgres.**

---

## 3. Monorepo Structure

```
adproof/
├── apps/
│   ├── web/                        # Next.js frontend (Vercel)
│   │   ├── app/
│   │   │   ├── (marketing)/page.tsx
│   │   │   ├── dashboard/
│   │   │   ├── brief/[briefId]/
│   │   │   ├── run/[runId]/
│   │   │   ├── library/
│   │   │   └── api/webhooks/b2/route.ts
│   │   ├── components/
│   │   ├── lib/
│   │   └── package.json
│   │
│   └── worker/                     # Python backend + Genblaze
│       ├── main.py
│       ├── api/
│       ├── pipeline/
│       ├── storage/
│       ├── db/
│       ├── jobs/
│       ├── manifest/
│       └── requirements.txt
│
├── packages/
│   └── shared-types/
│
├── infra/
│   ├── docker-compose.yml
│   ├── Dockerfile.worker
│   └── b2-bucket-setup.py
│
├── docs/                           # Team documentation (this folder)
├── .env.example
└── README.md
```

See individual spec documents for detail:

| Document | Contents |
|----------|----------|
| [setup.md](./setup.md) | Local dev environment |
| [frontend-spec.md](./frontend-spec.md) | Pages, components, API client |
| [backend-spec.md](./backend-spec.md) | FastAPI routes, job queue, workers |
| [database.md](./database.md) | Postgres schema and indexes |
| [pipeline.md](./pipeline.md) | Genblaze pipeline steps and fallbacks |
| [b2-storage.md](./b2-storage.md) | Key layout, Object Lock, lifecycle |
| [api-spec.md](./api-spec.md) | REST API surface |
| [deployment.md](./deployment.md) | Production hosting guide |
| [build-order.md](./build-order.md) | Day-by-day implementation plan |

---

## 4. Data Flow (End-to-End)

```
User submits brief
       │
       ▼
POST /briefs ──► Postgres (brief row, status=pending)
       │
       ▼
Job enqueued (Redis/RQ) ──► Worker picks up
       │
       ▼
Genblaze Pipeline runs (5 steps, fan-out on animate)
       │  Each step writes manifest.json + asset to B2
       │  Each step writes run_steps row to Postgres
       ▼
Final variant composed ──► B2 variants/{id}/final.mp4
       │                    B2 variants/{id}/manifest.json (Object Lock)
       ▼
B2 Event Notification ──► POST /api/webhooks/b2 (Next.js)
       │
       ▼
SSE push to frontend ──► Brief status = done, variant grid renders
```

---

## 5. Provenance & Replay

Every pipeline run:

1. Writes a **SHA-256 manifest per step** plus one rolled-up manifest for the final asset
2. Carries `parent_run_id` so forks ("try Runway instead of Kling") are traceable
3. Is **replayable** via `genblaze replay manifest.json`

The **Provenance Viewer** (`/run/[runId]`) is the differentiator screen — visual timeline, fallback flags, verify button, fork UI.

---

## 6. Technology Stack

| Layer | Technology | Hosting |
|-------|------------|---------|
| Frontend | Next.js 14+ (App Router) | Vercel |
| Backend API | FastAPI | Render / Railway / Fly |
| Job Queue | Redis + RQ (or Celery) | Upstash Redis |
| Database | PostgreSQL + SQLAlchemy + Alembic | Neon / Supabase |
| Pipeline | Genblaze Python SDK | Same host as worker |
| Object Storage | Backblaze B2 (S3-compatible) | B2 Cloud |
| Media Processing | ffmpeg (compose step) | Worker container |

---

## 7. Key Design Decisions

1. **Monorepo** — single repo, `apps/web` and `apps/worker` deploy independently
2. **Postgres = metadata only** — all binaries in B2 with content-addressable keys
3. **Object Lock on manifests** — tamper-evident provenance for judges and compliance
4. **Concurrent animate fan-out** — run multiple image-to-video models in parallel, pick best/fastest; fallback chain if one stalls
5. **B2 event notifications over polling** — webhook → SSE for real-time frontend updates
6. **Worker must not be serverless** — ffmpeg compose step needs long-running process (avoid Vercel/Netlify functions for worker)

---

## 8. Environment Variables

See [.env.example](../.env.example) and [setup.md](./setup.md) for the full list.

Critical groups: `DATABASE_URL`, `REDIS_URL`, `B2_*`, provider API keys (`GMICLOUD_API_KEY`, `ELEVENLABS_API_KEY`, etc.).
