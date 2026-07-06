# Startup Library Data Completeness Phase

## Category Behavior

Category is now an explicit organization field:

- `organizations.category_code`
- `organizations.category_label`

The frontend treats Category as a controlled dropdown. The options come from `GET /api/v1/vocabularies/categories`, which combines committed `CATEGORY` tags and distinct organization category fields. This keeps the MVP simple and reuses the existing vocabulary/tag foundation instead of adding a separate category table too early.

## Vertical Behavior

Vertical is now an explicit free-text organization field:

- `organizations.vertical_text`

This reflects the current Excel behavior, where Vertical contains meaningful but not always controlled values. It is searchable, filterable, visible in the Startup Library table, and editable on the Company Detail page.

## Added By And Added Date

The CRM now distinguishes imported attribution from real CRM user attribution.

Imported attribution:

- Excel `Added By` maps to `organizations.added_by_text`.
- Imported records do not automatically count as manual CRM contributions.
- If the workbook does not contain an explicit added date, the CRM does not invent one.

Manual CRM attribution:

- Manual creates set `organizations.created_by_user_id` to the current authenticated user.
- Manual updates set `organizations.updated_by_user_id`.
- `created_at` is the CRM added date for both imported and manual records.

Display behavior:

- `added_by_display` prefers the real CRM user full name from `created_by_user_id`.
- If there is no real CRM user, it falls back to imported `added_by_text`.
- `added_at` is currently `created_at`.

## Import Mapping

Startup Library import candidate generation now maps:

- `Category` -> `category_code`, `category_label`, and existing `CATEGORY` tag
- `Vertical` -> `vertical_text` and existing `VERTICAL` tag
- `Added By` -> `added_by_text`
- `Last Contact` -> `last_contact_date`

`Last Contact` is intentionally not used as Added Date.

## Re-import / Backfill Note

New imports will populate category and vertical directly.

For existing committed local data, run the backfill script after applying the migration:

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\python.exe scripts\backfill_org_category_vertical.py
```

The script derives category and vertical from existing `CATEGORY` and `VERTICAL` tags created by earlier import commits. If records were committed before tags existed or if the original candidate data did not contain those values, re-importing and committing the workbook is the cleanest local MVP repair path.

## Pagination And Sorting

`GET /api/v1/organizations` now returns a paginated response:

- `items`
- `total_count`
- `limit`
- `offset`
- `sort_by`

Supported sorting:

- `newest`
- `oldest`
- `name_asc`
- `last_contact_desc`

The frontend supports page sizes of 50, 100, and 200 with next/previous controls.

## Leaderboard Readiness

No leaderboard scoring was implemented in this phase.

The data is now better prepared for future scoring:

- Manual organization creation has `created_by_user_id`.
- Manual organization updates have `updated_by_user_id`.
- Notes already preserve `created_by_user_id`.
- Imported Excel attribution remains separate in `added_by_text`.

Future leaderboard logic should count real CRM user IDs only, not raw imported Excel names, unless an explicit mapping workflow is added.

## Testing Steps

1. Run `alembic upgrade head`.
2. Run `python scripts\backfill_org_category_vertical.py` if existing imported records need category/vertical repair.
3. Start the backend and frontend.
4. Open Startup Library.
5. Confirm Category, Vertical, Added By, Added Date, Last Contact, and pagination are visible.
6. Test filters for Category, Vertical, Added By, date range, and sorting.
7. Open a company detail page and edit Category, Vertical, Source, and Last Contact.
