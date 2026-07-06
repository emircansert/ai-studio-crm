# Security Notes

## Authentication

Local MVP:

- JWT access tokens.
- Passwords hashed with a modern password hashing algorithm.
- Short-lived access tokens.
- Refresh token support can be added later if needed.

Corporate future:

- Microsoft Entra ID / Azure AD OIDC.
- Map Entra groups to CRM roles.
- Keep local ADMIN/USER authorization checks independent from the identity provider.

## Authorization

Roles:

- `ADMIN`: user management, logo management, import confirmation, vocabulary management, audit logs.
- `USER`: standard CRM usage.

Every write endpoint should check authorization. Admin-only routes should be grouped under `/api/v1/admin`.

## Import Security

- Restrict uploads to `.xlsx`.
- Enforce file size limits.
- Store original filename safely; never use it as a storage path.
- Validate MIME type where possible.
- Do not execute workbook macros.
- Do not trust formulas as computed business truth.
- Treat every workbook value as untrusted input.
- Commit only normalized and validated records.

## Branding Upload Security

- Only admins can upload or activate logos.
- Allowed logo types for MVP: PNG, JPEG, SVG, and WebP.
- Default maximum logo size: 2 MB.
- Validate both declared content type and file extension; prefer content sniffing where available.
- Generate storage keys/paths server-side. Do not use the original filename as a path.
- Store original filename only as metadata.
- Keep exactly one active logo. Activate the new logo and deactivate the previous one in one transaction.
- Write an audit log entry for upload, activation, and replacement.
- Keep the storage interface portable so local volume storage can later be replaced by Azure Blob or internal object storage.

## Data Protection

The workbook contains personal data such as names, emails, and phone numbers. The CRM should:

- Limit access to authenticated users.
- Log data-changing actions.
- Avoid exposing raw import rows to non-admin users unless explicitly allowed.
- Avoid putting secrets or personal data into application logs.
- Support future data retention/deletion policies.

## Audit Logs

Audit logs should be append-only and include:

- Actor.
- Action.
- Entity type and ID.
- Before/after data where appropriate.
- Timestamp.
- IP and user agent when available.

## Secrets

Local:

- `.env` file for secrets.
- `.env` must not be committed.

Corporate:

- Use a managed secret store.
- Rotate JWT/OIDC secrets.
- Separate dev, test, and production settings.

## Network and Deployment

- Use HTTPS in corporate environments.
- Restrict database network access.
- Use least-privilege database credentials.
- Apply database migrations through controlled release steps.
- Enable centralized logging and monitoring for production.
