# IT Handover Notes

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

Current:

- Local JWT login.
- Password hashes stored in SQL Server.
- Roles: `ADMIN`, `USER`.

Future:

- Microsoft Entra ID SSO.
- Map Entra users/groups into CRM `users`.
- Keep CRM user ids stable for audit logs and leaderboard contributions.

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

## Microsoft Entra ID Integration Path

Recommended future path:

1. Add an auth provider abstraction around current JWT dependency.
2. Validate Entra access tokens server-side.
3. Map token identity to CRM `users`.
4. Map Entra groups to CRM roles.
5. Keep local admin fallback only for break-glass/local development if approved.

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
