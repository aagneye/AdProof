# AdProof — Backend Specification

**Stack:** FastAPI, SQLAlchemy, Alembic, Redis/RQ, Genblaze Python SDK.  
**Deploy:** Render, Railway, or Fly (long-running — **not** serverless).

---

## 1. Directory Structure

```
apps/worker/
├── main.py                 # FastAPI app entrypoint
├── api/
│   ├── briefs.py           # POST /briefs, GET /briefs/:id
│   ├── runs.py             # GET /runs/:id, POST replay/fork, verify, manifest
│   ├── library.py          # GET /library
│   └── webhooks.py         # Provider async callbacks
├── pipeline/
│   ├── ad_pipeline.py      # Genblaze Pipeline definition
│   ├── steps/
│   │   ├── storyboard.py
│   │   ├── animate.py
│   │   ├── voiceover.py
│   │   ├── score.py
│   │   └── compose.py
│   └── fallback_config.py
├── storage/
│   ├── b2_client.py
│   ├── key_layout.py
│   └── lifecycle_rules.py
├── db/
│   ├── models.py
│   ├── session.py
│   └── migrations/
├── jobs/
│   ├── queue.py
│   └── worker.py
├── manifest/
│   ├── verify.py
│   └── replay.py
└── requirements.txt
```

---

## 2. FastAPI Application (`main.py`)

```python
app = FastAPI(title="AdProof API", version="0.1.0")

# Routers
app.include_router(briefs_router, prefix="/briefs", tags=["briefs"])
app.include_router(runs_router, prefix="/runs", tags=["runs"])
app.include_router(library_router, prefix="/library", tags=["library"])
app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

@app.get("/health")
def health(): ...
```

CORS: allow `NEXT_PUBLIC_API_URL` origin (Vercel domain in prod).

On startup:

- Verify DB connection
- Optionally run `lifecycle_rules.ensure_configured()` against B2

---

## 3. API Routes

Full contract in [api-spec.md](./api-spec.md). Summary:

| Method | Path | Handler | Action |
|--------|------|---------|--------|
| POST | `/briefs` | `briefs.create` | Create brief, enqueue run |
| GET | `/briefs/{id}` | `briefs.get` | Brief + latest run status |
| GET | `/runs/{id}` | `runs.get` | Full run: steps, costs, manifest keys |
| POST | `/runs/{id}/replay` | `runs.replay` | Genblaze replay → new run |
| POST | `/runs/{id}/fork` | `runs.fork` | Replay with step override |
| GET | `/runs/{id}/manifest` | `runs.manifest` | Signed URL to manifest.json |
| GET | `/runs/{id}/verify` | `runs.verify` | Re-compute SHA-256, match/mismatch |
| GET | `/library` | `library.list` | Paginated variants |

---

## 4. Job Queue

### Queue (`jobs/queue.py`)

- Redis connection from `REDIS_URL`
- RQ (or Celery) queue named `adproof-pipeline`
- `enqueue_run(brief_id, run_id)` — pushes pipeline job

### Worker (`jobs/worker.py`)

```
1. Dequeue job (brief_id, run_id)
2. Update run.status = running
3. Execute pipeline/ad_pipeline.py for this brief
4. On each step completion:
   - Write run_steps row (provider, model, cost, manifest_key, asset_key)
   - Upload assets to B2 via key_layout
5. On success:
   - Write variants row(s)
   - Update run.status = succeeded, brief.status = done
6. On failure:
   - Update run.status = failed, log to B2 logs/{run_id}/pipeline.log
```

Worker must run as a **separate long-lived process** (not inside uvicorn workers) because ffmpeg compose can take minutes.

---

## 5. Pipeline Integration

See [pipeline.md](./pipeline.md) for step definitions.

Worker calls:

```python
from pipeline.ad_pipeline import run_pipeline

result = run_pipeline(
    brief_id=brief_id,
    run_id=run_id,
    brief_text=brief.brief_text,
    reference_image_key=brief.reference_image_key,
    on_step_complete=db_callback,
)
```

Each `on_step_complete` callback persists `run_steps` and updates progress (for SSE/polling).

---

## 6. Storage Layer

### `storage/b2_client.py`

Wraps `genblaze_s3.S3StorageBackend.for_backblaze(B2_BUCKET_NAME)`.

Methods: `upload`, `download`, `signed_url`, `delete`.

### `storage/key_layout.py`

Canonical B2 key builders — see [b2-storage.md](./b2-storage.md).

```python
def step_asset_key(run_id, step_name, step_id, ext, model=None) -> str: ...
def step_manifest_key(run_id, step_name, step_id, model=None) -> str: ...
def variant_final_key(run_id, variant_id) -> str: ...
def run_manifest_key(run_id) -> str: ...
```

### `storage/lifecycle_rules.py`

Called on boot or via `infra/b2-bucket-setup.py`:

- Delete `runs/{run_id}/steps/**` after 7 days
- Retain `variants/` and `*.manifest.json` indefinitely
- Object Lock on `*.manifest.json`

---

## 7. Manifest Module

### `manifest/verify.py`

```python
def verify_run(run_id: str) -> VerifyResult:
    # Download rolled-up manifest from B2
    # Re-compute SHA-256 of final.mp4
    # Compare with manifest claim
    # Return { match: bool, expected: str, actual: str }
```

### `manifest/replay.py`

```python
def replay_run(run_id: str, overrides: dict | None) -> str:
    # Load manifest.json from B2
    # genblaze replay with optional step overrides
    # Return new_run_id
```

---

## 8. Database

Models in `db/models.py`. Schema in [database.md](./database.md).

Session via `db/session.py` (SQLAlchemy async or sync — pick one, be consistent).

Alembic migrations in `db/migrations/`.

---

## 9. Auth (Hackathon MVP)

Minimal: single demo user or email magic link.

- `users` table exists for schema completeness
- MVP can hardcode `user_id` or skip auth middleware
- Production: add JWT/session middleware before launch

---

## 10. Error Handling

| Scenario | Behavior |
|----------|----------|
| Provider timeout | Fallback chain in Genblaze; record `fallback_triggered=true` |
| All fallbacks fail | `run_steps.status=failed`, `run.status=failed` |
| B2 upload fail | Retry 3x, then fail run |
| Invalid brief | 422 on POST /briefs |

---

## 11. Dependencies (`requirements.txt`)

Core:

```
fastapi
uvicorn[standard]
sqlalchemy
alembic
psycopg2-binary
redis
rq
genblaze
genblaze-s3
boto3
pydantic-settings
python-multipart
```

---

## 12. Local Run

```bash
# Terminal 1
uvicorn main:app --reload --port 8000

# Terminal 2
python -m jobs.worker
```

---

## 13. Docker Production

Use `infra/Dockerfile.worker`:

- Base: `python:3.11-slim` + ffmpeg installed
- CMD runs both uvicorn and worker (supervisord) or deploy as two services

See [deployment.md](./deployment.md).
