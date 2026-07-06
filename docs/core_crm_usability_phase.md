# Core CRM Usability Phase

## Implemented capabilities

This phase turns the imported ecosystem data into a usable CRM MVP while preserving the normalized architecture.

- Enriched organization list API with search, filters, status labels, Borusan fit summaries, tags, and activity counts.
- Full organization detail API including contacts, notes, opportunities, Borusan fit, tags, source metadata, and contribution tracking fields.
- Manual organization create/update with normalized name and website domain derivation.
- Nested contacts, notes, and Borusan company fit management under organizations.
- Basic opportunity and event create/update endpoints with audit logging.
- Dashboard summary endpoint for core CRM counts and latest import status.
- Admin logo upload endpoint with file validation, safe local storage, one active logo, and audit logging.

## Manual data entry behavior

Manual CRM records are written directly into normalized domain tables, not import staging tables. Manual organization, contact, event, and opportunity actions record the current user where the model supports it. Imported Excel records remain distinct because they preserve raw import references and are not counted as manual user contributions unless later mapped to real CRM users.

## Search and filtering

`GET /api/v1/organizations` supports practical CRM filters:

- `q`: searches name, normalized name, website, domain, solution summary, source, and tags.
- `organization_type`: separates startups, vendors, network institutions, Borusan companies, and tool vendors.
- `borusan_company_code`: filters by Borusan fit, for example `BORCELIK`.
- `status_code`: filters lifecycle status.
- `geography`, `source`, `tag`, `has_website`.

The use case “Find GenAI startups relevant for Borcelik” is supported by combining `q=GenAI`, `organization_type=STARTUP`, and `borusan_company_code=BORCELIK`.

## Known limitations

- Organization detail uses polymorphic notes as intentionally documented for the MVP.
- Tags are displayed and searched but not yet fully editable in the UI.
- Contact and note editing/deletion endpoints exist, but the first detail UI focuses on add/list workflows.
- Opportunity/event pages provide basic manual creation and list views, not full board/calendar workflows.
- Leaderboard scoring is intentionally not implemented; the frontend states that it activates after contribution tracking is complete.

## Next recommendations

- Add detail pages for opportunities and events.
- Add controlled tag editing and richer filter presets.
- Add saved views for common searches such as GenAI + Borcelik.
- Add frontend tests around import flow and CRM detail mutations.
