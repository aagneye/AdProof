# AdProof Team Handoff Guide

Quick orientation for new teammates joining the hackathon build.

---

## What Is AdProof?

Open-source AI ad generator with **cryptographic provenance**. Users submit a text brief, the Genblaze pipeline produces video variants, and every output has a verifiable manifest on Backblaze B2.


---

## Read These First

1. [architecture.md](./architecture.md) — system overview (start here)
2. [build-order.md](./build-order.md) — what to build and in what order
3. [setup.md](./setup.md) — get your local environment running

Then read the spec for your area:

| Role | Document |
|------|----------|
| Frontend | [frontend-spec.md](./frontend-spec.md) |
| Backend | [backend-spec.md](./backend-spec.md) |
| Pipeline / AI | [pipeline.md](./pipeline.md) |
| Infra / B2 | [b2-storage.md](./b2-storage.md), [deployment.md](./deployment.md) |
| API contract | [api-spec.md](./api-spec.md) |
| Database | [database.md](./database.md) |

---

## Repo Layout

```
apps/web/       → You if doing frontend (Next.js, Vercel)
apps/worker/    → You if doing backend/pipeline (FastAPI, Genblaze)
packages/       → Shared TypeScript types
infra/          → Docker Compose, Dockerfile, B2 setup script
docs/           → All documentation (you are here)
```

---

## Key Principles

1. **Postgres = metadata only.** Never store video/image bytes in the database.
2. **B2 = everything heavy.** Assets, manifests, thumbnails, logs.
3. **Object Lock on manifests.** Tamper-evident provenance is the differentiator.
4. **Worker is NOT serverless.** ffmpeg needs a long-running process.
5. **Provenance viewer is P0.** Do not defer `/run/[runId]` — it wins judging.

---

## Commit Rules

One file per commit. Format: `type(file): description`

See `.cursor/rules/commits.mdc` for full rules.

---

## Questions?

Check the relevant spec doc first. If something is ambiguous, flag it in the team channel and update the doc.
