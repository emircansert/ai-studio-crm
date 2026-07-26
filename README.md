# Borusan AI Ecosystem CRM

Local MVP for transforming the Borusan AI Studio Ecosystem Library Excel workbook into a normalized, searchable, auditable CRM.

The system is designed as a local-first MVP that can later move to Borusan internal infrastructure. It keeps the product model clean: Excel rows are staged and reviewed first, then committed into normalized CRM tables only after candidate generation and approval.

> ## ⚠️ Deploying this? Read [DEPLOYMENT.md](DEPLOYMENT.md) first.
>
> **`alembic upgrade head` MUST be run against the production database.** Local
> password authentication has been removed from the code, but until the
> migration `backend/alembic/versions/20260726_0020_drop_local_password_hash.py`
> runs, the `password_hash` column and its bcrypt hashes remain physically
> present in production. The app ignores the column so nothing breaks, but the
> security requirement to eliminate local credential storage is **not satisfied
> until this migration lands**.
>
> It is a **one-way migration** — it drops a column and destroys the hash data
> irreversibly. **Take a database backup first** and run it as a deliberate,
> confirmed step.

## Current MVP Capabilities

- Microsoft Entra ID single sign-on with `ADMIN` and `USER` roles
- Admin user management (roles, per-section access, activate/deactivate)
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
- Auth: Microsoft Entra ID SSO only (MSAL SPA + PKCE, no client secret, no stored passwords)
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

Environment configuration is split per service:

- `backend/.env.example` -> copy to `backend/.env` (FastAPI: database, Entra ID validation, docs exposure)
- `frontend/.env.example` -> copy to `frontend/.env.local` (Next.js: proxy target, public Entra ID values)

Key backend variables (see `backend/.env.example` for the full annotated list):

```powershell
$env:DATABASE_URL="mssql+pyodbc://@localhost\SQLEXPRESS01/BorusanAIEcosystemCRM?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
$env:ENVIRONMENT="development"   # enables /docs; anything else disables them (fail closed)
$env:ENTRA_TENANT_ID="<directory-tenant-id>"
$env:ENTRA_CLIENT_ID="<application-client-id>"
$env:ENTRA_ADMIN_UPNS="first.admin@borusan.com"   # bootstrapped as ADMIN on first sign-in
```

Authentication is Microsoft Entra ID single sign-on **only**. The application
stores no passwords, exposes no local sign-in endpoint, and needs no JWT signing
secret. The frontend signs in with MSAL as a public client (SPA platform, PKCE)
and sends the resulting OIDC **ID token** as the API bearer; the backend
validates its signature against Microsoft's JWKS and checks the issuer, tenant
(`tid`), and audience. **No client secret is used anywhere** — do not add one.

Matching frontend values (`frontend/.env.local`, public by design, baked into
the bundle at build time): `NEXT_PUBLIC_ENTRA_CLIENT_ID`,
`NEXT_PUBLIC_ENTRA_TENANT_ID`, and `NEXT_PUBLIC_ENTRA_REDIRECT_URI` (base origin
only; the app appends `/auth/callback`).

Run migrations and seed controlled data/admin:

```powershell
python -m alembic upgrade head
python -m app.db.seed
```

Run backend:

```powershell
python -m uvicorn app.main:app --reload
```

Backend docs (only when `ENVIRONMENT=development`; production returns 404):

```text
http://127.0.0.1:8000/docs
```

### Docker (production images)

```powershell
# Backend (build from the repository root):
docker build -f backend/Dockerfile -t borusan-crm-backend .
# Frontend (NEXT_PUBLIC_* are baked at build time; see frontend/Dockerfile):
docker build -t borusan-crm-frontend ./frontend
```

Secrets are never baked into images; pass them at runtime with `--env-file`.

Full deployment procedure — including the **required** `alembic upgrade head`
step, the Entra environment/app-registration requirements, and post-deployment
checks — is in [DEPLOYMENT.md](DEPLOYMENT.md).

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

There is nothing to set up per user: anyone in the tenant signs in with their
Microsoft account, and a CRM record is created automatically on first sign-in
(role `USER`, all controlled sections `HIDDEN` until an admin grants access).

To make sure at least one administrator exists before the first sign-in, list
their Entra UPN(s) in `ENTRA_ADMIN_UPNS`; those accounts are promoted to `ADMIN`
when they sign in. `python -m app.db.seed` can additionally pre-create an ADMIN
row from `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_FULL_NAME` (no credential is
stored) so section access can be configured ahead of time.

Admins manage roles and per-section access at `/admin/users`.

## Locked Out? Admin Recovery Procedure

**Read this before you need it.** Authentication is Microsoft Entra ID only —
there is no local password, no break-glass account, and no way to reset one.
This is deliberate (Information Security requires that the application hold no
internal user credentials), so recovery works through configuration, not through
a hidden login.

### Case 1: no CRM administrator can sign in

Symptoms: the last ADMIN was demoted to USER or deactivated, or nobody was ever
made an admin, so `/admin/*` is unreachable for everyone.

1. Edit `backend/.env` and add the administrator's **Entra UPN** (their Microsoft
   sign-in address, e.g. `first.admin@borusan.com`) to `ENTRA_ADMIN_UPNS`.
   The value is a comma-separated list:

   ```env
   ENTRA_ADMIN_UPNS=first.admin@borusan.com,second.admin@borusan.com
   ```

2. Restart the backend so the new value is read.
3. Have that person sign in again at `/login`.

The UPN list is re-evaluated on **every** sign-in, so the account is promoted to
`ADMIN` the moment they authenticate — no database surgery, no redeploy of the
frontend. This works whether or not a CRM record already exists for them: an
existing row is promoted, and a missing one is created as `ADMIN`.

If the account is also **deactivated**, sign-in is refused before the promotion
runs. Reactivate the row first (see Case 3), then sign in.

After recovery, trim `ENTRA_ADMIN_UPNS` back to the intended bootstrap list —
it is privileged configuration, and every UPN on it becomes an admin on sign-in.

### Case 2: nobody in the tenant can sign in

If Microsoft Entra ID or the tenant itself is unavailable, the CRM is
inaccessible to everyone including administrators. There is no application-level
workaround; this is the accepted consequence of storing no local credentials.
In practice a tenant outage also takes out Outlook, Teams, and SharePoint, so
the CRM is not the binding constraint. Wait for Entra to recover.

Also check these before assuming an outage — they produce the same symptom:

- the Azure app registration was deleted, or its **SPA** redirect URI no longer
  matches `<origin>/auth/callback`;
- `ENTRA_TENANT_ID` / `ENTRA_CLIENT_ID` drifted apart between the backend `.env`
  and the frontend build args;
- the frontend was rebuilt without the `NEXT_PUBLIC_ENTRA_*` values (they are
  baked in at **build** time, not read at run time).

### Case 3: last-resort database access

Only if the above cannot be used. Requires SQL Server access, and stores no
credential — it just flips the role and active flags:

```sql
UPDATE users SET role = 'ADMIN', is_active = 1 WHERE email = 'first.admin@borusan.com';
```

`email` holds the lower-cased Entra UPN and is the sole identity key, so it must
match the sign-in address exactly. Prefer Case 1: it is auditable through
configuration management, whereas direct SQL is not captured in the CRM audit
log.

## Smoke Test

With backend running. The script cannot mint its own token, so supply a current
Entra ID token for an ADMIN user (copy the bearer token the signed-in browser
sends to `/api/backend`):

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\Activate.ps1
$env:SMOKE_API_BASE_URL="http://127.0.0.1:8000"
$env:SMOKE_BEARER_TOKEN="<paste-current-entra-id-token>"
python scripts\smoke_test_api.py
```

## Common Troubleshooting

- `pyodbc` cannot connect: confirm SQL Server is running, database exists, and ODBC Driver 17/18 is installed.
- Driver 18 certificate errors: add `TrustServerCertificate=yes` for local MVP.
- Sign-in fails: check `ENTRA_TENANT_ID`/`ENTRA_CLIENT_ID` match the app registration on both services, that the Azure redirect URI is registered on the **SPA** platform as `<origin>/auth/callback`, and that the account is not deactivated in `/admin/users`.
- No admin exists: add the UPN to `ENTRA_ADMIN_UPNS` and sign in again.
- Frontend cannot reach API: confirm `NEXT_PUBLIC_API_BASE_URL=/api/backend`, `BACKEND_API_ORIGIN=http://127.0.0.1:8000`, restart `npm run dev`, and open `http://localhost:3000/api/backend/health`.
- Alembic command not found: run `python -m alembic upgrade head` from `backend` with the venv activated.
- Imported Excel records do not count on leaderboard: this is intentional. Only manual CRM contributions count.

## Handover Docs

Start with:

- `docs/local_runbook.md`
- `docs/auth_entra_id_setup.md`
- `docs/demo_script.md`
- `docs/qa_checklist.md`
- `docs/security_checklist.md`
- `docs/it_handover_notes.md`
- `docs/backup_restore_notes.md`
