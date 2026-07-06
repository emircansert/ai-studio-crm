# Admin Readiness + Final CRM Polish Phase

## Scope

This phase prepares the local Borusan AI Ecosystem CRM for broader internal MVP usage without changing the product architecture or adding AI features. The system remains FastAPI, SQLAlchemy, Alembic, Microsoft SQL Server, and Next.js.

## Admin User Management

Admins can manage local CRM users through `/api/v1/admin/users` and the `/admin/users` frontend page.

Implemented behavior:
- List and search users by name/email.
- Filter users by role and active state.
- Create users with a temporary password.
- Edit email, full name, role, and active state.
- Activate and deactivate users.
- Reset temporary passwords.
- Never expose password hashes.
- Prevent accidental deactivation or role downgrade of the only active admin.
- Use soft deactivation only; users are not physically deleted.
- Write audit logs for user create, update, activate, deactivate, role change, and password reset.

## Role Rules

The local MVP keeps `ADMIN` and `USER` roles. Admin routes require an active admin account. The frontend hides admin navigation for normal users and shows a clean access denied state if a user reaches an admin URL directly.

This keeps the identity boundary ready for a later Microsoft Entra ID adapter while preserving local JWT authentication for development.

## Authentication Improvements

Inactive users cannot log in. Successful login updates `last_login_at` when available. The frontend clears stored local JWT/user state on `401` or `403` responses and redirects to `/login`.

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

- Local JWT authentication remains the MVP identity provider.
- No Microsoft Entra ID SSO is implemented yet.
- Password reset is admin-set temporary password only; no email workflow exists.
- Follow-ups are polymorphic through `entity_type` and `entity_id`, matching the MVP notes pattern.
- Export is CSV, not formatted XLSX.
- Opportunity and event detail pages are intentionally functional rather than advanced workflow tools.
- Leaderboard scoring remains simple and manual-contribution based only.

## Future Entra ID Migration Note

The local user table remains useful even after Entra ID integration as an application profile and role mapping layer. A future SSO adapter should map Entra identities to CRM `users`, preserve `role`, and keep contribution/audit history tied to stable internal user ids.

## Testing Steps

1. Run the latest Alembic migration.
2. Start the backend and frontend.
3. Login as an admin.
4. Open `/admin/users`, create a user, change role, deactivate/reactivate, and reset password.
5. Confirm inactive users cannot log in.
6. Upload or activate a logo in `/admin/branding`, then confirm it appears in the sidebar.
7. Create and complete a follow-up from `/follow-ups` and from Company Detail.
8. Open an opportunity and event detail page from their list views and save edits.
9. Export Startup Library CSV from `/companies`.
10. Review `/admin/audit-logs` for user, CRM, follow-up, branding, and import actions.
