# Leaderboard Contribution Tracking

## Purpose

The leaderboard ranks Borusan AI Ecosystem CRM users by manual CRM contributions. It is intentionally separate from audit logs.

- Audit logs record accountability and traceability.
- User contributions record scoring events for adoption and recognition.

## What Counts

Only `user_contributions.source = MANUAL` counts by default.

Current contribution types and points:

- `ORGANIZATION_CREATED`: 10 points
- `OPPORTUNITY_CREATED`: 8 points
- `EVENT_CREATED`: 5 points
- `CONTACT_CREATED`: 3 points
- `BORUSAN_FIT_CREATED`: 3 points
- `NOTE_CREATED`: 2 points
- `ORGANIZATION_UPDATED`: 1 point

Manual API actions currently write contribution rows for:

- organization created
- organization updated
- contact created
- note created
- Borusan company fit created
- opportunity created
- event created

## What Does Not Count

The following are excluded from leaderboard scoring:

- imported Excel records
- import candidates
- import commit operations
- system-generated records
- automatic duplicate/match updates
- audit log entries by themselves

Imported Excel `Added By` values remain attribution metadata in the CRM, but they do not become leaderboard points unless a future explicit mapping workflow maps them to real CRM users.

## Data Model

The `user_contributions` table stores:

- `user_id`
- `contribution_type`
- `entity_type`
- `entity_id`
- `points`
- `source`
- `occurred_at`
- `metadata_json`
- `created_at`

Accepted source values are:

- `MANUAL`
- `IMPORT`
- `SYSTEM`

Only `MANUAL` is used by the current leaderboard queries.

## Endpoints

### `GET /api/v1/leaderboard`

Query params:

- `period`: `all_time`, `last_30_days`, `last_7_days`
- `metric`: `points`, `organizations`, `notes`, `contacts`, `opportunities`
- `limit`: default `20`

Returns ranked users with:

- rank
- user ID, full name, email
- total points
- contribution breakdown
- last contribution timestamp

### `GET /api/v1/leaderboard/me`

Returns the current authenticated user's rank and contribution breakdown for the selected period and metric.

## Frontend Behavior

The Leaderboard page shows:

- top three highlighted cards
- ranked table
- period selector
- metric selector
- current user contribution card
- reminder that imported Excel records are excluded

The dashboard shows a small leaderboard pulse with top contributor and current user rank for the last 30 days.

## Future Improvements

- Add follow-up completion endpoint and score `FOLLOW_UP_COMPLETED`.
- Add contribution deduplication rules for repeated edits within a short time window.
- Add admin configuration for points.
- Add explicit imported-user mapping if Borusan wants historical Excel `Added By` values to count.
- Add richer team-level and company-level leaderboard views.
