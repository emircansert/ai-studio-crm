# Excel Import Phase 2

Excel Import Phase 2 adds a reviewable candidate layer and a guarded commit flow. Staged Excel rows remain the source of truth; normalized CRM records are created only from approved candidates.

## Candidate Generation

Endpoint:

```text
POST /api/v1/imports/{batch_id}/candidates/generate
```

Generation is idempotent. If candidates already exist for a batch, the endpoint returns the existing candidate preview instead of creating duplicates.

Generated candidate entity types:

- `ORGANIZATION`
- `CONTACT`
- `ORGANIZATION_BORUSAN_FIT`
- `OPPORTUNITY`
- `EVENT`
- `EVENT_PARTICIPANT`
- `AI_TOOL`
- `NOTE`

Candidate decisions:

- `VALID` candidates default to `APPROVED`.
- `NEEDS_REVIEW` and `ERROR` candidates default to `PENDING`.
- `ERROR` candidates cannot be approved.

## Normalization Logic

Startup Library rows create organization candidates with:

- startup name and normalized name
- website URL and website domain
- lifecycle status mapping
- category and vertical tags
- geography, source, added by, last contact, solution summary
- contact candidate from `Kontak Kişisi`
- note candidate from `Notlar / Yorumlar`
- Borusan company fit candidates from Boru, Borcelik, Supsan, Oto, CAT, Energy, and Port columns

PoC rows create opportunity candidates with:

- startup linked to a Startup Library candidate when possible
- existing organization match by normalized name when possible
- minimal startup organization candidate when no match exists
- Borusan company mapping
- topic/title, stage, terms, notes, last contact date

Event rows create event candidates with:

- event name
- reliable ISO date as `starts_on`, otherwise preserved as `date_text`
- location and derived geography text
- relevance and value creation ratings
- tags from area/category
- participant candidate when participant fields exist

Network rows create network institution organization candidates with:

- organization type `NETWORK_INSTITUTION`
- subtype, expertise tags, geography, relationship status
- contact and note candidates

AI tool rows create `AI_TOOL` candidates only when rows contain a tool name.

## Duplicate and Match Handling

The implementation follows `config/import_policy.yml` conservatively:

- exact website domain match to one existing organization: `MATCH`
- exact normalized name match with enough confidence: `MATCH`
- duplicate domain with different names: `NEEDS_REVIEW`
- duplicate name with missing website: `NEEDS_REVIEW`
- PoC startup matching Startup Library candidate: link to that candidate
- network institution same name as existing non-network organization: `NEEDS_REVIEW`

Risky duplicates are not silently merged.

## Candidate Preview

Endpoint:

```text
GET /api/v1/imports/{batch_id}/candidates
```

Returns:

- candidate counts by entity type
- action counts
- validation counts
- decision counts
- candidates grouped by entity type
- needs review list
- duplicate/match summary
- candidate warnings
- `can_commit`

## Decisions

Endpoint:

```text
PATCH /api/v1/imports/candidates/{candidate_id}/decision
```

Body:

```json
{
  "decision_status": "APPROVED",
  "decision_reason": "Reviewed in Import Center"
}
```

Allowed statuses:

- `APPROVED`
- `REJECTED`
- `SKIPPED`

## Commit

Endpoint:

```text
POST /api/v1/imports/{batch_id}/commit
```

Commit rules:

- blocks double commit
- requires generated candidates
- blocks unresolved `PENDING` candidates with `NEEDS_REVIEW` or `ERROR`
- commits only `APPROVED` candidates
- skips `PENDING`, `REJECTED`, `SKIPPED`, and unapproved `ERROR` candidates
- uses one database transaction
- rolls back on failure
- writes audit logs
- marks the batch `COMMITTED` on success

Committed domain tables:

- `organizations`
- `contacts`
- `organization_borusan_fit`
- `opportunities`
- `events`
- `event_participants`
- `notes`
- `tags`
- `organization_tags`
- `event_tags`
- `ai_tools`

## Frontend Flow

The Import Center now supports:

1. Upload workbook.
2. Review staging preview.
3. Generate candidates.
4. Review candidate counts and needs-review items.
5. Approve, skip, or reject candidates.
6. Commit approved candidates.
7. Navigate to basic Company, Events, Network, or PoC list pages.

## Known Limitations

- Candidate review is minimal; it does not yet support editing candidate fields or manually choosing a match target.
- Date parsing remains conservative. Ambiguous event dates are preserved as text.
- Existing-record update behavior is intentionally limited; most approved candidates create records or match existing organizations.
- Relationship cleanup is not attempted on rejected/skipped parent candidates.
- AI tagging, summarization, semantic duplicate detection, and natural-language search remain out of scope.

## Testing Steps

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Then from the frontend:

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\frontend
npm install
npm run dev
```

In the browser:

1. Login as admin.
2. Open Import Center.
3. Upload `Ekosistem_Library_V2.xlsx`.
4. Generate candidates.
5. Resolve needs-review items.
6. Commit.
7. Check Startup Library, Events Library, Network Library, and PoC Pipeline.
