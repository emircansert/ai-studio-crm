# YZ Champion Program Productization Phase

## Summary

This phase aligns the CRM with the YZ Champion Program slide while preserving CRM Activity Points. The product now separates:

- use-case/project development work
- ecosystem CRM contribution work
- startup scouting support
- case-study contribution
- event and communication participation
- training completion

## CRM Activity Points Are Preserved As Evidence

CRM Activity Points remain available in the Leaderboard's CRM Activity Points tab, expanded user evidence, admin/debug views, and reset workflows. They continue to represent operational CRM contribution and are not deleted or replaced.

They support the Champion Program by providing evidence of real ecosystem-building work. They are not an official seventh score category and they do not appear as a main column in the official YZ Champion Score table. Many manual CRM actions create both CRM Activity Points and Champion Activity evidence.

Qualifying CRM activities feed **Ecosystem Library Contribution** by activity count:

- `STARTUP_ADDED`
- `VENDOR_ADDED`
- `AI_TOOL_ADDED`
- `EVENT_ADDED`
- `CONTACT_ADDED`
- `DECK_UPLOADED`
- `ORGANIZATION_ENRICHED`

The official category score follows the slide target: 0 contribution = 0, 1-7 contributions = 50, 8+ contributions = 100.

## Final Scores Are Not Manually Entered

Admins do not enter final YZ Champion Scores. Admins record underlying activities such as:

- case study submitted
- case study approved
- event attended
- training completed
- external use case proposed

The system calculates category scores and the final weighted YZ Champion Score automatically.

## Use Case Module

New route: `/use-cases`

Backend table: `use_case_proposals`

Use case fields include:

- title
- description
- Borusan company
- business unit
- proposer
- related startup/organization
- problem area
- proposed solution
- expected impact
- status
- stage
- priority

Creating a use case creates:

- CRM Activity Points via `USE_CASE_CREATED`
- Champion Activity via `USE_CASE_PROPOSED`

Moving a use case to `PROJECTIZED` creates Champion Activity evidence for projectization.

## Events Library

User-facing route: `/events`

There is one event-related surface in the UI: **Events Library**. The former Events & Education page is consolidated into Events Library to avoid parallel event workflows. The internal `/program-activities` API remains available because it stores YZ Champion Program event and training records, and `/program-activities` in the frontend redirects to `/events`.

Backend tables:

- `program_activities`
- `program_activity_participants`

Program activities can be:

- `EVENT`
- `TRAINING`

For events, participant attendance status drives scoring:

- `ATTENDED` creates `EVENT_PARTICIPATION`

For training, participant completion status drives scoring:

- `COMPLETED` creates `TRAINING_COMPLETED`

Imported or previously committed records from the original `events` table are preserved and shown in the same Events Library page as a secondary "Imported ecosystem events" section.

## Slide-To-CRM Mapping

| Slide Area | CRM Product Surface | Scoring Evidence |
| --- | --- | --- |
| Use Case & Project Development | Use Cases, Opportunities | use case proposed, opportunity created, projectized use case |
| Ecosystem Library Contribution | Startup Library, Events Library, AI Tools, Contacts, Deck Uploads | qualifying CRM actions counted from ecosystem additions and enrichments |
| Startup Scouting & AI Studio Support | Follow-ups, Champion Program admin evidence | completed follow-ups, startup reviewed, startup shortlisted |
| Case Study Contribution | Admin Champion Program | case study submitted/approved |
| Events & Communication Participation | Events Library | attended program event |
| Training Completion | Events Library | completed training |

## Known Limitations

- Event and training participant updates currently create positive evidence when a participant is marked attended/completed. A future phase can add explicit revocation if attendance/completion is later reversed.
- Borusan Academy integration is not implemented; training is admin-recorded.
- Teams or communication workflow integration is not implemented; case studies and event roles are admin-recorded.

## Testing Checklist

- `GET /api/v1/leaderboard/champion`
- `GET /api/v1/leaderboard/champion/rules`
- `GET /api/v1/use-cases`
- `POST /api/v1/use-cases`
- `GET /api/v1/program-activities`
- `POST /api/v1/program-activities`
- `POST /api/v1/program-activities/{id}/participants`
- `/events` is the single Events Library UI for events, communication activities, and training programs
- `/program-activities` redirects to `/events`
- `/leaderboard` main YZ Champion table shows the six official slide categories only
- `/leaderboard` CRM Activity Points tab/detail evidence still shows operational CRM points
- `/use-cases` creates use-case evidence
- `/events` records event/training participation evidence
