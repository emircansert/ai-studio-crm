# Admin Readiness + Final CRM Polish Phase

## Scope

This phase prepares the local Borusan AI Ecosystem CRM for broader internal MVP usage without changing the product architecture or adding AI features. The system remains FastAPI, SQLAlchemy, Alembic, Microsoft SQL Server, and Next.js.

## Admin User Management

Admins can manage local CRM users through `/api/v1/admin/users` and the `/admin/users` frontend page.

Implemented behavior:
- List and search users by name/email.
- Filter users by role and active state.
- Pre-provision a user by Entra UPN so role and section access can be set before their first sign-in. No credential is created.
- Edit email, full name, role, and active state.
- Activate and deactivate users.
- Manage per-section access (HIDDEN / VIEW / FULL).
- Store no password or credential material at all.
- Prevent accidental deactivation or role downgrade of the only active admin.
- Use soft deactivation only; users are not physically deleted.
- Write audit logs for user create, update, activate, deactivate, role change, and section-access change.

## Role Rules

The CRM keeps `ADMIN` and `USER` roles. Admin routes require an active admin account. The frontend hides admin navigation for normal users and shows a clean access denied state if a user reaches an admin URL directly.

Authentication is Microsoft Entra ID single sign-on only; the CRM remains the source of truth for the `ADMIN`/`USER` role and per-section access.

## Authentication Improvements

Inactive users cannot sign in, even with a valid Entra token. Successful sign-in updates `last_login_at`. The frontend clears the stored token and user state on `401` or `403` responses and redirects to `/login`.

## Branding Behavior

Admin branding supports safe logo upload and active-logo selection. The global app shell now loads the active logo and shows it in the sidebar brand area. If no logo exists, or if loading fails, the shell falls back to the Borusan AI Studio text/mark placeholder.

Branding assets remain local-file backed for MVP with an API boundary that can later move to blob/object storage.

## Follow-up / Task Management

Follow-up management is implemented through `/api/v1/follow-ups` and the `/follow-ups` frontend page.

Supported behavior:
- Create follow-ups for CRM entities.
- List by status, entity type, entity id, and assignee.
- Mark follow-ups as completed.
- Cancel follow-ups.
- Track creator, assignee, completer, completion timestamp, due date, and status.
- Show follow-ups on Company Detail.
- Award leaderboard contribution points when a manual user completes a follow-up.

Follow-up statuses are intentionally simple for MVP: `OPEN`, `DONE`, `CANCELLED`.

## Opportunity Detail

The frontend now includes `/opportunities/[id]`.

It shows and edits:
- Title
- Organization
- Borusan company
- Type
- Stage
- Status
- Owner
- Topic
- Terms
- Value hypothesis
- Expected dates
- Last contact date
- Related follow-ups

Backend opportunity create/update already writes audit logs and manual contribution events for creation.

## Event Detail

The frontend now includes `/events/[id]`.

It shows and edits:
- Name
- Start/end dates
- Raw date text
- Location
- Geography
- Area/category
- AI program relevance
- Value creation potential
- Comments

Backend event create/update already writes audit logs and manual contribution events for creation.

## Export Behavior

Startup Library export is available through `GET /api/v1/organizations/export` and the Startup Library `Export CSV` button.

The export:
- Uses CSV for the MVP.
- Requires authentication.
- Respects the practical organization filters used by the list view where supported.
- Does not export raw staging/import candidate tables.
- Avoids loading all rows through the UI by streaming the generated CSV response from the backend.

## Dashboard and Audit Polish

Dashboard now includes:
- Real CRM metrics.
- Open follow-ups count.
- Overdue follow-ups count.
- Latest import status.
- Leaderboard preview.
- Quick actions for adding companies, import, follow-ups, and leaderboard.

Audit Logs now include:
- Admin-only list view.
- Filters for action, entity type, and actor user id.
- Readable action/entity formatting.
- Expandable JSON payloads instead of showing raw JSON by default.

## Known Limitations

- Microsoft Entra ID requires the tenant and client ids from the Azure App Registration before it can be tested against a real tenant.
- The frontend stores the Entra ID token in localStorage; review with Information Security if HttpOnly cookies are required.
- There is no password reset because there are no passwords; sign-in credentials are managed entirely in the user's Microsoft account.
- Follow-ups are polymorphic through `entity_type` and `entity_id`, matching the MVP notes pattern.
- Export is CSV, not formatted XLSX.
- Opportunity and event detail pages are intentionally functional rather than advanced workflow tools.
- Leaderboard scoring remains simple and manual-contribution based only.

## Entra ID Note

The local user table remains the application profile and role mapping layer. Entra identities map to CRM `users.email`, preserve the existing CRM role, and keep contribution/audit history tied to stable internal user ids.

## Testing Steps

1. Run the latest Alembic migration.
2. Start the backend and frontend.
3. Sign in with Microsoft as an admin.
4. Open `/admin/users`, pre-provision a user, change role, deactivate/reactivate, and adjust section access.
5. Confirm inactive users cannot sign in even with a valid Entra token.
6. Upload or activate a logo in `/admin/branding`, then confirm it appears in the sidebar.
7. Create and complete a follow-up from `/follow-ups` and from Company Detail.
8. Open an opportunity and event detail page from their list views and save edits.
9. Export Startup Library CSV from `/companies`.
10. Review `/admin/audit-logs` for user, CRM, follow-up, branding, and import actions.
