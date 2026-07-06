# YZ Champion Score Leaderboard Phase

## Purpose

The main leaderboard follows the YZ Champion Program scorecard from the manager slide. The official score is the weighted **YZ Champion Score** calculated from exactly six slide-defined categories.

CRM Activity Points are not removed or replaced. They remain the internal operational evidence trail for hands-on CRM work such as adding startups, vendors, events, tools, contacts, decks, opportunities, and completing follow-ups. They are shown in the CRM Activity Points tab and user detail evidence, not as a separate official column in the main YZ Champion Score table.

## Score Relationship

The system now has one official score and one supporting evidence log:

- **YZ Champion Score**: official weighted 0-100 score calculated from category thresholds and weights.
- **CRM Activity Points**: internal operational point total from manual CRM contributions.

CRM Activity Points are not a seventh weighted category and are not summed into the final YZ Champion Score. Instead, many manual CRM actions create both:

- `user_contributions` for CRM Activity Points
- `champion_activities` for official category count and target scoring

Excel imports do not create either score unless explicitly converted in a future mapped backfill.

For the official leaderboard, qualifying CRM actions feed **Ecosystem Library Contribution** by count, then the slide threshold is applied:

- 0 qualifying ecosystem contribution = 0 category score
- 1-7 qualifying ecosystem contributions = 50 category score
- 8+ qualifying ecosystem contributions = 100 category score

The weighted contribution is then `Ecosystem Library category score * 15%`.

## Scorecard Areas

1. **Use Case & Project Development**
   - Helper: Use-case Önerisi ve Projelendirme
   - Weight: 40%
   - Target: 0 project = 0, 1 project = 50, 2+ projects = 100

2. **Ecosystem Library Contribution**
   - Weight: 15%
   - Target: 0 contribution = 0, 1-7 contributions = 50, 8+ contributions = 100
   - Evidence: qualifying CRM actions such as adding startups, vendors, events, AI tools, contacts, startup decks, and library enrichments

3. **Startup Scouting & AI Studio Support**
   - Weight: 15%
   - Target: 0 scouting = 0, 1-4 scouting = 50, 5+ scouting = 100

4. **Case Study Contribution**
   - Weight: 10%
   - Target: 0 case study = 0, 1 case study = 50, 2+ case studies = 100

5. **Events & Communication Participation**
   - Weight: 10%
   - Target: 0-1 event = 0, 2-4 events = 50, 5+ events = 100

6. **Training Completion**
   - Weight: 10%
   - Target: incomplete/missing = 0, complete = 100

## Automatic CRM Mapping

Manual CRM actions create Champion Activities where relevant. These are count-based evidence for the six official YZ Champion categories:

- Manual opportunity created -> Use Case & Project Development / `OPPORTUNITY_CREATED`
- Manual use case proposal created -> Use Case & Project Development / `USE_CASE_PROPOSED`
- Use case moved to `PROJECTIZED` -> Use Case & Project Development / `USE_CASE_PROJECTIZED`
- Manual organization/startup/vendor created -> Ecosystem Library Contribution / `STARTUP_ADDED` or `VENDOR_ADDED`
- Manual AI tool created -> Ecosystem Library Contribution / `AI_TOOL_ADDED`
- Manual event created -> Ecosystem Library Contribution / `EVENT_ADDED`
- Manual contact added -> Ecosystem Library Contribution / `CONTACT_ADDED`
- Startup deck uploaded -> Ecosystem Library Contribution / `DECK_UPLOADED`
- Library record enriched -> Ecosystem Library Contribution / `ORGANIZATION_ENRICHED`
- Follow-up completed -> Startup Scouting & AI Studio Support / `FOLLOW_UP_COMPLETED`

## Admin-Recorded Activities

Admins record underlying activities, not final scores.

Admin-recorded activities include:

- case study submitted/approved
- event participation
- training completed
- external use case proposal
- startup review/shortlist

The system calculates category scores automatically from activity counts.

## Endpoints

- `GET /api/v1/leaderboard/champion`
- `GET /api/v1/leaderboard/champion/me`
- `GET /api/v1/leaderboard/champion/users/{user_id}`
- `GET /api/v1/leaderboard/champion/rules`
- `GET /api/v1/leaderboard` for CRM Activity Points
- `GET /api/v1/use-cases`
- `POST /api/v1/use-cases`
- `GET /api/v1/program-activities`
- `POST /api/v1/program-activities`
- `POST /api/v1/program-activities/{id}/participants`
- `GET /api/v1/admin/champion-activities`

The user-facing Events Library is `/events`. It contains program activities for event participation and training completion, while preserving imported ecosystem event records in the same page.

## Reset / Exclusion

CRM Activity Points reset remains scoped to `user_contributions`. Champion activity evidence is preserved and can be archived/unarchived through Champion Program admin workflows. Resetting CRM Activity Points does not directly edit final YZ Champion Scores; official scores are recalculated from non-archived Champion Activities.

## Testing

1. Create a manual use case and confirm the Champion Score Use Case & Project Development category increases.
2. Confirm CRM Activity Points are preserved in the CRM Activity Points tab or expanded user evidence, not as a main YZ Champion table column.
3. Move a use case to `PROJECTIZED` and confirm a projectization Champion Activity is created.
4. Create an event or training in Events & Education Programs.
5. Add a participant with `ATTENDED` or `COMPLETED`.
6. Confirm qualifying CRM actions increase Ecosystem Library Contribution by count, not by summing raw CRM points.
7. Confirm the relevant category changes in the Leaderboard.
8. Confirm Score Rules tab shows slide-aligned area/task/KPI/target/weight/tracking owner columns.
