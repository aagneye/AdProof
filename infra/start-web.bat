@echo off
cd /d %~dp0..\apps\web
if not exist node_modules (
  echo Installing npm dependencies...
  call npm install
)
set NEXT_PUBLIC_API_URL=http://localhost:8000
REM Also loads apps/web/.env.local (NEXT_PUBLIC_SUPABASE_*, NEXTAUTH_*)
echo Starting frontend on http://localhost:3000
call npm run dev
