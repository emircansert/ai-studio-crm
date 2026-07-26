# Security Checklist

This checklist is for local MVP review and future corporate deployment readiness.

## Authentication

- [ ] Microsoft Entra ID SSO is the only sign-in path; no local login exists.
- [ ] `ENTRA_TENANT_ID` / `ENTRA_CLIENT_ID` match the app registration.
- [ ] Token signature, issuer, tenant (`tid`), audience, and expiry are all validated.
- [ ] Tokens from other tenants and Microsoft Graph access tokens are rejected.
- [ ] Inactive users are rejected even with a valid Entra token.
- [ ] Frontend clears token on 401/403.
- [ ] `ENTRA_ADMIN_UPNS` is short, reviewed, and treated as privileged config.

## Credential Handling

- [ ] No password or credential column exists on `users` (dropped in migration `20260726_0020`).
- [ ] No client secret is configured, stored, or required anywhere.
- [ ] No `/auth/login`, password-change, or password-reset endpoint exists.
- [ ] Availability risk of the no-break-glass design is accepted in writing (see `docs/auth_entra_id_setup.md`).

## Role-Based Access

- [ ] Admin endpoints require ADMIN.
- [ ] User Management, Branding, and Audit Logs are admin-only.
- [ ] USER role cannot see admin navigation.
- [ ] Backend remains the source of authorization truth.

## Upload Validation

- [ ] Excel import accepts `.xlsx` only.
- [ ] Branding upload accepts image files only.
- [ ] File size limits are enforced.
- [ ] Uploaded files are stored under controlled local directories.
- [ ] Uploaded file paths are not user-controlled public filesystem paths.
- [ ] Future deployment should move files to managed object/blob storage or a controlled internal share.

## Excel Import Safety

- [ ] Raw Excel data is staged first.
- [ ] Dirty data is not directly inserted into CRM domain tables.
- [ ] Candidate generation and preview happen before commit.
- [ ] Duplicate/match warnings are shown.
- [ ] Commit uses approved candidates only.
- [ ] Raw values are preserved for traceability.

## Audit Logging

- [ ] Admin user actions are audit logged.
- [ ] Import actions are audit logged.
- [ ] CRM create/update actions are audit logged.
- [ ] Audit logs are separate from leaderboard contributions.
- [ ] Production retention policy must be defined.

## SQL Server

- [ ] Use least-privilege SQL credentials for application runtime.
- [ ] Avoid using personal Windows trusted connection in shared environments.
- [ ] Protect connection strings outside source control.
- [ ] Enable encrypted connections for non-local environments.
- [ ] Define SQL backup, restore, and retention policies.

## Network / HTTPS

- [ ] Production must use HTTPS.
- [ ] CORS origins must be restricted to approved frontend hosts.
- [ ] API should sit behind an approved reverse proxy or app gateway.
- [ ] Security headers should be reviewed before corporate deployment.

## Secrets

- [ ] `.env` is not committed.
- [ ] Example secrets in `.env.example` are placeholders only.
- [ ] Production secrets should live in a corporate secret store.
- [ ] The only backend secret is the database connection string; Entra tenant/client IDs are public OIDC metadata.

## Backup and Recovery

- [ ] SQL Server database backup is configured.
- [ ] Uploaded import files and branding assets are backed up.
- [ ] Restore process is tested before production usage.
- [ ] CSV export is not treated as a full backup.

## Corporate Deployment Review Items

- [ ] Microsoft Entra ID SSO runtime configuration and redirect URI verification.
- [ ] CRM User Management remains the source of role mapping unless a future Entra group-mapping design is explicitly approved.
- [ ] SQL Server/Azure SQL sizing and access model.
- [ ] File storage target and retention.
- [ ] Vulnerability/dependency scan.
- [ ] Logging/monitoring integration.
- [ ] Backup/restore procedures.
- [ ] Data classification and privacy review.
