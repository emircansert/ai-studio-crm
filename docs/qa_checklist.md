# QA Checklist

Use this checklist before demos, handover, or larger internal testing.

## Environment

- [ ] SQL Server service is running.
- [ ] Database `BorusanAIEcosystemCRM` exists.
- [ ] ODBC Driver 17 or 18 is installed.
- [ ] `DATABASE_URL` points to the intended database.
- [ ] `JWT_SECRET_KEY` is not the example value.
- [ ] Backend starts without errors.
- [ ] Frontend starts without errors.
- [ ] `/api/v1/health` returns `ok`.
- [ ] `/api/v1/health/readiness` returns database status `ok`.

## Auth / Login / Logout

- [ ] Admin can log in.
- [ ] User can log in.
- [ ] Invalid password fails.
- [ ] Inactive user cannot log in.
- [ ] Logout clears local session.
- [ ] 401/403 clears token and redirects to login.

## Roles and Permissions

- [ ] ADMIN sees Admin Panel, User Management, Branding, Audit Logs.
- [ ] USER does not see admin navigation.
- [ ] USER direct access to `/admin/*` shows access denied.
- [ ] Admin-only API routes reject USER.

## User Management

- [ ] Admin can list users.
- [ ] Admin can search users.
- [ ] Admin can create user with temporary password.
- [ ] Admin can edit full name/email/role/status.
- [ ] Admin can activate/deactivate user.
- [ ] Admin can reset password.
- [ ] System prevents deactivating/downgrading the only active admin.
- [ ] User management actions appear in audit logs.

## Excel Import

- [ ] `.xlsx` upload succeeds.
- [ ] Non-`.xlsx` upload is rejected.
- [ ] Workbook sheets are detected.
- [ ] Row counts and staged counts appear.
- [ ] Unknown/missing mappings produce warnings.
- [ ] Candidate generation succeeds.
- [ ] Needs-review candidates can be approved/rejected/skipped.
- [ ] Commit is blocked when blocking review remains.
- [ ] Commit writes normalized CRM records.
- [ ] Double commit is blocked.
- [ ] Import actions appear in audit logs.

## Startup Library

- [ ] Search works across name/domain/solution/category/vertical/source/added by.
- [ ] Type filter works.
- [ ] Category filter works.
- [ ] Vertical filter works.
- [ ] Borusan company fit filter works.
- [ ] Status filter works.
- [ ] Geography and source filters work.
- [ ] Added date filters work.
- [ ] Has website filter works.
- [ ] Sorting works: newest, oldest, name, last contact.
- [ ] Pagination works across all records.
- [ ] Total count is not capped at 200.
- [ ] CSV export respects practical filters.

## Company Detail

- [ ] Detail page opens from Startup Library.
- [ ] Profile fields display category, vertical, Added By, Added Date, Last Contact.
- [ ] Company edit saves and refreshes.
- [ ] Add contact works.
- [ ] Add note works.
- [ ] Add Borusan fit works.
- [ ] Add opportunity works.
- [ ] Add and complete follow-up works.
- [ ] Manual actions create audit logs and contribution events where intended.

## Opportunities

- [ ] PoC Pipeline list loads.
- [ ] Opportunity detail opens from row click.
- [ ] Stage/status/topic/title edit works.
- [ ] Terms/value/dates/owner edit works.
- [ ] Related follow-up creation/completion works.
- [ ] Updates appear in audit logs.

## Events

- [ ] Events Library list loads.
- [ ] Event detail opens from row click.
- [ ] Event edit works for dates, location, area, relevance, value, comments.
- [ ] Updates appear in audit logs.

## Follow-ups

- [ ] Follow-ups page loads.
- [ ] Create follow-up for organization works.
- [ ] Open/done/cancelled filters work.
- [ ] Overdue styling appears for past open due dates.
- [ ] Complete follow-up works.
- [ ] Completion increments leaderboard contribution points.

## Leaderboard

- [ ] Leaderboard loads.
- [ ] All-time, last 30 days, last 7 days filters work.
- [ ] Metric selector works.
- [ ] Current user card loads.
- [ ] Imported Excel records do not count.
- [ ] Manual organization/contact/note/fit/opportunity/event/follow-up actions count as intended.

## Branding

- [ ] Admin can upload valid image logo.
- [ ] Invalid file type is rejected.
- [ ] Oversized file is rejected.
- [ ] Active logo appears in sidebar.
- [ ] Logo fallback works when no logo exists or endpoint fails.
- [ ] Branding actions appear in audit logs.

## Audit Logs

- [ ] Audit log page loads for ADMIN.
- [ ] USER cannot access audit logs.
- [ ] Filter by action works.
- [ ] Filter by entity type works.
- [ ] Filter by actor id works.
- [ ] Payload expansion works.

## SQL Server Migration

- [ ] `python -m alembic upgrade head` runs cleanly on empty database.
- [ ] `python -m alembic upgrade head` is safe to rerun when already at head.
- [ ] Offline SQL generation works.

## Smoke Test

- [ ] `python scripts\smoke_test_api.py` passes when backend is running.
