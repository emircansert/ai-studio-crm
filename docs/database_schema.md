# Database Schema

Local MVP database target: Microsoft SQL Server. SQLAlchemy maps UUID fields to SQL Server `UNIQUEIDENTIFIER`; JSON fields are stored in SQL Server-compatible JSON text via SQLAlchemy `JSON`; array-like reserved fields use JSON rather than database-specific array types.

SQL Server deletion policy: controlled/reference foreign keys use default `NO ACTION` rather than `SET NULL` or broad cascading. This includes references to statuses, users, tags, Borusan companies, and import row references. The reason is practical as well as architectural: SQL Server rejects some schemas with multiple cascade paths when the same parent table is referenced more than once, such as `organizations.lifecycle_status_id` and `organizations.relationship_status_id` both pointing to `statuses.id`. Database cascades are reserved for strongly owned child rows, such as import batch staging children and event participants.

## Design Principles

- Use English table and column names.
- Do not mirror Excel columns directly.
- Model relationships explicitly.
- Preserve raw import data separately from normalized CRM records.
- Use controlled vocabularies for status, type, category, relationship, relevance, and fit.
- Support fast search and filters.
- Keep room for future AI-generated tags, summaries, duplicate hints, and semantic search.

## Core Tables

### users

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| email | text unique | Lowercase. Holds the Microsoft Entra UPN and is the sole identity key. |
| full_name | text | Display name from the Entra token. |
| role | enum | `ADMIN`, `USER`. Managed in the CRM, not in Entra. |
| is_active | boolean | Inactive users are rejected even with a valid Entra token. |
| last_login_at | datetimeoffset | Refreshed on sign-in (throttled to 15 minutes). |
| created_at / updated_at | datetimeoffset | |

No credential column exists: authentication is Microsoft Entra ID only, and the
`password_hash` column from the original MVP was dropped in migration
`20260726_0020`.

### organizations

Represents startups, vendors, Borusan companies, network institutions, and AI tool vendors where applicable.

This single-table model is intentional for the MVP. All of these records are legal entities or institutional actors with overlapping CRM attributes: name, website/domain, geography, contacts, notes, tags, source, audit history, and relationships. A single `organizations` table avoids duplicate contact/note/search logic and makes cross-links easier.

The trade-off is that product areas must not rely on the table name alone. They must scope records by `organization_type`, optional `organization_subtype`, tags, and relationship tables:

- Company / Startup Library shows `STARTUP` and `VENDOR`.
- Network Library shows `NETWORK_INSTITUTION`.
- Borusan companies are seeded `BORUSAN_COMPANY` records used for matching, permissions, and relationships; they are not shown as startups/vendors.
- AI tool vendors may be linked through `ai_tools.vendor_organization_id`, but tools themselves live in `ai_tools`.

This keeps the data model compact without mixing distinct product experiences.

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| name | text | Required. |
| normalized_name | text | For duplicate matching. |
| organization_type | enum | `STARTUP`, `VENDOR`, `NETWORK_INSTITUTION`, `BORUSAN_COMPANY`, `OTHER`. |
| organization_subtype | text nullable | Examples: `VC`, `CVC`, `ACCELERATOR`, `COMMUNITY`, `PROGRAM`, `AI_TOOL_VENDOR`. Used for UI filters and network/tool-specific distinctions without extra MVP tables. |
| website_url | text | Original URL. |
| website_domain | text | Normalized domain. |
| geography_text | text | Human-readable normalized geography. |
| country_codes | JSON text | Optional later normalization; stores an array of country codes. |
| source_text | text | Source from workbook or manual entry. |
| added_by_text | text nullable | Raw/imported contributor text until user ownership is normalized. |
| solution_summary | text | Clean CRM-facing summary. |
| lifecycle_status_id | uuid FK | Current company status. |
| relationship_status_id | uuid FK nullable | Primarily for network institutions, using `network_relationship` vocabulary. |
| last_contact_date | date nullable | Imported from Startup Library when available. |
| raw_import_ref | uuid nullable | Link to import row where created. |
| ai_summary | text nullable | Reserved for future AI. |
| ai_tags | JSON text | Reserved for future AI; stores an array of tag strings. |
| created_at / updated_at | datetimeoffset | |

Indexes:

- Non-unique index on `website_domain` for import matching. Do not create a unique domain constraint during MVP because duplicate-domain conflicts must be reviewed, not blocked blindly.
- Non-unique index on `normalized_name`.
- SQL Server Full-Text Search can later cover `name`, `solution_summary`, `source_text`, tags, and notes. MVP can begin with indexed filters plus targeted contains queries.
- Composite indexes for common filters: `(organization_type, lifecycle_status_id)`, `(organization_type, geography_text)`, and `(organization_type, source_text)`.

### contacts

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| organization_id | uuid FK | |
| full_name | text nullable | Extracted or manually entered. |
| email | text nullable | Lowercase, validated. |
| phone | text nullable | E.164 preferred where possible. |
| title | text nullable | |
| contact_source | text | `EXCEL`, `MANUAL`, etc. |
| raw_contact_text | text | Preserves original mixed field. |
| created_at / updated_at | datetimeoffset | |

### statuses

Controlled status vocabulary.

Status `code` is unique within a `status_group`, not globally. This allows valid repeated codes such as `UNKNOWN` or `NDA` in different vocabularies while keeping each vocabulary internally unambiguous. Enforce this with a composite unique constraint on `(status_group, code)`.

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| code | text | Example: `INFORMATION_RECEIVED`, `CONTACTED`, `MEETING_HELD`. Unique together with `status_group`. |
| label | text | English display label. |
| status_group | text | `COMPANY`, `OPPORTUNITY`, `EVENT`, etc. |
| sort_order | integer | |
| is_terminal | boolean | |

### organization_status_history

Tracks company status changes.

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| organization_id | uuid FK | |
| status_id | uuid FK | |
| changed_by_user_id | uuid FK nullable | |
| changed_at | datetimeoffset | |
| note | text nullable | |

### borusan_companies

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| code | text unique | `BORCELIK`, `BORU`, `SUPSAN`, `OTO`, `CAT`, `ENERGY`, `PORT`. |
| name | text | English display name. |
| legacy_excel_column | text | Original source column. |
| is_active | boolean | |

### organization_borusan_fit

Replaces the workbook's one-column-per-Borusan-company flags.

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| organization_id | uuid FK | |
| borusan_company_id | uuid FK | |
| fit_level | enum | `RELEVANT`, `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`. |
| fit_reason | text nullable | |
| source | text | `EXCEL_FLAG`, `MANUAL`, future `AI_SUGGESTED`. |
| raw_value | text nullable | Usually `x` from Excel. |

Unique key: `(organization_id, borusan_company_id)`.

### tags

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| code | text unique | |
| label | text | English display label. |
| tag_group | text | `DOMAIN`, `TECHNOLOGY`, `VERTICAL`, `EVENT_CATEGORY`, etc. |

### organization_tags

Many-to-many relationship between organizations and tags.

| Column | Type |
| --- | --- |
| organization_id | uuid FK |
| tag_id | uuid FK |
| source | text |
| confidence | numeric nullable |

### opportunities

Opportunities have one authoritative pipeline field: `stage`.

- `stage` is the operational pipeline position and drives the pipeline UI.
- `status_id` is optional and should be used only for a secondary controlled disposition/detail when a business status is not the same thing as the stage. Examples: `WAITING_FOR_VENDOR`, `LEGAL_REVIEW`, `LOST_PRICE`, `COMPLETED_SUCCESSFULLY`.
- Raw Excel `Son Durum` values map first into `stage`. They should not create both a stage and a duplicate status. If a raw value cannot be mapped to a stage, the row receives an import warning and requires admin decision before commit.

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| title | text | Example: `AI Procurement Agent - Borcelik`. |
| organization_id | uuid FK | Startup/vendor. |
| borusan_company_id | uuid FK | Target Borusan company. |
| opportunity_type | enum | `POC`, `PARTNERSHIP`, `INVESTMENT`, `VENDOR_EVALUATION`, `OTHER`. |
| stage | enum | Required. `IDENTIFIED`, `CONTACTED`, `DISCUSSIONS_ONGOING`, `NDA`, `SCOPING`, `POC_PREPARATION`, `POC_IN_PROGRESS`, `COMPLETED`, `NOT_CONTINUING`, `CANCELLED`, `REJECTED`. Drives the pipeline UI. |
| status_id | uuid FK nullable | Optional secondary status/detail. Not used for the main pipeline board. |
| topic | text | From PoC `Konu`. |
| terms_text | text | From PoC conditions. |
| value_hypothesis | text nullable | |
| expected_start_date | date nullable | |
| expected_end_date | date nullable | |
| last_contact_date | date nullable | |
| owner_user_id | uuid FK nullable | |
| next_action_id | uuid FK nullable | |
| created_at / updated_at | datetimeoffset | |

### events

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| name | text | |
| starts_on | date nullable | Parsed when reliable. |
| ends_on | date nullable | Parsed when reliable. |
| date_text | text | Preserves partial dates such as `Aug 4-6`. |
| location_text | text | |
| geography_text | text nullable | |
| area_text | text nullable | |
| ai_program_relevance | enum | `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`. |
| value_creation_potential | enum | `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`. |
| comments | text nullable | |
| created_at / updated_at | datetimeoffset | |

### event_tags

Many-to-many relationship between events and tags.

### event_participants

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| event_id | uuid FK | |
| participant_role | text | Strategy, Ventures, CDO, Champion, C-Level, Finance. |
| participant_name | text nullable | |
| participant_note | text nullable | |

### ai_tools

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| name | text | |
| vendor_organization_id | uuid FK nullable | |
| category_text | text nullable | |
| solution_summary | text nullable | |
| notes | text nullable | |
| added_by_user_id | uuid FK nullable | |
| created_at / updated_at | datetimeoffset | |

### notes

MVP decision: notes use a controlled polymorphic reference through `entity_type` and `entity_id`.

This is acceptable for the MVP because notes need to attach to several domain objects and the schema is still evolving. The trade-off is that SQL Server cannot enforce a normal foreign key against multiple target tables from one polymorphic pair. The application must validate that `(entity_type, entity_id)` exists before insert/update, and the database should index `(entity_type, entity_id)`.

A minimal alternative for a later hardening phase is to replace this with nullable explicit FKs such as `organization_id`, `opportunity_id`, `event_id`, and `ai_tool_id` plus a check constraint requiring exactly one parent. That improves database enforcement but makes the schema less flexible.

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| entity_type | text | `ORGANIZATION`, `OPPORTUNITY`, `EVENT`, `NETWORK`, `TOOL`. |
| entity_id | uuid | Application-enforced polymorphic reference. |
| note_type | enum | `GENERAL`, `MEETING`, `DECISION`, `IMPORT_NOTE`. |
| body | text | |
| occurred_at | datetimeoffset nullable | Meeting date. |
| created_by_user_id | uuid FK nullable | |
| created_at / updated_at | datetimeoffset | |

### follow_up_actions

Follow-ups use the same MVP polymorphic parent strategy as notes. Application services must enforce parent existence and authorization.

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| entity_type | text | |
| entity_id | uuid | |
| title | text | |
| due_date | date nullable | |
| status | enum | `OPEN`, `DONE`, `CANCELLED`. |
| assigned_to_user_id | uuid FK nullable | |
| created_at / updated_at | datetimeoffset | |

## Import Tables

### import_batches

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| original_filename | text | |
| file_sha256 | text | Duplicate upload detection. |
| uploaded_by_user_id | uuid FK | |
| status | enum | `UPLOADED`, `PROFILED`, `MAPPED`, `PREVIEW_READY`, `COMMITTED`, `REJECTED`, `FAILED`. |
| workbook_metadata | JSON text | Sheet names, row counts, detected headers. |
| created_at / updated_at | datetimeoffset | |

### import_sheets

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| import_batch_id | uuid FK | |
| sheet_name | text | |
| detected_entity | text | `STARTUP_LIBRARY`, `POC`, `EVENTS`, etc. |
| header_row | integer | |
| row_count | integer | |
| column_mapping | JSON text | Applied mapping snapshot. |

### import_rows

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| import_sheet_id | uuid FK | |
| excel_row_number | integer | |
| raw_values | JSON text | Original cell values by column. |
| cleaned_values | JSON text | Trimmed/parsed values. |
| normalized_candidate | JSON text | Candidate CRM object before commit. |
| row_hash | text | Deduplication. |
| validation_status | enum | `VALID`, `WARNING`, `ERROR`, `SKIPPED`. |

### import_warnings

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| import_batch_id | uuid FK nullable | Used for workbook-, sheet-, and batch-level warnings. SQL Server FK uses `NO ACTION`. |
| import_row_id | uuid FK nullable | Used for row-level warnings. Null means the warning applies to the batch or sheet rather than a staged row. |
| severity | enum | `INFO`, `WARNING`, `ERROR`. |
| code | text | Example: `UNKNOWN_STATUS`, `PARTIAL_DATE`, `DUPLICATE_DOMAIN`. |
| message | text | |
| field_name | text nullable | |
| raw_value | text nullable | |

### import_candidates

Generic review layer between staged Excel rows and normalized CRM domain tables.

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| import_batch_id | uuid FK | Owning import batch. Cascade delete with batch. |
| import_row_id | uuid FK nullable | Source staged row when the candidate comes from one row. |
| entity_type | text | `ORGANIZATION`, `CONTACT`, `ORGANIZATION_BORUSAN_FIT`, `OPPORTUNITY`, `EVENT`, `EVENT_PARTICIPANT`, `AI_TOOL`, `NOTE`. |
| action_type | text | `CREATE`, `UPDATE`, `MATCH`, `SKIP`, `NEEDS_REVIEW`. |
| match_entity_type | text nullable | Domain entity type when matched or committed. |
| match_entity_id | uuid nullable | Existing or newly committed domain record id. |
| candidate_data | JSON text | Normalized candidate payload. |
| raw_source | JSON text nullable | Raw staged source values. |
| validation_status | text | `VALID`, `WARNING`, `ERROR`, `NEEDS_REVIEW`. |
| decision_status | text | `PENDING`, `APPROVED`, `REJECTED`, `SKIPPED`. |
| decision_reason | text nullable | Admin decision note. |
| created_at / updated_at | datetimeoffset | |

## Audit and Branding

### audit_logs

Append-only.

| Column | Type |
| --- | --- |
| id | uuid PK |
| actor_user_id | uuid nullable |
| action | text |
| entity_type | text |
| entity_id | uuid nullable |
| before_data | JSON text nullable |
| after_data | JSON text nullable |
| ip_address | string nullable |
| user_agent | text nullable |
| created_at | datetimeoffset |

### branding_assets

| Column | Type | Notes |
| --- | --- | --- |
| id | uuid PK | |
| asset_type | text | `LOGO`. |
| original_filename | text | |
| storage_path | text | Generated safe local path or future blob/object key. Never derived directly from the uploaded filename. |
| content_type | text | |
| file_size_bytes | integer | Enforce upload size limit. |
| file_sha256 | text | |
| is_active | boolean | |
| uploaded_by_user_id | uuid FK | |
| created_at | datetimeoffset | |

Rules:

- Allowed logo content types for MVP: `image/png`, `image/jpeg`, `image/svg+xml`, `image/webp`.
- Maximum file size: 2 MB unless changed by admin configuration.
- Exactly one active logo per environment/tenant. Enforce with a partial unique index on `(asset_type)` where `asset_type = 'LOGO' and is_active = true`.
- Logo replacement must happen in a transaction: insert new asset, deactivate previous active logo, write audit log.
- Storage provider abstraction should allow local volume storage now and Azure Blob/internal object storage later.
