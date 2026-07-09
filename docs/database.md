# AdProof — Database Schema

**Engine:** PostgreSQL  
**ORM:** SQLAlchemy  
**Migrations:** Alembic  

Postgres holds **metadata and pointers only**. All binary assets live in B2.

---

## 1. Entity Relationship

```
users
  └── briefs (1:N)
        └── runs (1:N)
              ├── run_steps (1:N)
              ├── variants (1:N)
              └── runs (self-ref: parent_run_id for forks)
```

---

## 2. Tables

### `users`

Google OAuth via NextAuth (frontend). Backend stores profile and issues JWT for API calls.

```sql
CREATE TABLE users (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email       TEXT UNIQUE NOT NULL,
  google_id   TEXT UNIQUE,
  name        TEXT,
  avatar_url  TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Briefs, runs, and library queries are scoped by `user_id` — users cannot read another account's data.

### `briefs`

One ad request from a user.

```sql
CREATE TABLE briefs (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               UUID NOT NULL REFERENCES users(id),
  brand_name            TEXT NOT NULL,
  brief_text            TEXT NOT NULL,
  reference_image_key   TEXT,          -- B2 key, nullable
  status                TEXT NOT NULL DEFAULT 'pending',
                                        -- pending | running | done | failed
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### `runs`

One execution of the pipeline for a brief. Many runs per brief (retries, forks).

```sql
CREATE TABLE runs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brief_id        UUID NOT NULL REFERENCES briefs(id),
  parent_run_id   UUID REFERENCES runs(id),   -- fork lineage
  status          TEXT NOT NULL DEFAULT 'queued',
                                        -- queued | running | succeeded | failed
  started_at      TIMESTAMPTZ,
  finished_at     TIMESTAMPTZ,
  total_cost_usd  NUMERIC(10, 4)
);
```

### `run_steps`

Individual pipeline steps within a run.

```sql
CREATE TABLE run_steps (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id              UUID NOT NULL REFERENCES runs(id),
  step_name           TEXT NOT NULL,    -- storyboard | animate | voiceover | score | compose
  provider            TEXT,             -- actual provider used (post-fallback)
  model               TEXT,
  status              TEXT NOT NULL,    -- succeeded | fallback_used | failed
  fallback_triggered  BOOLEAN NOT NULL DEFAULT FALSE,
  cost_usd            NUMERIC(10, 4),
  latency_ms          INTEGER,
  manifest_key        TEXT,             -- B2 key to step manifest JSON
  asset_key           TEXT,             -- B2 key to step output asset
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### `variants`

Final selectable outputs from a run (usually 1 per fanned-out animate branch).

```sql
CREATE TABLE variants (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id            UUID NOT NULL REFERENCES runs(id),
  asset_key         TEXT NOT NULL,      -- final composed video in B2
  thumbnail_key     TEXT,
  manifest_key      TEXT NOT NULL,      -- rolled-up final manifest
  sha256_hash       TEXT NOT NULL,
  provider_summary  TEXT,               -- e.g. "kling + elevenlabs + minimax"
  selected          BOOLEAN NOT NULL DEFAULT FALSE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 3. Indexes

```sql
CREATE INDEX idx_runs_brief_id ON runs(brief_id);
CREATE INDEX idx_runs_parent_run_id ON runs(parent_run_id);
CREATE INDEX idx_run_steps_run_id ON run_steps(run_id);
CREATE INDEX idx_variants_run_id ON variants(run_id);
CREATE INDEX idx_briefs_user_id ON briefs(user_id);
CREATE INDEX idx_briefs_status ON briefs(status);
```

---

## 4. Common Queries

### Brief with latest run status

```sql
SELECT b.*, r.id AS run_id, r.status AS run_status
FROM briefs b
LEFT JOIN LATERAL (
  SELECT * FROM runs WHERE brief_id = b.id ORDER BY started_at DESC NULLS LAST LIMIT 1
) r ON true
WHERE b.id = $1;
```

### Provenance tree (fork lineage)

```sql
WITH RECURSIVE lineage AS (
  SELECT * FROM runs WHERE id = $1
  UNION ALL
  SELECT r.* FROM runs r JOIN lineage l ON r.id = l.parent_run_id
)
SELECT * FROM lineage;
```

### Run detail with steps

```sql
SELECT r.*, json_agg(rs ORDER BY rs.created_at) AS steps
FROM runs r
LEFT JOIN run_steps rs ON rs.run_id = r.id
WHERE r.id = $1
GROUP BY r.id;
```

### Library (paginated variants)

```sql
SELECT v.*, b.brand_name, r.brief_id
FROM variants v
JOIN runs r ON r.id = v.run_id
JOIN briefs b ON b.id = r.brief_id
WHERE ($provider IS NULL OR v.provider_summary ILIKE '%' || $provider || '%')
  AND ($brand IS NULL OR b.brand_name ILIKE '%' || $brand || '%')
ORDER BY v.created_at DESC
LIMIT $limit OFFSET $offset;
```

---

## 5. SQLAlchemy Models Location

`apps/worker/db/models.py` — mirror this schema exactly.

Alembic initial migration: `apps/worker/db/migrations/versions/001_initial_schema.py`

---

## 6. Data Rules

| Rule | Rationale |
|------|-----------|
| Never store blobs in Postgres | B2 is the asset store |
| `manifest_key` always points to B2 | Enables verify without DB |
| `parent_run_id` set on fork/replay | Provenance chain integrity |
| `total_cost_usd` = sum of `run_steps.cost_usd` | Computed on run completion |
| `selected` on variants | User picks one variant per brief |

---

## 7. Local Connection

```env
DATABASE_URL=postgresql://adproof:adproof@localhost:5432/adproof
```

Docker Compose provides this by default — see [setup.md](./setup.md).
