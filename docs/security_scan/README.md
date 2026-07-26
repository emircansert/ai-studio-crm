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

Sign-in is Microsoft Entra ID only; there is no username/password login to
script. Create dedicated **Entra test accounts** in the tenant, sign in with
each interactively, and use the ID token the browser sends as the bearer:

- ADMIN test account: `<admin_test_upn>`
- USER test account: `<user_test_upn>`

Set the CRM role for each in **User Management**. Tokens expire in roughly 60
minutes and must be refreshed during long scans. Do not place real credentials
or real tokens in this folder.

## Known Caveats

- Authentication is Microsoft Entra ID SSO only. The frontend is an MSAL public client (SPA platform, PKCE, **no client secret**) and sends the OIDC ID token as the API bearer; the backend validates it against Microsoft's public JWKS. There is no local login endpoint and the database stores no credential material.
- There is deliberately no break-glass account: an Entra tenant outage locks everyone out, administrators included.
- XML is not used.
- No external AI/LLM APIs are integrated.
- Admin scan actions can mutate data.
- Import commit and archive/unarchive tests should use dedicated test data.
- File upload tests should use safe synthetic files.

## Contact / Owner

Application owner / technical contact: `<owner_name / team / email TBD>`
