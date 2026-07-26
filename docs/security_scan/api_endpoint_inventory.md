# API Endpoint Inventory for Security Scan

This inventory summarizes the FastAPI REST API exposed under `/api/v1`. The authoritative machine-readable schema is `docs/security_scan/openapi.json`.

Authentication model:

- Public endpoints: no bearer token required.
- Authenticated endpoints: require `Authorization: Bearer <jwt>`.
- Admin endpoints: require an authenticated user with role `ADMIN`.

| Method | Path | Router / Module | Auth Required | Admin Required | Request Body Type | Response Type | Purpose | Security Testing Notes |
|---|---|---|---:|---:|---|---|---|---|
| `GET` | `/api/v1/health` | `health.py` | No | No | none | JSON | Basic health check. | Should not expose secrets or environment values. |
| `GET` | `/api/v1/health/readiness` | `health.py` | No | No | none | JSON | DB/migration/table readiness check. | Verify no connection strings, credentials, or stack traces are returned. |
| `GET` | `/api/v1/health/routes` | `health.py` | No | No | none | JSON | Safe route diagnostics for key route registration. | Validate it only exposes route names, not sensitive runtime config. |
| `GET` | `/api/v1/auth/config` | `auth.py` | No | No | none | JSON | Reports the auth mode (always `entra`). | Confirm it leaks no tenant/client identifiers or other config. |
| `GET` | `/api/v1/auth/me` | `auth.py` | Yes | No | none | JSON | Current authenticated user; provisions the CRM record just-in-time. | Test expired/forged/wrong-audience/wrong-tenant Entra tokens and deactivated users. |
| `GET` | `/api/v1/users/active` | `users.py` | Yes | No | none/query | JSON | Active user picker for assignments. | Confirm inactive users are not exposed. |
| `GET` | `/api/v1/dashboard/summary` | `dashboard.py` | Yes | No | none/query | JSON | Dashboard metrics. | Check authorization and aggregate data visibility. |
| `GET, POST` | `/api/v1/organizations` | `organizations.py` | Yes | No | JSON for `POST`; query for `GET` | JSON | Startup/company/library list and manual create. | Test filtering, pagination, injection, validation, RBAC expectations. |
| `GET, PATCH, PUT` | `/api/v1/organizations/{organization_id}` | `organizations.py` | Yes | No | JSON for write methods | JSON | Organization detail/update. | Test object-level authorization expectations and input validation. |
| `GET` | `/api/v1/organizations/export` | `organizations.py` | Yes | No | query | CSV file download | Startup Library CSV export. | Confirm filters respected and archived records visibility is role-aware. |
| `PATCH` | `/api/v1/organizations/{organization_id}/archive` | `organizations.py` | Yes | Yes | JSON optional reason | JSON | Archive organization. | Admin-only destructive-like operation; scan only on test records. |
| `PATCH` | `/api/v1/organizations/{organization_id}/unarchive` | `organizations.py` | Yes | Yes | JSON optional reason | JSON | Restore archived organization. | Admin-only; test audit log creation. |
| `GET, POST` | `/api/v1/organizations/{organization_id}/contacts` | `organizations.py` | Yes | No | JSON for `POST` | JSON | List/add contacts for organization. | Test contact PII handling, validation, object access. |
| `GET, POST` | `/api/v1/contacts` | `contacts.py` | Yes | No | JSON for `POST` | JSON | Global contact list/create. | Test search/pagination and access control. |
| `GET, PATCH, PUT, DELETE` | `/api/v1/contacts/{contact_id}` | `contacts.py` | Yes | Mixed | JSON for write methods | JSON/none | Contact detail/update/delete legacy archive behavior. | Archive/unarchive is admin-only; legacy delete should be tested only on test data. |
| `PATCH` | `/api/v1/contacts/{contact_id}/archive`, `/unarchive` | `contacts.py` | Yes | Yes | JSON optional reason | JSON | Archive/restore contact. | Verify USER cannot archive globally unless explicitly allowed. |
| `GET, POST` | `/api/v1/organizations/{organization_id}/notes` | `organizations.py` | Yes | No | JSON for `POST` | JSON | List/add organization notes. | Notes may contain business-sensitive free text; test XSS and validation. |
| `PUT, DELETE` | `/api/v1/notes/{note_id}` | `notes.py` | Yes | Mixed | JSON for `PUT` | JSON/none | Note update/delete legacy archive behavior. | Update is authenticated; archive/unarchive endpoints are admin-only. |
| `PATCH` | `/api/v1/notes/{note_id}/archive`, `/unarchive` | `notes.py` | Yes | Yes | JSON optional reason | JSON | Archive/restore note. | Test audit logging and access control. |
| `GET, POST` | `/api/v1/organizations/{organization_id}/borusan-fit` | `organizations.py` | Yes | No | JSON for `POST` | JSON | List/add Borusan fit. | Test duplicate fit constraints and role expectations. |
| `PUT, DELETE` | `/api/v1/organizations/{organization_id}/borusan-fit/{fit_id}` | `organizations.py` | Yes | Mixed | JSON for `PUT` | JSON/none | Update/delete legacy archive behavior. | Archive/unarchive endpoints are admin-only. |
| `PATCH` | `/api/v1/organizations/{organization_id}/borusan-fit/{fit_id}/archive`, `/unarchive` | `organizations.py` | Yes | Yes | JSON optional reason | JSON | Archive/restore Borusan fit. | Admin-only; test broken access control. |
| `GET, POST` | `/api/v1/opportunities` | `opportunities.py` | Yes | No | JSON for `POST` | JSON | PoC/opportunity list/create. | Test stage/status values, injection, object references. |
| `GET, PATCH, PUT` | `/api/v1/opportunities/{opportunity_id}` | `opportunities.py` | Yes | No | JSON for write methods | JSON | Opportunity detail/update. | Test object-level access and validation. |
| `PATCH` | `/api/v1/opportunities/{opportunity_id}/archive`, `/unarchive` | `opportunities.py` | Yes | Yes | JSON optional reason | JSON | Archive/restore opportunity. | Admin-only destructive-like operation. |
| `GET, POST` | `/api/v1/use-cases` | `use_cases.py` | Yes | No | JSON for `POST` | JSON | Use case proposal list/create. | Creating/projectizing use cases can affect Champion Score; scan on test users. |
| `GET, PUT` | `/api/v1/use-cases/{use_case_id}` | `use_cases.py` | Yes | No | JSON for `PUT` | JSON | Use case detail/update. | Test status transitions and validation. |
| `PATCH` | `/api/v1/use-cases/{use_case_id}/archive`, `/unarchive` | `use_cases.py` | Yes | Yes | JSON optional reason | JSON | Archive/restore use case. | Admin-only. |
| `GET, POST` | `/api/v1/events` | `events.py` | Yes | No | JSON for `POST` | JSON | Event Library records. | Test date fields, comments, XSS, filters. |
| `GET, PATCH, PUT` | `/api/v1/events/{event_id}` | `events.py` | Yes | No | JSON for write methods | JSON | Event detail/update. | Test validation and object access. |
| `PATCH` | `/api/v1/events/{event_id}/archive`, `/unarchive` | `events.py` | Yes | Yes | JSON optional reason | JSON | Archive/restore event. | Admin-only. |
| `GET, POST` | `/api/v1/program-activities` | `program_activities.py` | Yes | Mixed | JSON for `POST` | JSON | Program events/training list/create. | Create/update/admin participant actions can affect Champion Score. |
| `GET, PUT` | `/api/v1/program-activities/{activity_id}` | `program_activities.py` | Yes | Mixed | JSON for `PUT` | JSON | Program activity detail/update. | Writes are admin-only; reads authenticated. |
| `POST, PUT` | `/api/v1/program-activities/{activity_id}/participants[...]` | `program_activities.py` | Yes | Yes | JSON | JSON | Add/update event/training participants. | Marking attended/completed creates Champion evidence; use test records. |
| `PATCH` | `/api/v1/program-activities/{activity_id}/archive`, `/unarchive` | `program_activities.py` | Yes | Yes | JSON optional reason | JSON | Archive/restore program activity. | Admin-only. |
| `GET, POST` | `/api/v1/ai-tools` | `ai_tools.py` | Yes | No | JSON for `POST` | JSON | AI Tools Library list/create. | Manual create affects CRM Activity Points and Champion evidence. |
| `GET, PUT, PATCH` | `/api/v1/ai-tools/{tool_id}` | `ai_tools.py` | Yes | No | JSON for write methods | JSON | AI tool detail/update. | Test field validation and XSS in notes/description. |
| `PATCH` | `/api/v1/ai-tools/{tool_id}/archive`, `/unarchive` | `ai_tools.py` | Yes | Yes | JSON optional reason | JSON | Archive/restore AI tool. | Admin-only. |
| `GET, POST` | `/api/v1/follow-ups` | `follow_ups.py` | Yes | No | JSON for `POST` | JSON | Follow-up/task list/create. | Completion can affect leaderboard/Champion evidence. |
| `GET, PUT` | `/api/v1/follow-ups/{follow_up_id}` | `follow_ups.py` | Yes | No | JSON for `PUT` | JSON | Follow-up detail/update. | Test assignment and object references. |
| `PATCH` | `/api/v1/follow-ups/{follow_up_id}/complete`, `/cancel` | `follow_ups.py` | Yes | No | JSON optional | JSON | Complete/cancel follow-up. | Completion can mutate contribution score. |
| `PATCH` | `/api/v1/follow-ups/{follow_up_id}/archive`, `/unarchive` | `follow_ups.py` | Yes | Yes | JSON optional reason | JSON | Archive/restore follow-up. | Admin-only. |
| `GET, POST` | `/api/v1/network` | `network.py` | Yes | No | JSON for `POST` | JSON | Network institution list/create. | Backed by organizations with network type; test filtering and access. |
| `GET, PATCH` | `/api/v1/network/{organization_id}` | `network.py` | Yes | No | JSON for `PATCH` | JSON | Network institution detail/update. | Test object references. |
| `GET, POST` | `/api/v1/imports` | `imports.py` | Yes | Mixed | JSON for generic create | JSON | Import batch list/create metadata. | Upload/generate/decision/commit are admin-only. |
| `POST` | `/api/v1/imports/upload` | `imports.py` | Yes | Yes | multipart form-data | JSON | Upload `.xlsx` workbook. | File upload endpoint; 25 MB limit; test safe files only. |
| `GET` | `/api/v1/imports/{batch_id}`, `/preview`, `/candidates` | `imports.py` | Yes | No | none | JSON | Import batch details, preview, candidate preview. | Verify staged raw values visibility and access expectations. |
| `POST` | `/api/v1/imports/{batch_id}/candidates/generate` | `imports.py` | Yes | Yes | none | JSON | Generate normalized candidates. | Mutates staging tables. |
| `PATCH` | `/api/v1/imports/candidates/{candidate_id}/decision` | `imports.py` | Yes | Yes | JSON | JSON | Approve/reject/skip import candidate. | Admin-only; affects later commit behavior. |
| `POST` | `/api/v1/imports/{batch_id}/commit` | `imports.py` | Yes | Yes | none | JSON | Commit approved candidates into CRM tables. | Creates domain records; coordinate before scanning. |
| `GET, POST` | `/api/v1/tags`, `/api/v1/statuses`, `/api/v1/borusan-companies` | `tags.py`, `statuses.py`, `borusan_companies.py` | Yes | No | JSON for `POST` | JSON | Controlled vocabularies/reference data. | Current MVP allows authenticated users to mutate these; review RBAC expectations. |
| `GET, PATCH` | `/api/v1/tags/{id}`, `/statuses/{id}`, `/borusan-companies/{id}` | reference routers | Yes | No | JSON for `PATCH` | JSON | Reference data detail/update. | Candidate area for stricter admin-only control in production. |
| `GET` | `/api/v1/vocabularies/categories` | `vocabularies.py` | Yes | No | none | JSON | Category vocabulary for UI. | Low-risk read endpoint; verify auth required. |
| `GET` | `/api/v1/leaderboard`, `/me` | `leaderboard.py` | Yes | No | query | JSON | CRM Activity Points leaderboard. | Verify users can only see intended leaderboard data. |
| `GET` | `/api/v1/leaderboard/champion`, `/champion/me`, `/champion/rules`, `/champion/users/{user_id}` | `leaderboard.py` | Yes | No | query | JSON | YZ Champion Score leaderboard and rules. | Check user detail exposure expectations. |
| `POST` | `/api/v1/admin/leaderboard/reset` | `admin_leaderboard.py` | Yes | Yes | JSON | JSON | Dry-run/apply contribution reset exclusion. | Destructive-like admin action; use dry run or test data. |
| `GET, POST` | `/api/v1/admin/users` | `admin_users.py` | Yes | Yes | JSON for `POST` | JSON | Admin user list / pre-provision (no credential is set). | Verify the response carries no credential fields and that `POST` cannot set one. |
| `GET, PUT` | `/api/v1/admin/users/{user_id}` | `admin_users.py` | Yes | Yes | JSON for `PUT` | JSON | Admin user detail/update. | Test last-admin protection, RBAC, and that unknown fields are ignored. |
| `PATCH` | `/api/v1/admin/users/{user_id}/activate`, `/deactivate`, `/role` | `admin_users.py` | Yes | Yes | JSON for role; none for activate/deactivate | JSON | User lifecycle/admin actions. | Sensitive admin-only actions; scan against test users. |
| `GET` | `/api/v1/admin/audit-logs` | `admin_audit_logs.py` | Yes | Yes | query | JSON | Audit log listing. | Verify admin-only access; logs may include before/after business data. |
| `GET, POST, PATCH` | `/api/v1/admin/branding[...]` | `admin_branding.py` | Yes | Mixed | JSON or multipart form-data | JSON/file download | Branding asset management. | Upload is admin-only; active/content reads require authentication. |
| `POST` | `/api/v1/admin/branding/upload` | `admin_branding.py` | Yes | Yes | multipart form-data | JSON | Upload active logo. | File upload endpoint; image types only; 2 MB limit. |
| `GET` | `/api/v1/admin/branding/{asset_id}/content` | `admin_branding.py` | Yes | No | none | file download | Download branding/logo content. | Verify auth required and stored path cannot be manipulated. |
| `GET, POST` | `/api/v1/organizations/{organization_id}/documents` | `organizations.py` | Yes | No | multipart form-data for `POST` | JSON | List/upload startup decks. | File upload endpoint; PDF/PPTX only; 50 MB limit. |
| `GET` | `/api/v1/organizations/{organization_id}/documents/{document_id}/download` | `organizations.py` | Yes | No | none | file download | Download startup deck. | Verify archived files return 404 and path traversal is not possible. |
| `PATCH` | `/api/v1/organizations/{organization_id}/documents/{document_id}/archive`, `/unarchive` | `organizations.py` | Yes | Uploader or Admin | JSON optional reason | JSON | Archive/restore startup deck. | USER can only archive own upload; admin can archive any. |

## Additional Notes

- OpenAPI schema is generated by FastAPI and exported to `docs/security_scan/openapi.json`.
- Most request/response payloads are JSON.
- File uploads use `multipart/form-data`.
- File downloads are used for Startup Decks and branding/logo content.
- XML is not used by the current application.
- Some authenticated mutation endpoints are intentionally available to `USER` role in the MVP. InfoSec/business owners should review whether stricter RBAC is required before group-wide rollout.
