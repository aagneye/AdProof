-- AdProof app tables for Supabase Postgres (public schema)
-- Run in Supabase SQL Editor after Auth is enabled.
-- NOTE: auth.users is managed by Supabase Auth (OAuth). These tables store
-- application data (profiles, briefs, runs, activity). Point DATABASE_URL here.

CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(36) PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  google_id TEXT UNIQUE,
  name TEXT,
  avatar_url TEXT,
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS briefs (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL REFERENCES users(id),
  brand_name TEXT NOT NULL,
  brief_text TEXT NOT NULL,
  reference_image_key TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS runs (
  id VARCHAR(36) PRIMARY KEY,
  brief_id VARCHAR(36) NOT NULL REFERENCES briefs(id),
  parent_run_id VARCHAR(36) REFERENCES runs(id),
  status VARCHAR(20) NOT NULL DEFAULT 'queued',
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  total_cost_usd NUMERIC(10, 4),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS run_steps (
  id VARCHAR(36) PRIMARY KEY,
  run_id VARCHAR(36) NOT NULL REFERENCES runs(id),
  step_name VARCHAR(50) NOT NULL,
  provider TEXT,
  model TEXT,
  status VARCHAR(20) NOT NULL,
  fallback_triggered BOOLEAN NOT NULL DEFAULT false,
  cost_usd NUMERIC(10, 4),
  latency_ms INTEGER,
  manifest_key TEXT,
  asset_key TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS variants (
  id VARCHAR(36) PRIMARY KEY,
  run_id VARCHAR(36) NOT NULL REFERENCES runs(id),
  asset_key TEXT NOT NULL,
  thumbnail_key TEXT,
  manifest_key TEXT NOT NULL,
  sha256_hash TEXT NOT NULL,
  provider_summary TEXT,
  selected BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_activities (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL REFERENCES users(id),
  action VARCHAR(80) NOT NULL,
  resource_type VARCHAR(50),
  resource_id VARCHAR(36),
  metadata_json TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_user_activities_user_id ON user_activities (user_id);
CREATE INDEX IF NOT EXISTS ix_user_activities_action ON user_activities (action);
CREATE INDEX IF NOT EXISTS ix_briefs_user_id ON briefs (user_id);
CREATE INDEX IF NOT EXISTS ix_runs_brief_id ON runs (brief_id);
