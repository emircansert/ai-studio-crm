# Security Scan Handover - Borusan AI Ecosystem CRM

## A. Application Overview

Application name: Borusan AI Ecosystem CRM

Purpose: Internal CRM workspace for Borusan AI Studio ecosystem operations. The application manages startup/vendor discovery, company detail records, contacts, notes, Borusan company fit, PoC opportunities, use cases, events/training program activities, AI tools, follow-ups, startup deck uploads, imports, audit logs, and YZ Champion Program scoring.

Current maturity: local/demo MVP. The intended next step is Information Security review and hardening before any group-wide usage.

Architecture:

- Frontend: Next.js / React / TypeScript.
- Backend: FastAPI / Python.
- Database: Microsoft SQL Server via SQLAlchemy and `pyodbc`.
- API style: REST API under `/api/v1`.
- Communication format: JSON for normal API requests/responses.

## B. URLs To Be Scanned

Production or shared test URLs are TBD by IT.

| Item | URL |
|---|---|
| Frontend URL | `<frontend-url>` |
| Backend/API URL | `<backend-url>` |
| API base path | `<backend-url>/api/v1` |
| Swagger UI | `<backend-url>/docs` |
| OpenAPI JSON | `<backend-url>/openapi.json` |
| ReDoc | `<backend-url>/redoc` |
| Local frontend default | `http://localhost:3000` |
| Local backend default | `http://127.0.0.1:8000` |
| Local Swagger UI | `http://127.0.0.1:8000/docs` |
| Local OpenAPI JSON | `http://127.0.0.1:8000/openapi.json` |
| Local ReDoc | `http://127.0.0.1:8000/redoc` |

Confirmed from code:

- FastAPI uses default Swagger UI, OpenAPI JSON, and ReDoc routes.
- `app.include_router(api_router, prefix="/api/v1")` makes application routes available under `/api/v1`.
- OpenAPI export file for scan: `docs/security_scan/openapi.json`.

## C. API Format

- REST API: yes.
- JSON request/response: yes.
- XML endpoints/schemas: no active XML usage.
- multipart/form-data: used for file uploads.
- File downloads: used for startup deck documents and branding/logo content.

## D. Authentication

Current authentication:

- Microsoft Entra ID single sign-on **only**. There is no local login endpoint.
- The frontend signs in with MSAL as a public client (SPA platform, PKCE, no
  client secret) and sends the resulting OIDC **ID token** as
  `Authorization: Bearer <token>`.
- The backend validates the RS256 signature against Microsoft's public JWKS and
  checks issuer, tenant (`tid`), audience (the bare client id), and expiry.
- The application stores **no passwords and no credential material of any kind**;
  `users` holds only UPN, display name, role, active flag, and last login.
- Users are provisioned just-in-time on first successful sign-in.
- Roles: `ADMIN`, `USER`. Inactive users are rejected even with a valid token.
- `last_login_at` is refreshed on sign-in (throttled to 15 minutes).

Deliberately not implemented:

- Any local/break-glass credential. An Entra tenant outage makes the CRM
  inaccessible to everyone including administrators; this is an accepted
  consequence of the "no internal user information" requirement.
- Backend confidential-client authorization code flow (would require a secret).
- SAML federation; MFA is enforced by Entra ID conditional access, not by the app.

Token storage caveat:

- The frontend stores the Entra ID token and user profile in browser `localStorage`.
- This should be reviewed by Information Security if HttpOnly session cookies are required.

## E. Authorization Model

Admin-only areas include:

- Admin user management.
- Audit log listing.
- Branding upload/list/update.
- Excel import upload, candidate generation, candidate decisions, and commit.
- Leaderboard reset.
- Admin champion activity management.
- Archive/unarchive for many business records.

Authenticated user areas include:

- Dashboard.
- Startup Library and organization detail.
- Contacts and notes.
- Borusan fit creation/update.
- Opportunities/PoC.
- Use cases.
- Events Library.
- AI Tools Library.
- Follow-ups.
- Leaderboard.
- Startup deck upload/download.

Known RBAC limitations / areas to review:

- The MVP has only two application roles: `ADMIN` and `USER`.
- Authenticated `USER` accounts can create/update many CRM domain records.
- Some reference-data endpoints, such as tags/statuses/Borusan companies, currently allow authenticated mutation and may need admin-only restriction for production.
- Object-level authorization is broad for MVP. InfoSec/business owners should confirm whether users should be limited by department, company, ownership, or Borusan business unit.

## F. Test Users Needed For Scan

Do not use real production credentials in scan documentation.

Sign-in is Microsoft Entra ID only, so the scanner cannot log in with a
username and password. Provide **test Entra accounts in the tenant** and drive
authenticated scans with the ID token each account obtains after an interactive
sign-in (the bearer token the browser sends to `/api/backend`).

| Role | Placeholder Entra UPN | Credential |
|---|---|---|
| ADMIN | `<admin_test_upn>` | Entra account; token captured after interactive sign-in |
| USER | `<user_test_upn>` | Entra account; token captured after interactive sign-in |

Note that these tokens expire (roughly 60 minutes) and must be refreshed during
long scans. The CRM role is set in **User Management**, not in Entra.

Recommended scan modes:

- Unauthenticated scan.
- Authenticated USER scan.
- Authenticated ADMIN scan.

Admin scan caution:

- Admin endpoints can create, update, archive, import, commit, reset contribution records, and modify users.
- Admin scan should be coordinated and run against a test environment or dedicated test records.

## G. Data Formats And Uploads

JSON:

- Primary request/response format for REST APIs.
- OpenAPI JSON is available for automated scanner import.

XML:

- No active XML endpoints or schemas exist in the current application.

File uploads:

| Upload Type | Endpoint | Role | Allowed Types | Size Limit | Storage |
|---|---|---|---|---:|---|
| Excel import | `POST /api/v1/imports/upload` | ADMIN | `.xlsx` | 25 MB | `backend/uploads/imports` |
| Startup deck | `POST /api/v1/organizations/{id}/documents` | authenticated user | `.pdf`, `.pptx` | 50 MB | `uploads/organization_documents` |
| Branding/logo | `POST /api/v1/admin/branding/upload` | ADMIN | `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp` | 2 MB | `uploads/branding` |

File upload validation includes extension, MIME type where applicable, file size, generated storage filenames, and SHA-256 metadata.

Production recommendation:

- Add malware scanning.
- Move uploaded files to approved managed storage or an internal file share with backup.
- Define file retention and access-control policy.

## H. External Integrations

Confirmed current state:

- No active external AI/LLM API calls.
- No OpenAI, Azure OpenAI, Anthropic, Gemini, or other model API integration.
- No active third-party enrichment API.
- AI-related fields exist as placeholders/future-ready CRM data fields only.

## I. Database

Current database:

- Microsoft SQL Server.
- Local/demo can use SQL Server Express.
- SQLAlchemy ORM and Alembic migrations.
- Production SQL Server environment is TBD by IT.

Production items for IT:

- Least-privilege SQL user.
- Encrypted SQL Server connectivity.
- Network restriction / firewall policy.
- Backup and restore plan.
- SQL Server audit/logging decision.
- Data classification and retention review.

## J. Logging And Audit

Application-level audit logs exist in `audit_logs`.

Audit log examples include:

- Admin user create/update/activate/deactivate/role change and section-access change.
- Import upload/candidate/commit actions.
- CRM create/update/archive operations across many domain records.
- Startup deck upload/archive.
- Branding upload/update.
- Leaderboard reset and champion activity administration.

Caveats:

- Audit coverage is broad but should be formally reviewed before production.
- Application audit logs are not a replacement for web server, reverse proxy, SQL Server, OS, or SIEM logging.
- Retention policy is not implemented in the application and should be defined by IT/security.

## K. Out-of-Scope / Caution For Scan

- Do not run destructive tests against production data without explicit approval.
- File upload tests should use safe synthetic test files.
- Import commit tests can create or update CRM data.
- Admin user management tests can deactivate users or change their roles and section access.
- Archive/delete-like tests should use dedicated test records.
- Leaderboard reset tests should use dry-run mode or test data.
- Rate/load tests should be coordinated.
- Do not scan with real privileged production credentials unless the scan plan explicitly requires it.

## L. Recommended Scan Scope

Recommended areas:

- Frontend web app routes.
- Backend REST API endpoints under `/api/v1`.
- Swagger/OpenAPI-driven API scan using `docs/security_scan/openapi.json`.
- Unauthenticated scan.
- Authenticated USER scan.
- Authenticated ADMIN scan.
- File upload validation.
- RBAC / broken access control.
- Object-level authorization.
- SQL injection and input validation.
- XSS in free-text fields such as notes, descriptions, comments, and uploaded filenames.
- CSRF/session/token handling review.
- Entra ID token validation: forged/expired/wrong-audience/wrong-tenant tokens, and Graph access tokens presented to the CRM API.
- CORS and security headers.
- Dependency vulnerability scan.
- Secret scan.
- Local file storage/path traversal tests for file download endpoints.

## Attachments In This Folder

- `openapi.json`: exported FastAPI OpenAPI schema.
- `api_endpoint_inventory.md`: endpoint inventory and scan notes.
- `data_format_note.md`: JSON/XML/multipart note.
- `postman_collection.json`: starter Postman collection with placeholder credentials.
- `README.md`: folder guide.
