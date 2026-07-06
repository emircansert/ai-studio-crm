# Security Scan Handover Pack

This folder contains handover artifacts for Borusan Information Security to scan the Borusan AI Ecosystem CRM.

## Included Files

- `openapi.json` - exported FastAPI OpenAPI schema.
- `api_endpoint_inventory.md` - scan-oriented endpoint inventory.
- `security_scan_handover.md` - main handover document for InfoSec.
- `data_format_note.md` - JSON/XML/multipart usage note.
- `postman_collection.json` - starter Postman collection with placeholder variables.

## Swagger / OpenAPI

When the backend is running:

- Swagger UI: `<backend-url>/docs`
- OpenAPI JSON: `<backend-url>/openapi.json`
- ReDoc: `<backend-url>/redoc`
- API base path: `<backend-url>/api/v1`

Local defaults:

- Backend: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Export OpenAPI

From the backend directory:

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\Activate.ps1
python scripts\export_openapi.py
```

Output:

```text
docs/security_scan/openapi.json
```

## Run Locally For Scan

Backend:

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\Activate.ps1
python -m alembic upgrade head
python -m app.db.seed
python -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\frontend
npm install
$env:NEXT_PUBLIC_API_BASE_URL="/api/backend"
$env:BACKEND_API_ORIGIN="http://127.0.0.1:8000"
npm run dev
```

## Required Test Users

Create dedicated scan accounts before testing:

- ADMIN test account: `<admin_test_email>` / `<admin_test_password>`
- USER test account: `<user_test_email>` / `<user_test_password>`

Do not place real credentials in this folder.

## Known Caveats

- The current system uses local JWT authentication, not Microsoft Entra ID.
- XML is not used.
- No external AI/LLM APIs are integrated.
- Admin scan actions can mutate data.
- Import commit and archive/unarchive tests should use dedicated test data.
- File upload tests should use safe synthetic files.

## Contact / Owner

Application owner / technical contact: `<owner_name / team / email TBD>`
