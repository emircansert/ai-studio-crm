# Deployment Notes

Operational steps required when deploying the Borusan AI Ecosystem CRM. Read
this before deploying; some steps are irreversible.

---

## ⚠️ REQUIRED: run the database migration for the Entra-only auth cutover

**`alembic upgrade head` MUST be run against the production database as part of
this deployment.**

Local password authentication has been removed from the code, but until this
migration runs, the `password_hash` column and its bcrypt hashes remain
physically present in the production database — the app ignores the column so
nothing breaks, but the security requirement to eliminate local credential
storage is not satisfied until this migration lands.

**This is a one-way migration (drops a column, destroys the hash data
irreversibly) — take a DB backup first and run it as a deliberate, confirmed
step.**

Migration file:

```text
backend/alembic/versions/20260726_0020_drop_local_password_hash.py
```

### Procedure

1. **Back up the production database.** The hashes cannot be recovered after
   this runs. The migration's `downgrade()` re-creates the column shape only —
   it restores an empty column, not the data.

2. Confirm the current revision before upgrading:

   ```powershell
   cd backend
   python -m alembic current
   ```

   Expect `20260707_0019`. If it is already `20260726_0020`, the migration has
   run and no action is needed.

3. Run the migration:

   ```powershell
   python -m alembic upgrade head
   ```

4. Verify the column is gone and user rows survived:

   ```sql
   SELECT COUNT(*) AS user_count FROM users;
   SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'users';
   ```

   `password_hash` must not appear. The user count must be unchanged — this
   migration drops a column, never a row.

### Verified on the development database

Run against `BorusanAIEcosystemCRM` on 2026-07-26: 5 users before, 5 users
after; remaining columns `id, email, full_name, role, is_active, created_at,
updated_at, last_login_at`.

---

## Required environment configuration

Authentication is Microsoft Entra ID single sign-on only. **No client secret is
used anywhere** — do not add one.

**Backend** (`backend/.env`):

| Variable | Notes |
| --- | --- |
| `DATABASE_URL` | The only real secret in the backend configuration. |
| `ENVIRONMENT` | Must NOT be `development` in production, or Swagger/ReDoc/OpenAPI are exposed. Fails closed on any other value. |
| `ENTRA_TENANT_ID` | Directory (tenant) ID from the app registration. |
| `ENTRA_CLIENT_ID` | Application (client) ID. Also the accepted token audience. |
| `ENTRA_ADMIN_UPNS` | Comma-separated UPNs bootstrapped as ADMIN on sign-in. Privileged — keep short and review after rollout. |

**Frontend** — these are compiled into the browser bundle at **build** time, so
they must be passed as Docker build args, not only at container-run time. None
are secrets (client id, tenant id, and redirect URI are public OIDC metadata):

| Variable | Notes |
| --- | --- |
| `NEXT_PUBLIC_ENTRA_CLIENT_ID` | Must match the backend `ENTRA_CLIENT_ID`. |
| `NEXT_PUBLIC_ENTRA_TENANT_ID` | Must match the backend `ENTRA_TENANT_ID`. |
| `NEXT_PUBLIC_ENTRA_REDIRECT_URI` | **Base origin only**, e.g. `https://library.borusan.com`. The app appends `/auth/callback`. |
| `BACKEND_API_ORIGIN` | Server-side proxy target. Runtime variable, not compiled in. |

### Azure app registration

Register the redirect URI under the **Single-page application (SPA)** platform,
as the full callback path:

```text
https://library.borusan.com/auth/callback
```

Do **not** use the Web platform. This app redeems the authorization code in the
browser with PKCE, which Microsoft only permits for the SPA client type. A Web
registration fails at the final token-redemption step with `AADSTS9002326`, and
sign-in appears to work right up until that point — which makes the
misconfiguration easy to miss.

---

## Post-deployment checks

1. `GET /api/v1/health` and `/api/v1/health/readiness` return `ok`.
2. `GET /api/v1/auth/config` returns `{"auth_mode": "entra"}`.
3. `/docs`, `/redoc`, and `/openapi.json` return **404** (docs lockdown active).
4. `POST /api/v1/auth/login` returns **404** — the endpoint no longer exists.
   Together with a `users` table that has no `password_hash` column, this is the
   check that local credentials are gone rather than merely disabled.
5. One real Microsoft sign-in completes end to end and lands on `/dashboard`.
6. The signed-in administrator can open `/admin/users`.

## If nobody can sign in

There is no local password and no break-glass account by design. See
**"Locked Out? Admin Recovery Procedure"** in the [README](README.md) — in
short: add the administrator's Entra UPN to `ENTRA_ADMIN_UPNS`, restart the
backend, and have them sign in again.

An Entra ID or tenant-wide outage makes the CRM inaccessible to everyone,
administrators included. This is the accepted consequence of holding no internal
user credentials; the trade-off is documented in
[docs/auth_entra_id_setup.md](docs/auth_entra_id_setup.md).
