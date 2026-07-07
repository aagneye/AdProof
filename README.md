# AdProof

> **Absurd for everyone, and every ad it makes can prove it's real.**

Open-source, self-serve AI ad pipeline with cryptographic provenance. Built for the Backblaze Generative Media Hackathon (Genblaze + B2).

Generate 30–60s ad or UGC-style video variants from a text brief. Every output carries a verifiable, tamper-evident manifest stored on Backblaze B2 with Object Lock.

---

## What It Does

1. **Submit a brief** — brand name, ad description, optional product photo
2. **Pipeline runs** — storyboard → animate (multi-provider fan-out) → voiceover → score → compose
3. **Pick a variant** — grid of finished videos with cost and provider info
4. **Verify provenance** — SHA-256 manifest check, full step timeline, fallback history
5. **Fork & replay** — swap a provider (e.g. Kling → Runway) and re-run with lineage tracking

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js (Vercel) |
| Backend | FastAPI + Redis job queue |
| Pipeline | Genblaze Python SDK |
| Database | PostgreSQL (metadata only) |
| Storage | Backblaze B2 (assets + manifests) |
| Media | ffmpeg compose step |

---

## Quick Start

```bash
# 1. Clone and configure
git clone <repo-url> adproof && cd adproof
cp .env.example .env   # fill in API keys

# 2. Start Postgres + Redis
cd infra && docker compose up -d && cd ..

# 3. Setup B2 bucket (one-time)
python infra/b2-bucket-setup.py

# 4. Backend
cd apps/worker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000          # terminal 1
python -m jobs.worker                          # terminal 2

# 5. Frontend
cd apps/web
npm install && npm run dev
```

Open http://localhost:3000

Full setup guide: [docs/setup.md](docs/setup.md)

---

## Documentation

| Document | Description |
|----------|-------------|
| [architecture.md](docs/architecture.md) | System overview, data flow, design decisions |
| [setup.md](docs/setup.md) | Local development setup |
| [frontend-spec.md](docs/frontend-spec.md) | Pages, components, API client |
| [backend-spec.md](docs/backend-spec.md) | FastAPI routes, job queue, workers |
| [database.md](docs/database.md) | Postgres schema |
| [pipeline.md](docs/pipeline.md) | Genblaze pipeline steps and fallbacks |
| [b2-storage.md](docs/b2-storage.md) | B2 key layout, Object Lock, lifecycle |
| [api-spec.md](docs/api-spec.md) | REST API contract |
| [deployment.md](docs/deployment.md) | Production hosting (Vercel, Render, etc.) |
| [build-order.md](docs/build-order.md) | Day-by-day implementation plan |
| [env-vars.md](docs/env-vars.md) | Environment variables reference |

---

## Providers & Models

| Step | Primary | Fallback |
|------|---------|----------|
| Storyboard | Seedream 5.0 Lite (GMI Cloud) | FLUX Kontext Pro, Imagen 4 |
| Animate | Kling, Wan 2.6, Pixverse (concurrent) | Runway Gen-4 Turbo, Luma Ray 2 |
| Voiceover | ElevenLabs | NVIDIA Magpie TTS |
| Score | Stability Audio | MiniMax (GMI Cloud) |
| Compose | ffmpeg (built-in) | — |

---

## B2 Usage

- **Bucket:** `adproof-assets` — content-addressable key layout under `runs/{run_id}/`
- **Object Lock:** All `*.manifest.json` files — governance mode, 30-day retention
- **Lifecycle:** Intermediate `steps/` auto-deleted after 7 days; variants and manifests kept
- **Event Notifications:** `variants/*/final.mp4` PUT → webhook → SSE to frontend

Details: [docs/b2-storage.md](docs/b2-storage.md)

---

## Genblaze Usage

Pipeline defined in `apps/worker/pipeline/ad_pipeline.py`:

- 5 chained steps with per-step SHA-256 manifests
- Concurrent fan-out on animate step
- Automatic fallback chains when providers stall
- Full replay via `genblaze replay manifest.json`
- Fork support with `parent_run_id` lineage tracking

Details: [docs/pipeline.md](docs/pipeline.md)

---

## Deployment

| Component | Host |
|-----------|------|
| Frontend | Vercel (`apps/web`) |
| API + Worker | Render / Railway / Fly.io |
| Postgres | Neon / Supabase |
| Redis | Upstash |
| Storage | Backblaze B2 |

Full guide: [docs/deployment.md](docs/deployment.md)

---

## License

TBD
