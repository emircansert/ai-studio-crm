# Local Development Setup

The local MVP now uses Microsoft SQL Server instead of a containerized database.

## Prerequisites

- Python 3.11+.
- Microsoft SQL Server running locally or reachable on the network.
- Microsoft ODBC Driver 18 for SQL Server. If your machine only has Driver 17 installed, either install Driver 18 or change the `driver=` value in `DATABASE_URL` to `ODBC+Driver+17+for+SQL+Server`.
- Node.js 20+ when frontend work resumes.

## Create Local Database

Database name:

```sql
CREATE DATABASE BorusanAIEcosystemCRM;
GO
```

You can run this in SQL Server Management Studio, Azure Data Studio, or `sqlcmd`.

## Environment

Copy `.env.example` to `.env` and set `DATABASE_URL`.

SQL username/password example:

```text
DATABASE_URL=mssql+pyodbc://username:password@localhost:1433/BorusanAIEcosystemCRM?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
```

Windows trusted connection example:

```text
DATABASE_URL=mssql+pyodbc://@localhost:1433/BorusanAIEcosystemCRM?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes
```

Important local variables:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `BACKEND_CORS_ORIGINS`
- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`
- `INITIAL_ADMIN_FULL_NAME`

## Test SQL Server Connection

From `backend/` after installing dependencies:

```powershell
@'
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    print(conn.execute(text("SELECT DB_NAME()")).scalar())
'@ | python -
```

Expected output:

```text
BorusanAIEcosystemCRM
```

## Backend Commands

From `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
```

Seed controlled vocabularies, Borusan companies, and an optional initial admin:

```powershell
$env:INITIAL_ADMIN_EMAIL="admin@example.com"
$env:INITIAL_ADMIN_PASSWORD="change-me-admin-password"
$env:INITIAL_ADMIN_FULL_NAME="Initial Admin"
python -m app.db.seed
```

Run the backend:

```powershell
uvicorn app.main:app --reload
```

Expected local services:

- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## Frontend Commands

From `frontend/`:

```powershell
npm install
npm run dev
```

Optional frontend environment variable:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Expected frontend URL:

```text
http://localhost:3000
```

Use `/login` first, then open the Import Center from the sidebar. The Import Center calls the live backend upload and preview endpoints.

## Notes

- Excel import commit is not implemented yet. Upload, profiling, staging, warnings, and preview are implemented.
- AI features are not implemented yet.
- Container orchestration is intentionally not part of the local MVP path now.
