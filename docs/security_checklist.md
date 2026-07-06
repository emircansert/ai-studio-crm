# Security Checklist

This checklist is for local MVP review and future corporate deployment readiness.

## Authentication

- [ ] Local JWT auth is acceptable for MVP/demo only.
- [ ] `JWT_SECRET_KEY` is long, random, and environment-specific.
- [ ] Token expiry is configured appropriately.
- [ ] Inactive users cannot log in.
- [ ] Frontend clears token on 401/403.
- [ ] Future Microsoft Entra ID integration is planned before enterprise rollout.

## Password Handling

- [ ] Passwords are hashed with backend security helpers.
- [ ] Password hashes are never exposed through APIs.
- [ ] Temporary passwords are communicated out of band.
- [ ] Password reset events are audit logged.
- [ ] Corporate deployment should review password policy or replace local auth with SSO.

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
- [ ] Local admin seed password must be changed after first setup.

## Backup and Recovery

- [ ] SQL Server database backup is configured.
- [ ] Uploaded import files and branding assets are backed up.
- [ ] Restore process is tested before production usage.
- [ ] CSV export is not treated as a full backup.

## Corporate Deployment Review Items

- [ ] Microsoft Entra ID SSO design.
- [ ] Role mapping from Entra groups to CRM roles.
- [ ] SQL Server/Azure SQL sizing and access model.
- [ ] File storage target and retention.
- [ ] Vulnerability/dependency scan.
- [ ] Logging/monitoring integration.
- [ ] Backup/restore procedures.
- [ ] Data classification and privacy review.
