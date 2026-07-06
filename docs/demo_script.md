# Demo Script

Use this flow for a Borusan internal local MVP demo.

## Preparation

1. Start SQL Server.
2. Run backend at `http://127.0.0.1:8000`.
3. Run frontend at `http://localhost:3000`.
4. Have `Ekosistem_Library_V2.xlsx` available.
5. Login with an admin user.

## Demo Flow

### 1. Login

- Open `http://localhost:3000`.
- Login as an admin.
- Explain that local JWT auth is MVP-only and the architecture is ready for future Microsoft Entra ID.

### 2. Dashboard Overview

- Open Dashboard.
- Show total organizations, startups/vendors, opportunities, events, follow-ups, latest import status, Borusan fit counts, and leaderboard preview.
- Position it as the command center replacing scattered Excel views.

### 3. Import Excel Workbook

- Open Import Center.
- Upload `Ekosistem_Library_V2.xlsx`.
- Show detected sheets, staged rows, warnings, duplicate candidates, and preview samples.
- Emphasize that raw Excel values are preserved but dirty rows are not blindly written into CRM tables.

### 4. Generate Candidates

- Generate candidates.
- Show candidate counts for organizations, contacts, Borusan fits, opportunities, events, network institutions, and notes.
- Show the needs-review section if present.

### 5. Commit

- Commit only after candidates are valid or reviewed.
- Explain that commit writes normalized records into domain tables and audit logs the action.

### 6. Startup Library Search/Filter

- Open Startup Library.
- Search for `GenAI`.
- Filter by Borusan company `BORCELIK`.
- Show category, vertical, Added By, Added Date, Last Contact, source, and activity counts.
- Explain support for the use case: "Find GenAI startups relevant for Borcelik."

### 7. Company Detail

- Open a company row.
- Show the profile, category, vertical, website, source/import metadata, contacts, notes, Borusan fits, opportunities, and follow-ups.

### 8. Manual CRM Actions

- Add a note.
- Add a contact.
- Add or update Borusan fit.
- Create a follow-up.
- Explain that manual actions are attributed to the current CRM user.

### 9. Complete Follow-up

- Open Follow-ups or use the Company Detail follow-up card.
- Complete a follow-up.
- Explain that completed manual follow-ups contribute to the leaderboard.

### 10. Leaderboard

- Open Leaderboard.
- Show all-time / last 30 days / last 7 days filters.
- Explain that imported Excel records are excluded. Only manual CRM contributions count.

### 11. Opportunities and Events

- Open PoC Pipeline.
- Open an opportunity detail page and edit stage/topic/owner/dates.
- Open Events Library.
- Open an event detail page and edit relevance/value/comments.

### 12. Admin User Management

- Open Admin Panel > User Management.
- Show user search, create user, role changes, activate/deactivate, and password reset.
- Explain protection against accidentally deactivating the only active admin.

### 13. Branding Upload

- Open Admin Branding.
- Upload or activate a Borusan AI Studio logo.
- Show that the active logo appears globally in the sidebar.

### 14. Audit Logs

- Open Audit Logs.
- Filter by entity/action.
- Expand one payload.
- Explain that audit logs are separate from leaderboard contribution scoring.

### 15. Export CSV

- Return to Startup Library.
- Apply a filter and click Export CSV.
- Explain that export is for working extracts, not database backup.

## Closing Message

The MVP demonstrates an end-to-end CRM workflow: controlled Excel onboarding, normalized records, search/filter, manual relationship management, follow-ups, contribution tracking, admin controls, auditability, and readiness for corporate deployment hardening.
