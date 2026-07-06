# Stability Error Hardening Phase

## What Changed

This phase hardens the local MVP against avoidable blank pages, opaque 500s, proxy confusion, and missing-migration failures.

Key changes:

- Structured backend error responses with `error_code`, `message`, and `request_id`.
- Request logging middleware for method, path, status, and duration.
- Server-side traceback logging for unexpected exceptions.
- Readiness checks for critical database tables and basic row counts.
- Safer Organization Detail deck/document reads when the newest migration has not been applied yet.
- Richer frontend API errors with request path, request id, backend message, and proxy target URL.
- Reusable frontend error state with retry and local technical details.
- Expanded read-only smoke test for fragile CRM endpoints.

## Diagnosing A 500

1. Check the frontend error message and expand technical details in local development.
2. Note the `Path`, `Status`, and `Request ID`.
3. Check the backend terminal for the same request id and traceback.
4. Run readiness:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health/readiness
```

If readiness is `degraded`, fix the reported item first. A common case after new features is a missing migration/table.

## Diagnosing Failed To Fetch

The browser should call the Next.js same-origin proxy:

```text
http://localhost:3000/api/backend/health
```

The proxy forwards to:

```text
http://127.0.0.1:8000/api/v1/health
```

If the proxy cannot reach FastAPI, it returns JSON like:

```json
{
  "error": "Backend proxy failed",
  "targetUrl": "http://127.0.0.1:8000/api/v1/health",
  "message": "..."
}
```

Check that both processes are running:

```powershell
# Backend
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload

# Frontend
cd C:\Users\emirc\borusan-ai-studio-crm\frontend
$env:NEXT_PUBLIC_API_BASE_URL="/api/backend"
$env:BACKEND_API_ORIGIN="http://127.0.0.1:8000"
npm run dev
```

## Verifying Migrations

Do not drop or recreate the database unless that is explicitly intended.

Use:

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\Activate.ps1
python -m alembic current
python -m alembic heads
python -m alembic upgrade head
```

Then check readiness:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health/readiness
```

Critical tables include:

- `users`
- `organizations`
- `contacts`
- `notes`
- `organization_borusan_fit`
- `opportunities`
- `events`
- `follow_up_actions`
- `import_batches`
- `import_candidates`
- `user_contributions`
- `organization_documents`
- `audit_logs`

## Running Smoke Test

The smoke test is read-only except login.

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\Activate.ps1
$env:SMOKE_API_BASE_URL="http://127.0.0.1:8000"
$env:SMOKE_ADMIN_EMAIL="admin@example.com"
$env:SMOKE_ADMIN_PASSWORD="change-me-admin-password"
python scripts\smoke_test_api.py
```

It checks:

- health
- readiness
- login
- dashboard
- organization list/detail
- organization documents/contacts/notes/Borusan fit
- follow-ups
- leaderboard
- import batches
- admin branding active
- audit logs for admin users

## Common SQL Server Issues

- Missing table after a new feature: run `python -m alembic upgrade head`.
- Pagination failure: every paginated SQL Server query must include deterministic `ORDER BY`.
- Boolean filtering: use existing helpers such as `not_archived()` and `not_excluded()`.
- Multiple cascade paths: avoid `ON DELETE SET NULL` on multiple reference FKs.

## Common Proxy Issues

- `NEXT_PUBLIC_API_BASE_URL` should be `/api/backend`.
- `BACKEND_API_ORIGIN` should be the origin only, usually `http://127.0.0.1:8000`.
- Do not include `/api/v1` in `BACKEND_API_ORIGIN`.
- Manual proxy checks:

```text
http://localhost:3000/api/backend/health
http://localhost:3000/api/backend/health/readiness
http://localhost:3000/api/backend/dashboard/summary
```

## What Not To Do

- Do not drop the SQL Server database to fix a 500 unless you intentionally want a full local reset.
- Do not bypass migrations by manually creating tables in production-like environments.
- Do not switch the frontend back to direct `http://127.0.0.1:8000` browser calls.
- Do not commit real secrets or local `.env` files.
