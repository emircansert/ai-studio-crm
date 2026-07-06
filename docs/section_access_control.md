# Sidebar Section Access Control

## Model Decision

The MVP uses per-user section access because the existing User Management model has only coarse `ADMIN` and `USER` roles. This keeps the implementation conservative and easy for admins to manage without introducing a full role/permission hierarchy.

Roles still apply:
- `ADMIN` is required for User Management, Admin Branding, Audit Logs, Diagnostics, and other admin-only operations.
- Section access adds a second layer for controlled sidebar sections.
- User Management itself is not controlled by the matrix so active admins can recover access.

## Access Levels

- `HIDDEN`: the section is hidden in the sidebar and matching API endpoints are blocked.
- `VIEW`: the section is visible and read endpoints are allowed; create/edit/archive/upload/delete API actions are blocked.
- `FULL`: read and mutating API actions are allowed.

Safe defaults:
- New `USER` accounts default to `HIDDEN` for every controlled section.
- New `ADMIN` accounts default to `FULL` for every controlled section.
- Existing users without explicit rows use the same role-aware fallback.

## Controlled Sections

- Startup Library
- Use Cases
- PoC Pipeline
- Events Library
- AI Tools Library
- Network Library
- Vendor Library, reserved for future routes
- Follow-ups
- Leaderboard
- Champion Program, still admin-only
- Admin Overview, frontend route only
- Leaderboard Admin, still admin-only

## Backend Enforcement

The backend has a central request guard that maps API prefixes to section keys:

- `STARTUP_LIBRARY`: `/api/v1/organizations`, `/api/v1/contacts`, `/api/v1/notes`
- `USE_CASES`: `/api/v1/use-cases`
- `POC_PIPELINE`: `/api/v1/opportunities`
- `EVENTS_LIBRARY`: `/api/v1/events`, `/api/v1/program-activities`
- `AI_TOOLS_LIBRARY`: `/api/v1/ai-tools`
- `NETWORK_LIBRARY`: `/api/v1/network`
- `FOLLOW_UPS`: `/api/v1/follow-ups`
- `LEADERBOARD`: `/api/v1/leaderboard`
- `CHAMPION_PROGRAM`: `/api/v1/admin/champion-activities`
- `LEADERBOARD_ADMIN`: `/api/v1/admin/leaderboard`

`GET`, `HEAD`, and `OPTIONS` are treated as read-level actions. Other HTTP methods require `FULL`.

## Known Caveat

Frontend hiding and the direct-route access-denied page are implemented. Some individual page buttons may still appear for a `VIEW` user, but the backend blocks the mutating API call with `SECTION_ACCESS_DENIED`. Backend enforcement is the security boundary.

`ADMIN_OVERVIEW` is currently frontend-only because there is no dedicated admin overview API. Admin-specific APIs such as User Management, Branding, Audit Logs, and Diagnostics remain role-gated separately.

## Manual Regression Checklist

1. Create a test `USER`.
2. Confirm the user defaults to no controlled sidebar sections.
3. Grant `VIEW` for Startup Library only.
4. Log in as the user and confirm only Startup Library plus non-controlled areas are visible.
5. Directly open `/companies`; confirm the page loads.
6. Directly open `/use-cases`; confirm access denied.
7. With the same token, call `GET /api/v1/organizations?limit=1`; expect `200`.
8. With the same token, call `POST /api/v1/organizations`; expect `403 SECTION_ACCESS_DENIED`.
9. Change Startup Library to `FULL`.
10. Repeat `POST /api/v1/organizations` with valid payload; expect normal endpoint validation or success, not section access denial.
11. Grant `VIEW` for Leaderboard and confirm `GET /api/v1/leaderboard` works.
12. Confirm `POST /api/v1/admin/leaderboard/reset` is blocked unless the user is also `ADMIN` and has `FULL` Leaderboard Admin.
13. Confirm User Management remains hidden and blocked for all non-admin users regardless of matrix values.
