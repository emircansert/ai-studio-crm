# IT Handover Notes

> **⚠️ Deploying? `alembic upgrade head` MUST be run against the production
> database.** Local password authentication has been removed from the code, but
> the `password_hash` column and its bcrypt hashes stay physically present in
> production until migration
> `backend/alembic/versions/20260726_0020_drop_local_password_hash.py` runs.
> It is a one-way migration that destroys the hash data irreversibly — back up
> the database first. Full procedure: [DEPLOYMENT.md](../DEPLOYMENT.md).

## Current Local Architecture

The CRM is a local-first MVP with three main components:

- Backend API: FastAPI running on Python.
- Frontend UI: Next.js running on Node.js.
- Database: Microsoft SQL Server accessed through SQLAlchemy and `pyodbc`.

The local default backend URL is `http://127.0.0.1:8000`. The local frontend URL is `http://localhost:3000`.

## Backend

The backend contains:

- JWT authentication.
- Admin/user roles.
- SQLAlchemy models and services.
- Alembic migrations.
- Excel import staging, candidate generation, and commit flow.
- CRM APIs for organizations, contacts, notes, Borusan fit, opportunities, events, follow-ups, leaderboard, branding, and audit logs.

Operational commands are documented in `docs/local_runbook.md`.

## Frontend

The frontend contains:

- App shell with Borusan AI Studio branding.
- Login and protected routes.
- Startup Library, Company Detail, Import Center, PoC Pipeline, Events, Network, AI Tools, Follow-ups, Leaderboard, Admin pages.
- Centralized API client using `NEXT_PUBLIC_API_BASE_URL`.

## Database Dependency

The MVP uses Microsoft SQL Server. Local development can use SQL Server Express. Corporate deployment can use internal SQL Server or Azure SQL after connection, security, and backup review.

Database name:

```text
BorusanAIEcosystemCRM
```

Migration command:

```powershell
python -m alembic upgrade head
```

Seed command:

```powershell
python -m app.db.seed
```

## File Upload Storage

Current local storage:

- Imported workbooks: `backend/uploads/`
- Branding/logo assets: `backend/uploads/branding/`

This is acceptable for local MVP. Corporate deployment should move uploads to one of:

- Managed internal file share with backup.
- Azure Blob Storage.
- Another approved object storage service.

The API boundary is already separated enough to migrate storage later.

## Authentication Model

Microsoft Entra ID single sign-on is the **only** authentication method:

- The frontend signs in with MSAL as a public client (SPA platform, PKCE,
  **no client secret**) and sends the OIDC ID token as the API bearer.
- The backend validates the RS256 signature against Microsoft's public JWKS and
  checks issuer, tenant (`tid`), audience, and expiry.
- The application stores **no passwords or credential material of any kind**.
  There is no login endpoint, no password reset, and no `password_hash` column
  (dropped in migration `20260726_0020`).
- `users` holds only the Entra UPN (`email`), display name, role, active flag,
  and last-login timestamp. CRM user ids stay stable, so audit logs and
  leaderboard contributions survive identity changes.
- Users are provisioned just-in-time on first sign-in as `USER` with every
  controlled section `HIDDEN`. Roles and section access are managed in the CRM
  at `/admin/users`, not in Entra.
- Roles: `ADMIN`, `USER`.

Required configuration: `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`, and
`ENTRA_ADMIN_UPNS` on the backend; `NEXT_PUBLIC_ENTRA_TENANT_ID`,
`NEXT_PUBLIC_ENTRA_CLIENT_ID`, and `NEXT_PUBLIC_ENTRA_REDIRECT_URI` baked into
the frontend build. See `docs/auth_entra_id_setup.md`.

### Admin recovery (operators: read this before you need it)

There is no break-glass account by design. If no CRM administrator can sign in,
add their Entra UPN to `ENTRA_ADMIN_UPNS` in `backend/.env`, restart the
backend, and have them sign in again — the list is re-evaluated on every
sign-in, so they are promoted to `ADMIN` immediately. Full procedure, including
the tenant-outage case and the last-resort SQL fallback, is in the README under
**"Locked Out? Admin Recovery Procedure"**.

An Entra or tenant-wide outage makes the CRM inaccessible to everyone,
administrators included. This is the accepted consequence of holding no internal
user credentials; the same outage takes out Microsoft 365 generally.

## Admin/User Roles

ADMIN can:

- Manage users.
- Upload/change branding.
- View audit logs.
- Use imports and CRM functions.

USER can:

- Use CRM workflows.
- Add/edit CRM records where endpoints allow.
- Create notes, contacts, follow-ups, and opportunities.

## Audit Logs

Audit logs record accountability events. They are not a replacement for infrastructure logs. Corporate deployment should decide retention and monitoring approach.

## Data Tables Overview

Core domain:

- `users`
- `organizations`
- `contacts`
- `statuses`
- `borusan_companies`
- `organization_borusan_fit`
- `tags`
- `opportunities`
- `events`
- `notes`
- `follow_up_actions`

Import:

- `import_batches`
- `import_sheets`
- `import_rows`
- `import_warnings`
- `import_candidates`

Admin/ops:

- `audit_logs`
- `branding_assets`
- `user_contributions`

## Deployment Options

### Internal Windows Server

- Run backend as a Windows service using Python/uvicorn or a process manager.
- Serve frontend with Node.js or as a built Next.js app behind IIS/reverse proxy.
- Use internal SQL Server.
- Use HTTPS via internal certificates.

### IIS / Reverse Proxy

- IIS can terminate HTTPS and reverse proxy to backend/frontend processes.
- CORS should be restricted to approved frontend hostnames.
- Static/upload file serving must be reviewed carefully.

### Azure App Service / Azure Container Apps

- Backend and frontend can be deployed as separate apps/services.
- Use Azure SQL or internal SQL Server connectivity.
- Store secrets in Key Vault/App Settings.
- Move uploads to Azure Blob Storage.

### Database Options

- Internal SQL Server for corporate network deployment.
- Azure SQL for cloud deployment.

## Microsoft Entra ID Integration Status

**Complete.** Entra ID SSO is implemented and is the only authentication method;
see the Authentication Model section above and `docs/auth_entra_id_setup.md`.

Local password login was removed entirely (not merely disabled) and the
`password_hash` column was dropped, per the Information Security requirement
that the application work exclusively through Entra users and hold no internal
user information. **A local admin fallback was deliberately not kept** — the
availability trade-off is documented in `docs/auth_entra_id_setup.md` under
"Availability risk to accept explicitly".

Remaining optional work, none of it required to operate the system:

1. Map Entra **groups** to CRM roles (today roles are managed per user in the
   CRM, which keeps the CRM the source of truth for authorization).
2. Review browser `localStorage` token storage if Information Security requires
   HttpOnly session cookies.

## Security Review Items

- SSO/role model.
- Secret storage.
- HTTPS and reverse proxy.
- SQL Server least privilege.
- Upload scanning and file retention.
- Audit log retention.
- Backup/restore testing.
- Dependency vulnerability scanning.

## Backup / Restore Expectations

- Schedule SQL Server backups.
- Back up uploaded files with matching retention.
- Test restore into a non-production environment.
- Do not rely on CSV export as a backup strategy.
