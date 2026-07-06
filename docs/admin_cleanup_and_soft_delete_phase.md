# Admin Cleanup and Soft Delete Phase

## Purpose

This phase adds safe cleanup behavior for demo, test, and future corporate use. The CRM now prefers archive/restore over physical deletion for business records.

## Archive vs Hard Delete

Archive is the supported MVP behavior.

Archived records:
- Stay in the database.
- Are hidden from normal lists and dashboard counts.
- Remain available for audit/history.
- Can be restored by an admin.
- Do not automatically remove historical leaderboard contributions.

Hard delete is intentionally not exposed in the UI. It is risky because CRM records are connected to imports, audit logs, notes, contacts, opportunities, and contribution history. If hard delete is ever required, it should be implemented later as a restricted, audited danger-zone tool and only for already archived records.

## Tables With Archive Fields

The following tables now support archive metadata:

- `organizations`
- `opportunities`
- `events`
- `contacts`
- `notes`
- `organization_borusan_fit`
- `follow_up_actions`
- `ai_tools`

Archive fields:

- `is_archived`
- `archived_at`
- `archived_by_user_id`
- `archive_reason`

## Who Can Archive

For the MVP, archive and unarchive operations are admin-only. This is intentional because ownership logic for imported records vs manual records needs more product design before normal users can safely archive their own records.

Normal users can continue to use operational actions such as completing follow-ups. Admins handle cleanup.

## List Behavior

Default behavior excludes archived records.

Admin users can request archived records with:

```text
include_archived=true
```

This applies to:

- Organizations / Startup Library
- Network organizations
- Opportunities
- Events
- Contacts
- Follow-ups
- AI tools

Company detail also hides archived contacts, notes, Borusan fit records, opportunities, and follow-ups by default.

## Archive Endpoints

Organizations:

- `PATCH /api/v1/organizations/{id}/archive`
- `PATCH /api/v1/organizations/{id}/unarchive`

Opportunities:

- `PATCH /api/v1/opportunities/{id}/archive`
- `PATCH /api/v1/opportunities/{id}/unarchive`

Events:

- `PATCH /api/v1/events/{id}/archive`
- `PATCH /api/v1/events/{id}/unarchive`

Contacts:

- `PATCH /api/v1/contacts/{id}/archive`
- `PATCH /api/v1/contacts/{id}/unarchive`

Notes:

- `PATCH /api/v1/notes/{id}/archive`
- `PATCH /api/v1/notes/{id}/unarchive`

Borusan fit:

- `PATCH /api/v1/organizations/{organization_id}/borusan-fit/{fit_id}/archive`
- `PATCH /api/v1/organizations/{organization_id}/borusan-fit/{fit_id}/unarchive`

Follow-ups:

- `PATCH /api/v1/follow-ups/{id}/archive`
- `PATCH /api/v1/follow-ups/{id}/unarchive`

AI tools:

- `PATCH /api/v1/ai-tools/{id}/archive`
- `PATCH /api/v1/ai-tools/{id}/unarchive`

Request body:

```json
{
  "reason": "Mistaken test record"
}
```

## Legacy Delete Endpoints

Existing delete endpoints for contacts, notes, and Borusan fit no longer physically delete data. They archive the record and write an audit log. New UI should prefer archive endpoints directly.

## Leaderboard Reset

Admin-only endpoint:

```text
POST /api/v1/admin/leaderboard/reset
```

Request body:

```json
{
  "scope": "all",
  "user_id": null,
  "reason": "Reset demo/test contribution data",
  "dry_run": true
}
```

Supported scopes:

- `all`
- `user`

Reset behavior:

- Dry run returns the number of contribution records that would be affected.
- Final reset does not delete contribution rows.
- Final reset marks matching manual contribution rows as excluded.
- Leaderboard queries ignore excluded contribution rows.
- CRM records remain intact.

Contribution exclusion fields:

- `is_excluded`
- `excluded_at`
- `excluded_by_user_id`
- `exclusion_reason`

Imported Excel records were already excluded from leaderboard scoring because leaderboard counts only `source=MANUAL`.

## Audit Logging

Audit logs are written for:

- Archive
- Unarchive
- Leaderboard reset final action

Dry-run leaderboard reset is not audit logged because it does not mutate data.

Audit payloads include entity type, entity id, actor, archive state, affected contribution count, and reason where practical.

## Frontend Behavior

Admin UI now includes:

- Archive buttons on Startup Library / Events / Opportunities list rows.
- Admin "show archived" views.
- Archive/unarchive button on Company Detail.
- Archive buttons for contacts, notes, Borusan fit, and follow-ups on Company Detail.
- Archive buttons on Opportunity and Event detail pages.
- Follow-ups archive action.
- Admin Panel link to Leaderboard Management.
- Leaderboard reset dry-run and final confirmation workflow.

Normal users do not see admin cleanup controls.

## Dashboard and Export

Dashboard totals exclude archived organizations, opportunities, events, and follow-ups.

Startup Library CSV export excludes archived records by default. Admins can include archived records when using the admin archived view.

## Testing Steps

1. Run Alembic migration.
2. Login as admin.
3. Archive a test company from Startup Library.
4. Confirm it disappears from normal Startup Library.
5. Enable Show archived and confirm it appears.
6. Unarchive it and confirm it returns to the normal list.
7. Open Company Detail and archive a contact, note, Borusan fit, and follow-up.
8. Confirm those items disappear from Company Detail after refresh.
9. Archive an opportunity and event from their list/detail pages.
10. Confirm dashboard counts exclude archived records.
11. Open Admin Panel > Leaderboard Management.
12. Run dry-run reset for one user.
13. Apply reset and confirm leaderboard points change.
14. Review audit logs for archive and leaderboard reset actions.

## Production Recommendation

Keep archive as the default production cleanup model. Hard delete should require a separate security/data-retention review, strict admin-only access, and careful foreign-key handling.
