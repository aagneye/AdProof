# AdProof

## Quick Start (Tonight — Demo Mode)

Works **without Docker, B2, or AI API keys**. Uses SQLite + local storage + simulated pipeline.

### Terminal 1 — Backend

```bat
infra\start-api.bat
```

Or manually:

```bat
cd apps\worker
set DATABASE_URL=sqlite:///./adproof_local.db
set ADPROOF_DEMO_MODE=true
.venv\Scripts\python.exe -m uvicorn main:app --port 8000
```

API: http://localhost:8000 · Docs: http://localhost:8000/docs

### Terminal 2 — Frontend

```bat
infra\start-web.bat
```

Or manually:

```bat
cd apps\web
set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install && npm run dev
```

App: http://localhost:3000

### Demo Flow

1. Open **Dashboard** → submit a brief (brand + description)
2. Watch **pipeline progress** (storyboard → animate → voiceover → score → compose)
3. View **variants** with thumbnails and SHA-256 hash
4. Open **Provenance Viewer** → click **Verify Manifest** (green check)
5. **Fork** a run with a different animate model → see `parent_run_id` lineage
6. Browse everything in **Library**

---

## Production Setup

With Docker, Postgres, B2, and provider API keys — see [docs/setup.md](docs/setup.md).

```bash
cd infra && docker compose up -d
cp .env.example .env   # fill in B2 + provider keys
python infra/b2-bucket-setup.py
cd apps/worker && alembic upgrade head
```

| Component | Host |
|-----------|------|
| Frontend | Vercel (`apps/web`) |
| API + Worker | Render / Railway / Fly.io |
| Postgres | Neon / Supabase |
| Redis | Upstash (optional) |
| Storage | Backblaze B2 |

Full guide: [docs/deployment.md](docs/deployment.md)

---

## What It Does

| Feature | Status |
|---------|--------|
| Brief → pipeline → variant | ✅ Demo + Genblaze-ready |
| Per-step manifests (SHA-256) | ✅ |
| Provenance viewer + verify | ✅ |
| Fork / replay with lineage | ✅ |
| Library browse | ✅ |
| B2 Object Lock | ✅ When B2 configured |
| Real AI providers | Set `ADPROOF_DEMO_MODE=false` + API keys |

---

## Tech Stack

Next.js · FastAPI · SQLAlchemy · Genblaze SDK · Backblaze B2 · ffmpeg

---

## Documentation

| Doc | Contents |
|-----|----------|
| [architecture.md](docs/architecture.md) | System overview |
| [setup.md](docs/setup.md) | Local dev |
| [frontend-spec.md](docs/frontend-spec.md) | UI spec |
| [backend-spec.md](docs/backend-spec.md) | API spec |
| [pipeline.md](docs/pipeline.md) | Genblaze pipeline |
| [b2-storage.md](docs/b2-storage.md) | B2 key layout |
| [deployment.md](docs/deployment.md) | Hosting guide |
| [build-order.md](docs/build-order.md) | Build plan |

---

## Providers (Production)

| Step | Primary | Fallback |
|------|---------|----------|
| Storyboard | Seedream (GMI Cloud) | FLUX, Imagen |
| Animate | Kling, Wan, Pixverse | Runway, Luma |
| Voiceover | ElevenLabs | NVIDIA Magpie |
| Score | Stability Audio | MiniMax |
| Compose | ffmpeg | — |
