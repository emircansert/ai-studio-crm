# Backup and Restore Notes

## SQL Server Backup Recommendation

For any shared demo, pilot, or production-like environment, use SQL Server native backups.

Example local backup command:

```sql
BACKUP DATABASE BorusanAIEcosystemCRM
TO DISK = 'C:\Backups\BorusanAIEcosystemCRM.bak'
WITH INIT, COMPRESSION;
```

PowerShell via `sqlcmd`:

```powershell
sqlcmd -S localhost\SQLEXPRESS01 -E -Q "BACKUP DATABASE BorusanAIEcosystemCRM TO DISK = 'C:\Backups\BorusanAIEcosystemCRM.bak' WITH INIT"
```

## Restore Considerations

Restore into a separate environment first:

```sql
RESTORE DATABASE BorusanAIEcosystemCRM_RestoreTest
FROM DISK = 'C:\Backups\BorusanAIEcosystemCRM.bak'
WITH MOVE 'BorusanAIEcosystemCRM' TO 'C:\SQLData\BorusanAIEcosystemCRM_RestoreTest.mdf',
     MOVE 'BorusanAIEcosystemCRM_log' TO 'C:\SQLData\BorusanAIEcosystemCRM_RestoreTest.ldf';
```

Logical file names vary by SQL Server setup. Confirm them with:

```sql
RESTORE FILELISTONLY FROM DISK = 'C:\Backups\BorusanAIEcosystemCRM.bak';
```

## Uploaded Files Backup

Back up:

- `backend/uploads/`
- `backend/uploads/branding/`

The database stores metadata and file paths. A database backup without uploaded files may leave branding/import references incomplete.

## CSV Export Limitations

Startup Library CSV export is for working extracts and business review. It is not a full backup because it does not include:

- All relational tables.
- Audit logs.
- Import staging rows.
- Import candidates.
- User accounts.
- Uploaded files.
- Complete relationship history.

## Local Dev Reset

For local development only:

1. Stop backend and frontend.
2. Back up the database if needed.
3. Drop/recreate local database.
4. Run migrations.
5. Run seed.
6. Re-import workbook if needed.

Example:

```powershell
sqlcmd -S localhost\SQLEXPRESS01 -E -Q "ALTER DATABASE BorusanAIEcosystemCRM SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE BorusanAIEcosystemCRM; CREATE DATABASE BorusanAIEcosystemCRM"
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\Activate.ps1
python -m alembic upgrade head
python -m app.db.seed
```

## Production Warning

Never drop, reset, or overwrite a production or shared pilot database casually. Confirm backup integrity and restore plan first.
