# Local Runbook

This runbook is the fastest path to run the local Borusan AI Ecosystem CRM on Windows.

## 1. Confirm SQL Server

Check SQL Server service:

```powershell
Get-Service | Where-Object { $_.Name -like "MSSQL*" -or $_.DisplayName -like "*SQL Server*" } | Select-Object Name,DisplayName,Status
```

Check ODBC drivers:

```powershell
Get-OdbcDriver | Where-Object { $_.Name -like "*SQL Server*" } | Select-Object Name,Platform
```

Create database for SQLEXPRESS01:

```powershell
sqlcmd -S localhost\SQLEXPRESS01 -E -Q "IF DB_ID('BorusanAIEcosystemCRM') IS NULL CREATE DATABASE BorusanAIEcosystemCRM"
```

Known working SQLEXPRESS01 connection string:

```powershell
$env:DATABASE_URL="mssql+pyodbc://@localhost\SQLEXPRESS01/BorusanAIEcosystemCRM?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
```

Driver 18 trusted connection:

```powershell
$env:DATABASE_URL="mssql+pyodbc://@localhost:1433/BorusanAIEcosystemCRM?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
```

SQL username/password connection:

```powershell
$env:DATABASE_URL="mssql+pyodbc://username:password@localhost:1433/BorusanAIEcosystemCRM?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
```

## 2. Backend

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set local env vars:

```powershell
$env:DATABASE_URL="mssql+pyodbc://@localhost\SQLEXPRESS01/BorusanAIEcosystemCRM?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
$env:JWT_SECRET_KEY="replace-with-a-long-random-local-secret"
$env:BACKEND_CORS_ORIGINS="http://localhost:3000"
$env:INITIAL_ADMIN_EMAIL="admin@example.com"
$env:INITIAL_ADMIN_PASSWORD="change-me-admin-password"
$env:INITIAL_ADMIN_FULL_NAME="Initial Admin"
```

Run migration and seed:

```powershell
python -m alembic upgrade head
python -m app.db.seed
```

Run backend:

```powershell
python -m uvicorn app.main:app --reload
```

Verify:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health/readiness
```

## 3. Frontend

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\frontend
npm install
$env:NEXT_PUBLIC_API_BASE_URL="/api/backend"
$env:BACKEND_API_ORIGIN="http://127.0.0.1:8000"
npm run dev
```

The browser should now talk to the frontend origin only:

```text
http://localhost:3000/api/backend/*
```

Next.js proxies those calls to:

```text
http://127.0.0.1:8000/api/v1/*
```

This avoids local CORS and localhost-vs-127.0.0.1 browser issues. FastAPI still runs directly at `http://127.0.0.1:8000` for Swagger and smoke tests.

The frontend proxy defaults to `http://127.0.0.1:8000` when `BACKEND_API_ORIGIN` is not set. Set
`BACKEND_API_ORIGIN` only when FastAPI runs on a different origin, and use the origin only:

```powershell
$env:BACKEND_API_ORIGIN="http://127.0.0.1:8000"
```

Do not include `/api/v1` in `BACKEND_API_ORIGIN`; the proxy adds that path automatically.

Manual proxy checks:

```text
http://localhost:3000/api/backend/health
http://localhost:3000/api/backend/health/readiness
http://localhost:3000/api/backend/health/routes
http://localhost:3000/api/backend/dashboard/summary
http://localhost:3000/api/backend/use-cases?limit=10
http://localhost:3000/api/backend/program-activities?limit=10
```

Open:

```text
http://localhost:3000
```

Events are managed from one UI route:

```text
http://localhost:3000/events
```

The Events Library includes AI Studio events, communication activities, and training/education programs. The older `/program-activities` frontend route redirects to `/events`; the backend `/api/v1/program-activities` API remains active for program activity data.

## 4. Smoke Test

Keep backend running, then in a second terminal:

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\Activate.ps1
$env:SMOKE_API_BASE_URL="http://127.0.0.1:8000"
$env:SMOKE_ADMIN_EMAIL="admin@example.com"
$env:SMOKE_ADMIN_PASSWORD="change-me-admin-password"
python scripts\smoke_test_api.py
```

Expected result: all checks pass.

## 5. Stop Services

Use `Ctrl+C` in each terminal running `uvicorn` and `npm run dev`.
