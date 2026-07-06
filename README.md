# Borusan AI Ecosystem CRM

Local MVP for transforming the Borusan AI Studio Ecosystem Library Excel workbook into a normalized, searchable, auditable CRM.

The system is designed as a local-first MVP that can later move to Borusan internal infrastructure. It keeps the product model clean: Excel rows are staged and reviewed first, then committed into normalized CRM tables only after candidate generation and approval.

## Current MVP Capabilities

- Local JWT authentication with `ADMIN` and `USER` roles
- Admin user management
- Admin logo/branding upload
- SQL Server-backed CRM data model
- Excel workbook upload, profiling, staging, candidate generation, review, and commit
- Startup Library with search, filtering, sorting, pagination, and CSV export
- Company detail with contacts, notes, Borusan company fit, opportunities, and follow-ups
- PoC/opportunity list and detail/edit views
- Events list and detail/edit views
- Network and AI Tools list foundations
- Follow-up/task management
- Leaderboard based on manual CRM contributions only
- Audit logs for imports, admin actions, and CRM mutations
- Health/readiness endpoints and smoke test script

## Architecture Overview

- Backend: FastAPI, SQLAlchemy ORM, Alembic migrations
- Database: Microsoft SQL Server via `pyodbc`
- Frontend: Next.js, React, TypeScript
- Auth: local JWT for MVP; future Microsoft Entra ID integration is planned
- File storage: local `backend/uploads/` for imported workbooks and branding assets
- Config: `.env` and YAML mappings under `config/`

## Repository Structure

- `backend/` - FastAPI app, SQLAlchemy models, Alembic migrations, seed/smoke scripts
- `frontend/` - Next.js CRM UI
- `config/` - Excel sheet/column/status/Borusan mapping YAML
- `docs/` - product, architecture, import, security, runbook, QA, and handover notes

## Prerequisites

- Windows PowerShell
- Python 3.12 recommended
- Node.js 20 recommended
- Microsoft SQL Server or SQL Server Express
- ODBC Driver 17 or 18 for SQL Server

Check installed ODBC drivers:

```powershell
Get-OdbcDriver | Where-Object { $_.Name -like "*SQL Server*" } | Select-Object Name,Platform
```

## SQL Server Setup

Create the local database:

```powershell
sqlcmd -S localhost\SQLEXPRESS01 -E -Q "IF DB_ID('BorusanAIEcosystemCRM') IS NULL CREATE DATABASE BorusanAIEcosystemCRM"
```

Known local trusted connection pattern for SQLEXPRESS01:

```text
mssql+pyodbc://@localhost\SQLEXPRESS01/BorusanAIEcosystemCRM?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes
```

Driver 18 TCP example:

```text
mssql+pyodbc://username:password@localhost:1433/BorusanAIEcosystemCRM?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
```

## Backend Setup

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create or update `C:\Users\emirc\borusan-ai-studio-crm\.env` from `.env.example`.

Required backend variables:

```powershell
$env:DATABASE_URL="mssql+pyodbc://@localhost\SQLEXPRESS01/BorusanAIEcosystemCRM?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
$env:JWT_SECRET_KEY="replace-with-a-long-random-local-secret"
$env:INITIAL_ADMIN_EMAIL="admin@example.com"
$env:INITIAL_ADMIN_PASSWORD="change-me-admin-password"
$env:INITIAL_ADMIN_FULL_NAME="Initial Admin"
```

Run migrations and seed controlled data/admin:

```powershell
python -m alembic upgrade head
python -m app.db.seed
```

Run backend:

```powershell
python -m uvicorn app.main:app --reload
```

Backend docs:

```text
http://127.0.0.1:8000/docs
```

Health endpoints:

```text
GET http://127.0.0.1:8000/api/v1/health
GET http://127.0.0.1:8000/api/v1/health/readiness
```

## Frontend Setup

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\frontend
npm install
$env:NEXT_PUBLIC_API_BASE_URL="/api/backend"
$env:BACKEND_API_ORIGIN="http://127.0.0.1:8000"
npm run dev
```

For local development, the browser calls the Next.js same-origin proxy:

```text
http://localhost:3000/api/backend/*
```

Next.js rewrites those requests to FastAPI:

```text
http://127.0.0.1:8000/api/v1/*
```

This keeps local development independent from browser CORS behavior. Backend CORS remains configured as a fallback and for direct API testing.

Manual proxy checks after restarting `npm run dev`:

```text
http://localhost:3000/api/backend/health
http://localhost:3000/api/backend/health/readiness
http://localhost:3000/api/backend/dashboard/summary
```

Frontend:

```text
http://localhost:3000
```

## Login Setup

The seed command creates an initial admin only when these variables are set and the email does not already exist:

- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`
- `INITIAL_ADMIN_FULL_NAME`

After login, admins can create additional users at `/admin/users`.

## Smoke Test

With backend running:

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\Activate.ps1
$env:SMOKE_API_BASE_URL="http://127.0.0.1:8000"
$env:SMOKE_ADMIN_EMAIL="admin@example.com"
$env:SMOKE_ADMIN_PASSWORD="change-me-admin-password"
python scripts\smoke_test_api.py
```

## Common Troubleshooting

- `pyodbc` cannot connect: confirm SQL Server is running, database exists, and ODBC Driver 17/18 is installed.
- Driver 18 certificate errors: add `TrustServerCertificate=yes` for local MVP.
- Login fails: rerun `python -m app.db.seed` with `INITIAL_ADMIN_*` env vars set, or reset via admin user management.
- Frontend cannot reach API: confirm `NEXT_PUBLIC_API_BASE_URL=/api/backend`, `BACKEND_API_ORIGIN=http://127.0.0.1:8000`, restart `npm run dev`, and open `http://localhost:3000/api/backend/health`.
- Alembic command not found: run `python -m alembic upgrade head` from `backend` with the venv activated.
- Imported Excel records do not count on leaderboard: this is intentional. Only manual CRM contributions count.

## Handover Docs

Start with:

- `docs/local_runbook.md`
- `docs/demo_script.md`
- `docs/qa_checklist.md`
- `docs/security_checklist.md`
- `docs/it_handover_notes.md`
- `docs/backup_restore_notes.md`
