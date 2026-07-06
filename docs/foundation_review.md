# Foundation Review

## Scope Reviewed

Reviewed the current foundation across:

- Product requirements
- Architecture
- Database schema
- Excel import pipeline specification
- YAML configs
- FastAPI skeleton
- Next.js skeleton
- Original Docker Compose draft
- Project structure

This review focused only on architectural correctness. It did not implement CRM CRUD, full UI screens, AI features, or backend import execution.

## Critical Issues Found

### Opportunity stage and status semantics were ambiguous

The schema had both `opportunities.stage` and `opportunities.status_id`, but did not define which one drives the pipeline UI or how raw Excel `Son Durum` values map.

Risk: duplicated or contradictory opportunity state, unclear pipeline implementation, and inconsistent filters.

Resolution: fixed. The schema and import spec now define `stage` as the required pipeline-driving field. `status_id` is optional secondary detail only. Excel `Son Durum` maps first to `stage`.

### Import commit decisions were underspecified

The import flow described preview and confirmation, but did not define row-level policies for exact domain matches, duplicate names, duplicate domains, unknown statuses, partial dates, missing website, or contact gaps.

Risk: dirty data could be committed inconsistently or ambiguous records could be auto-merged incorrectly.

Resolution: fixed. The import spec now includes a commit policy table, and `config/import_policy.yml` captures the same decisions in machine-readable form.

## Important Issues Found

### Organization model needed clearer boundaries

The single `organizations` table was directionally correct, but the trade-off and UI scoping rules were not explicit enough.

Risk: startups, vendors, network institutions, and Borusan companies could become mixed in product views and search results.

Resolution: fixed. Architecture and schema now document that the single table is intentional, with separation enforced by `organization_type`, `organization_subtype`, tags, and scoped UI queries.

### YAML mappings referenced fields not clearly present in the schema

The Network mapping used `organizations.network_type` and `organizations.relationship_status`, while the schema did not define those exact fields.

Risk: Backend Phase 1 could implement divergent model names or require avoidable migrations.

Resolution: fixed. The schema now includes `organization_subtype`, `relationship_status_id`, `added_by_text`, and `last_contact_date`. The Network mapping now targets `organization_subtype` and `relationship_status_id`.

### Search strategy was too high-level

The architecture said search would use indexed filters, full-text search, and tags, but did not define concrete fields.

Risk: first backend implementation could miss important filters such as Borusan company fit, stage, status, source, or geography.

Resolution: fixed. Architecture now defines exact organization, opportunity, and event filters, full-text fields, tag filters, fit filters, and the exact query shape for "Find GenAI startups relevant for Borcelik."

### Branding upload requirements needed hardening

The logo feature existed conceptually but lacked upload validation details.

Risk: unsafe file paths, unbounded uploads, multiple active logos, and weak auditability.

Resolution: fixed. Architecture, database schema, and security notes now define allowed file types, 2 MB default limit, generated storage paths, one active logo, transactional replacement, audit logging, and future blob/object storage compatibility.

## Nice-to-Have Issues Found

### Polymorphic notes and follow-ups reduce database-level enforcement

The MVP uses `entity_type` and `entity_id`, which is flexible but cannot enforce true foreign keys to multiple tables.

Decision: keep for MVP. The schema now documents the trade-off and the later minimal alternative: nullable explicit FKs plus a check constraint requiring exactly one parent.

### Controlled vocabulary normalization can become large

Status, relationship, geography, and tag normalization will grow as more workbook variants are found.

Decision: acceptable for Backend Phase 1. Keep YAML-driven mappings and admin vocabulary management as planned.

### Search can start with relational SQL filters but may later need semantic search

The MVP search plan should be enough for exact filtering and keyword search.

Decision: defer vector/AI semantic search. Reserve architectural space only.

## Fixes Applied

- Clarified the single-table organization model and its trade-offs.
- Added `organization_subtype` to avoid overloading tags for core institution subtype distinctions.
- Clarified product/UI separation between startup/vendor, network, Borusan company, and AI tool records.
- Defined `opportunities.stage` as the required pipeline driver.
- Defined `opportunities.status_id` as optional secondary detail only.
- Updated raw Excel `Son Durum` mapping behavior.
- Added concrete import commit policy rules.
- Added `config/import_policy.yml`.
- Added exact search/filter fields and full-text fields.
- Explicitly supported the "GenAI startups relevant for Borcelik" query.
- Documented the polymorphic notes/follow-ups trade-off.
- Hardened admin logo upload/change requirements.
- Aligned config targets with schema names.
- Added `.gitignore` for local secrets, runtime caches, Node build outputs, uploads, and logs.

## Remaining Intentional Trade-Offs

- `organizations` remains a shared table. This is intentional for the MVP to avoid duplicated identity, contacts, notes, search, and audit logic.
- Notes and follow-ups remain polymorphic. This is flexible but application-enforced.
- `website_domain` is not unique in the MVP. Duplicate domains require review because the workbook already has brand/legal-name ambiguity.
- Event dates can preserve partial text instead of forcing parsed dates.
- Missing website and missing contact email are warnings, not blockers, because the workbook contains many incomplete but still valuable records.
- AI-assisted cleanup, duplicate detection, summarization, tagging, and natural language search remain out of scope.

## Readiness Assessment for Backend Phase 1

Ready with conditions.

The foundation is now clear enough for Backend Phase 1 to begin with:

- SQLAlchemy models and first Alembic migration
- Auth and RBAC skeleton
- Controlled vocabulary seed data
- Organization, tag, Borusan fit, opportunity, import staging, audit, and branding tables
- Deterministic import preview logic
- Search/filter query foundations

Before building UI-heavy workflows, Backend Phase 1 should first implement the data model, migrations, seed vocabularies, and import staging/preview contracts exactly as documented.
