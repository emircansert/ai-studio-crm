# Excel Import Phase 1

Excel Import Phase 1 implements upload, profiling, staging, validation warnings, and preview only. It does not commit normalized CRM records into `organizations`, `opportunities`, `events`, `contacts`, `ai_tools`, or related domain tables.

## Implemented Endpoints

- `GET /api/v1/imports`
  - Lists import batches.
- `GET /api/v1/imports/{batch_id}`
  - Reads one import batch.
- `POST /api/v1/imports/upload`
  - Admin-only workbook upload.
  - Accepts `.xlsx` only.
  - Enforces a 25 MB upload limit.
  - Calculates SHA-256.
  - Stores the uploaded workbook under `backend/uploads/imports`.
  - Creates an `import_batches` record with workbook metadata.
  - Profiles sheets, detects mappings, stages rows, and creates warnings.
- `GET /api/v1/imports/{batch_id}/preview`
  - Returns the staged preview summary.
- `POST /api/v1/imports/{batch_id}/commit`
  - Present as an intentional placeholder.
  - Returns `501 Not Implemented`.

## Workbook Profiling

The import pipeline reads the workbook with `openpyxl` and uses:

- `config/sheet_mapping.yml` for expected sheet names, entity types, header row, first data row, and required columns.
- `config/column_mapping.yml` for source column-to-target intent.
- `config/status_mapping.yml` for controlled status aliases.

Known entity types:

- `STARTUP_LIBRARY`
- `POC_OPPORTUNITIES`
- `EVENTS`
- `NETWORK`
- `AI_TOOLS`
- `CONTROLLED_LISTS`

Unknown sheets are stored in `import_sheets` with `detected_entity = UNKNOWN` and produce an `UNKNOWN_SHEET` warning. Missing required sheets and required columns also produce warnings.

## Staging Behavior

For each known sheet, Phase 1 stages non-empty data rows into `import_rows`.

Stored row fields:

- `raw_values`
  - Original cell values converted only to JSON-safe values.
- `cleaned_values`
  - Safe cleaned values.
- `normalized_candidate`
  - Minimal candidate hints such as entity type, normalized name, and website domain.
- `excel_row_number`
  - Source workbook row number.
- `row_hash`
  - SHA-256 hash of raw row values.
- `validation_status`
  - `VALID` or `WARNING` in Phase 1.

Cleaning is intentionally conservative:

- trim whitespace
- collapse repeated whitespace
- normalize blank placeholders like `-`, `?`, `N/A`, `NA`, empty string to null
- convert Excel dates/datetimes to ISO strings
- preserve raw source values separately

The pipeline does not guess ambiguous values.

## Validation Warnings

Phase 1 can create:

- `UNKNOWN_SHEET`
- `MISSING_REQUIRED_SHEET`
- `MISSING_REQUIRED_COLUMN`
- `EMPTY_ROW_SKIPPED`
- `PARTIAL_DATE`
- `UNKNOWN_STATUS`
- `DUPLICATE_NORMALIZED_COMPANY_NAME_CANDIDATE`
- `DUPLICATE_WEBSITE_DOMAIN_CANDIDATE`
- `MALFORMED_WEBSITE_URL`
- `MISSING_WEBSITE`
- `CONTACT_WITHOUT_EMAIL`

Batch-level warnings use `import_warnings.import_batch_id`. Row-level warnings also link to `import_warnings.import_row_id`.

## Preview Response

`GET /api/v1/imports/{batch_id}/preview` returns:

- batch metadata
- detected sheets
- row counts by sheet
- staged row counts by entity type
- warning counts by severity and code
- sample staged rows per entity type
- duplicate candidates
- missing mappings or columns
- status mappings used

## Local Testing Through FastAPI Docs

1. Start the backend:

   ```powershell
   cd C:\Users\emirc\borusan-ai-studio-crm\backend
   .\.venv\Scripts\uvicorn.exe app.main:app --reload
   ```

2. Open:

   ```text
   http://127.0.0.1:8000/docs
   ```

3. Sign in to the CRM at `http://localhost:3000` as an `ADMIN` user and copy the
   Entra ID token the browser sends as the `Authorization` bearer. (There is no
   login endpoint: authentication is Microsoft Entra ID single sign-on only.)

4. Click **Authorize** in Swagger and paste:

   ```text
   Bearer <entra_id_token>
   ```

5. Use `POST /api/v1/imports/upload` and upload:

   ```text
   C:\Users\emirc\Downloads\Ekosistem_Library_V2.xlsx
   ```

6. Copy the returned batch `id`.

7. Call `GET /api/v1/imports/{batch_id}/preview`.

## Local Profiling Script

For a quick workbook profile without touching the database:

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\python.exe -m scripts.profile_workbook C:\Users\emirc\Downloads\Ekosistem_Library_V2.xlsx
```

## Intentionally Not Implemented

- import commit
- normalized CRM record creation
- admin conflict resolution UI
- full Excel date parsing and interpretation
- contact splitting into first/last/name/title fields
- advanced duplicate resolution
- AI-assisted tagging, summarization, duplicate detection, or natural-language search

## Next Phase

Excel Import Phase 2 should implement normalization and confirmed commit:

- map staged startup rows into `organizations`
- link PoC rows to existing or admin-selected organizations
- create opportunities/events/network records after admin confirmation
- enforce `config/import_policy.yml`
- add an admin preview/decision UI
