# Excel Import Pipeline Specification

## Goals

- Accept workbook upload.
- Detect known sheets.
- Apply YAML-driven sheet and column mappings.
- Preserve raw workbook values.
- Clean and normalize fields for CRM usage.
- Detect invalid values, partial dates, duplicate companies, duplicate domains, and malformed contacts.
- Present a preview before committing.
- Commit normalized records only after admin confirmation.

## Non-Goals

- No AI-assisted cleanup in the first stage.
- No direct Excel-to-domain-table write.
- No silent correction of ambiguous values.

## Pipeline Stages

### 1. Upload

Input: `.xlsx` workbook.

Actions:

- Store file metadata.
- Calculate SHA-256.
- Create `import_batches` row.
- Reject unsupported file types.
- Warn on repeated file hash.

### 2. Workbook Profile

Actions:

- Detect sheets and dimensions.
- Detect header row per sheet.
- Capture first rows for preview.
- Create `import_sheets` rows.

Known sheet mappings:

- `Startup Library` -> `STARTUP_LIBRARY`
- `PoC` -> `POC_OPPORTUNITIES`
- `Events` -> `EVENTS`
- `Network` -> `NETWORK`
- `AI Tools` -> `AI_TOOLS`
- `Lists` -> `CONTROLLED_LISTS`

### 3. Column Mapping

Actions:

- Apply `config/column_mapping.yml`.
- Apply `config/import_policy.yml` for match, warning, hold, skip, and create-new behavior.
- Flag unmapped required fields.
- Preserve unmapped columns in raw row JSON.
- Support Turkish and English source headers.

### 4. Raw Row Staging

Actions:

- Write every non-empty source row into `import_rows`.
- Store `raw_values`.
- Store source sheet and Excel row number.
- Skip known non-record tail rows, such as the PoC status values in column I, but preserve them as batch warnings or list candidates.

### 5. Cleaning

Cleaning rules:

- Trim whitespace and non-breaking spaces.
- Normalize empty placeholders: `-`, `?`, `N/A`, blank.
- Normalize URLs and extract domains.
- Parse Excel dates and supported date strings.
- Preserve partial dates in `date_text` if exact date cannot be trusted.
- Extract email addresses from mixed contact fields.
- Extract phone-like values into raw phone candidates.
- Split multi-value categories/tags by comma, slash, ampersand, and known separators when confidence is high.
- Normalize Turkish/English geography aliases.

### 6. Status Normalization

Use `config/status_mapping.yml`.

Examples:

- `Bilgi` -> `INFORMATION_RECEIVED`
- `Gorusuldu` -> `MEETING_HELD`
- `Komite olarak gorusuldu` -> `COMMITTEE_REVIEWED`
- `Calisiliyor` -> `IN_PROGRESS`
- `Demo Asamasinda` -> `DEMO_IN_PROGRESS`
- `PoC devam ediyor` -> `POC_IN_PROGRESS`
- `Devam etmiyor` -> `NOT_CONTINUING`

For PoC rows, `Son Durum` maps to `opportunities.stage`, which is the pipeline-driving field. It should not also create a duplicate opportunity `status_id`. `status_id` is reserved for secondary disposition/detail values that are not pipeline stages.

Unknown statuses create warnings and the affected row requires an admin decision before commit. The admin can map the value to an existing stage/status, create a controlled vocabulary value if appropriate, or skip the row.

### 7. Candidate Generation

Candidate objects:

- Organizations from Startup Library and Network.
- Contacts from contact fields.
- Organization tags from verticals, categories, solution text, and event categories.
- Borusan fit records from company flag columns.
- Opportunities from PoC rows.
- Events from Events rows.
- AI tools from AI Tools rows if future rows exist.

### 8. Duplicate Detection

MVP deterministic checks:

- Exact normalized organization name.
- Exact website domain.
- Email reuse across contacts.
- Same opportunity organization + Borusan company + topic.

Known workbook duplicate candidates:

- Artiwise appears twice by normalized name.
- Jetlink appears twice by normalized name.
- OneNewOne appears twice by normalized name and domain.
- AlternaCX / Alterna CX share `alternacx.com`.

Future AI-assisted duplicate detection can score fuzzy similarities but should not auto-merge.

### 8.1 Import Commit Policy

The import preview must classify each candidate row with one commit action. Admin confirmation is still required for the batch, but some rows can be pre-classified as safe auto-matches while ambiguous rows require row-level decisions.

| Case | Default action | Warning | Admin decision required | Notes |
| --- | --- | --- | --- | --- |
| Exact website domain match to one existing organization of compatible type | Auto-match existing record | `DOMAIN_MATCHED` info | No | Compatible means startup/vendor to startup/vendor, network to network, or tool vendor to vendor/other. Do not overwrite high-quality existing fields with blanks. |
| Exact normalized name match and no domain conflict | Auto-match existing record | `NAME_MATCHED` info | No, unless multiple matches exist | Use when domain is blank or same. Preserve raw import reference. |
| Duplicate normalized name but candidate has missing domain | Match only if there is exactly one compatible existing record; otherwise hold | `DUPLICATE_NAME_MISSING_DOMAIN` warning | Yes when multiple or incompatible matches exist | Prevents merging unrelated companies with common or ambiguous names. |
| Duplicate domain with different names | Hold for review | `DUPLICATE_DOMAIN_DIFFERENT_NAME` warning | Yes | Example: legal name vs brand may be valid, but auto-merge is risky. |
| PoC row references an existing startup by exact domain or exact normalized name | Auto-link opportunity to existing organization | `POC_LINKED_TO_EXISTING_ORGANIZATION` info | No when match is unique | If no unique match exists, hold the opportunity row for admin organization selection/creation. |
| PoC row references a startup not found in Startup Library or existing CRM | Create new minimal startup candidate | `POC_ORGANIZATION_CREATED_FROM_REFERENCE` warning | Yes | Admin should confirm because PoC sheet has less company profile data. |
| Network institution has same normalized name as an existing network institution | Auto-match | `NETWORK_NAME_MATCHED` info | No when unique | Update network-specific subtype/tags only where policy allows. |
| Network institution has same normalized name as an existing startup/vendor/Borusan company | Create warning and hold | `NETWORK_NAME_CONFLICT` warning | Yes | The same name may represent a fund, startup, or internal company; product areas must remain separate. |
| Unknown status value | Hold affected row | `UNKNOWN_STATUS` error | Yes | Admin must map, create vocabulary, or skip. |
| Partial date parsing, such as `Aug 4-6`, `Nov`, or `Her ay` | Preserve text, commit nullable parsed dates | `PARTIAL_DATE` warning | No for events; Yes for opportunity date if operationally required | Events can rely on `date_text`. Opportunity `last_contact_date` should be exact when used for follow-ups. |
| Failed date parsing with non-empty value | Preserve raw value; set parsed date null | `DATE_PARSE_FAILED` warning/error by field | Yes for opportunity dates, No for low-impact event date text | Do not guess dates. |
| Missing website | Create or match by unique normalized name | `MISSING_WEBSITE` warning | No if unique name match; Yes if new organization or duplicate name | Missing website is common in the workbook but weakens duplicate detection. |
| Missing contact email | Commit organization/contact raw text if other required fields pass | `CONTACT_WITHOUT_EMAIL` warning | No | Contact email is valuable but not required for an organization record. |
| Missing required organization name | Skip row | `MISSING_REQUIRED_NAME` error | No, unless admin edits preview in a future UI | Cannot create normalized organization without a name. |
| Missing Borusan company in PoC row | Hold row | `UNKNOWN_BORUSAN_COMPANY` error | Yes | Opportunity requires a target Borusan company. |

Commit behavior:

- `auto-match`: use the matched record and apply non-destructive updates according to field-level policy.
- `create new record`: create only after batch confirmation.
- `require admin decision`: keep staged row out of domain tables until resolved.
- `skip`: keep raw row and warning in import staging; write no domain record.

### 9. Validation Warnings

Warning examples:

- `UNKNOWN_STATUS`
- `MISSING_REQUIRED_NAME`
- `MISSING_WEBSITE`
- `MALFORMED_URL`
- `PARTIAL_DATE`
- `DATE_PARSE_FAILED`
- `CONTACT_WITHOUT_EMAIL`
- `DUPLICATE_NAME`
- `DUPLICATE_DOMAIN`
- `UNKNOWN_BORUSAN_COMPANY`
- `EMPTY_CONTROLLED_CATEGORY`
- `SKIPPED_NON_RECORD_ROW`

Warnings do not always block import. Errors do.

### 10. Import Preview

Preview must show:

- Record counts by entity type.
- New vs matched existing records.
- Validation warnings by severity.
- Duplicate candidates.
- Status mappings used.
- Rows skipped with reason.
- Sample normalized records with raw source references.
- Proposed commit action for each row: `AUTO_MATCH`, `CREATE_NEW`, `REQUIRES_DECISION`, or `SKIP`.

### 11. Confirmation Commit

Only admins can commit.

On confirmation:

- Use a database transaction.
- Upsert matched records where policy allows.
- Insert status history.
- Insert import references.
- Insert audit log entries.
- Mark batch as `COMMITTED`.

On rejection:

- Keep staging data.
- Mark batch as `REJECTED`.
- No CRM domain table writes.

## Sheet-Specific Transformation

### Startup Library

Source columns become:

- `Startup` -> `organizations.name`
- `Website` -> `organizations.website_url` and `website_domain`
- `Status` -> `organizations.lifecycle_status_id`
- `Vertical`, `Category`, `Solution / Use-case` -> tags and solution summary
- `Cografya` -> normalized geography fields
- `Kontak Kisisi` -> contacts
- `Notlar / Yorumlar` -> notes
- `Kaynak` -> source text
- Borusan company columns -> `organization_borusan_fit`

### PoC

Source columns become:

- `Sirket` -> Borusan company mapping.
- `Startup` -> linked organization by name/domain if possible.
- `Konu` -> opportunity topic/title.
- `Son Durum` -> `opportunities.stage`, the pipeline-driving field.
- `POC Sartlari` -> terms text.
- `Notlar` -> opportunity note.
- `Son Gorusme` -> last contact date, with parsing warnings for strings.

### Events

Source columns become:

- `Etkinlik Adi` -> event name.
- `Date` -> parsed start/end date when possible plus preserved date text.
- `Alan` and `Kategori` -> event tags.
- `Lokasyon` -> location text.
- `AI Program Relevance` -> relevance enum.
- `Deger yaratma Opsiyonu` -> value creation enum.
- `Katilimci`, `Katilimci Ismi`, `Katilimci Notu` -> participant records.
- `Yorumlar` -> comments.

### Network

Source columns become:

- `Institution` -> organization name with type `NETWORK_INSTITUTION`.
- `Type` -> organization subtype tag or enum.
- `Expertise` -> tags.
- `Geography` -> normalized geography.
- `Contact Person` -> contact extraction.
- `Relationship` -> normalized relationship strength/status.
- `Notes` -> notes.

### AI Tools

No data rows were present in the analyzed workbook. The mapping is ready for future rows.
