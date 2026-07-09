# Authentication

AdProof uses **Google OAuth** on the frontend (NextAuth.js) and **JWT bearer tokens** on the API. Each user's briefs, runs, and library items are isolated by `user_id`.

## Flow

1. User clicks **Sign in with Google** on `/login` or `/signup`.
2. NextAuth completes the Google OAuth flow.
3. On first sign-in, the frontend calls `POST /auth/google` to create or update the user in Postgres/SQLite.
4. The API returns a JWT (`access_token`). NextAuth stores it in the session.
5. All API requests send `Authorization: Bearer <token>`.
6. FastAPI validates the JWT and scopes queries to the authenticated user.

## Environment variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `GOOGLE_CLIENT_ID` | Vercel / `apps/web` | OAuth client ID from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | Vercel / `apps/web` | OAuth client secret |
| `NEXTAUTH_SECRET` | Vercel / `apps/web` | Signs NextAuth session cookies |
| `NEXTAUTH_URL` | Vercel / `apps/web` | Public app URL (e.g. `http://localhost:3000`) |
| `AUTH_JWT_SECRET` | Backend API | Signs API JWTs — use the same value as `NEXTAUTH_SECRET` in production |

Copy values from `.env.example` for local development.

## Protected routes

**Frontend (middleware):** `/dashboard`, `/brief/*`, `/library`, `/run/*`

**Backend:** `POST /briefs`, `GET /briefs`, `GET /briefs/:id`, all `/runs/*`, `GET /library`

Public: `GET /health`, `POST /auth/google`, static assets.

## Local setup checklist

1. Create OAuth credentials in [Google Cloud Console](docs/deployment.md#12-google-oauth-nextauth).
2. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `NEXTAUTH_SECRET`, `NEXTAUTH_URL` in `apps/web/.env.local`.
3. Set `AUTH_JWT_SECRET` (same as `NEXTAUTH_SECRET`) in root `.env` or `start-api.bat`.
4. Restart API and web dev servers.
5. Sign in at http://localhost:3000/login — dashboard shows only your briefs.
