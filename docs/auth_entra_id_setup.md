# Microsoft Entra ID Authentication Setup

Microsoft Entra ID single sign-on is the **only** way to authenticate to this
CRM. Per the Information Security requirement that the application work solely
through Entra users and hold no internal user information, the local credential
path has been removed outright, not merely disabled:

- there is no `/auth/login` endpoint, no password change, and no admin password
  reset;
- the `users` table has no `password_hash` column (migration `20260726_0020`);
- there is no JWT signing secret, because the application issues no tokens of
  its own.

The `users` table still exists, holding only the Entra UPN, display name, CRM
role, active flag, and last-login timestamp — no credential material.

The Entra implementation is a **browser-based public-client flow**: the frontend
uses MSAL (`@azure/msal-browser`) with `loginPopup`, the authorization code is
redeemed in the browser using PKCE, and the backend validates the resulting
token against Microsoft's public JWKS keys.

**There is no client secret anywhere in this application.** The backend never
performs a server-side token exchange and never holds Entra credentials.

## Azure App Registration

Register the redirect URIs under the **Single-page application (SPA)** platform.

> **Do not use the "Web" platform.** The Web platform is for confidential
> clients that redeem the authorization code server-side with a secret. This
> app redeems the code in the browser, so Microsoft requires the `spa` redirect
> type. A Web-platform registration fails at the final token-redemption step
> with `AADSTS9002326: Cross-origin token redemption is permitted only for the
> 'Single-Page Application' client-type` — note that sign-in *appears* to work
> up to that point, which makes this misconfiguration easy to miss.

Currently registered:

```text
https://library.borusan.com/auth/callback
http://localhost:3000/auth/callback
https://localhost:3000/auth/callback
```

Rules that matter, because redirect URI matching is exact-string:

- No trailing slash.
- Lowercase path, exactly `/auth/callback`.
- `http` is permitted only for `localhost`; everything else must be `https`.
- For `localhost` redirect URIs Microsoft ignores the port when matching, so a
  single `http://localhost:3000/auth/callback` entry also covers dev servers
  started on other ports.

No client secret is required. If one already exists on the registration, this
app does not use it and it should not be distributed to the application team.

### Permissions and scopes

The registration grants **delegated Microsoft Graph permissions only** and
deliberately **exposes no custom API**. Sign-in therefore requests:

```text
openid  profile  email  User.Read
```

`profile` and `email` are what populate the `preferred_username` / `email` /
`name` claims the backend uses to identify the user.

> **Do not add an `api://<client-id>/...` scope to the sign-in request.** There
> is no Application ID URI on this registration, so Microsoft rejects it with
> `AADSTS500011: The resource principal named api://<client-id> was not found in
> the tenant`. There is no `NEXT_PUBLIC_ENTRA_API_SCOPE` variable for this
> reason.

Because there is no custom API to issue an access token for, the CRM API is
authenticated with the **OIDC ID token**, whose audience is the client id
itself. The Graph access token MSAL also obtains is not used — it is addressed
to Microsoft Graph, not to this application.

## Backend Environment

The backend needs the tenant and client identifiers only, to validate incoming
tokens. Placeholders only — never commit real values:

```env
ENVIRONMENT=production
ENTRA_TENANT_ID=
ENTRA_CLIENT_ID=
ENTRA_ADMIN_UPNS=
```

`AUTH_MODE` is retained as an accepted-but-ignored setting so an existing
deployment's environment file does not break start-up. Its only supported value
is `entra`; no other mode exists in the code.

Optional overrides, normally left empty:

```env
# Comma-separated accepted audiences. When empty the backend accepts the bare
# ENTRA_CLIENT_ID, which is the audience of the OIDC ID token used for sign-in.
ENTRA_AUDIENCE=
# Only needed for non-standard Microsoft clouds.
ENTRA_ISSUER=
ENTRA_JWKS_URL=
```

Notes:

- There is no `JWT_SECRET_KEY`: the application issues no tokens of its own and
  only validates Microsoft-signed ID tokens against the public JWKS.
- `ENVIRONMENT` must be `development` to expose Swagger/ReDoc/OpenAPI. Any other
  value — including unset — disables them (fail closed).
- The backend reads `.env` relative to its working directory, so the file must
  be at `backend/.env` when uvicorn is started from `backend/`.

## Frontend Environment

These are compiled into the browser bundle at **build time** (standard Next.js
`NEXT_PUBLIC_*` behaviour), so they must be supplied as Docker build args, not
only at container-run time. None of them are secrets: the client id, tenant id,
and redirect URI are public OIDC metadata.

```env
NEXT_PUBLIC_ENTRA_CLIENT_ID=
NEXT_PUBLIC_ENTRA_TENANT_ID=
NEXT_PUBLIC_ENTRA_REDIRECT_URI=
NEXT_PUBLIC_API_BASE_URL=/api/backend
BACKEND_API_ORIGIN=http://127.0.0.1:8001
```

There is no API-scope variable; the delegated scopes are fixed in code
(`ENTRA_LOGIN_SCOPES` in `frontend/src/lib/entraAuth.ts`).

`NEXT_PUBLIC_ENTRA_REDIRECT_URI` is the **base origin only**, for example
`https://library.borusan.com`. The app appends `/auth/callback` itself
(`buildEntraRedirectUri` in `frontend/src/lib/entraAuth.ts`), strips any
trailing slash, and tolerates a value that already includes the path. The URI
registered in Azure must be the full `<base>/auth/callback` value.

`BACKEND_API_ORIGIN` is a server-side runtime variable for the Next.js proxy and
is not compiled into the bundle.

## Login Flow

1. The user clicks **Sign in with Microsoft** on `/login`.
2. MSAL opens a popup to the tenant authorize endpoint with `response_type=code`,
   a PKCE `code_challenge` (S256), and scopes
   `openid profile email User.Read`.
3. The user authenticates with Microsoft.
4. Microsoft redirects the **popup** to `<origin>/auth/callback`, a minimal
   static page whose only job is to let MSAL read the response and close the
   popup. It renders no application shell and must remain reachable without
   authentication.
5. MSAL redeems the code in the browser and returns an **ID token** (plus a
   Graph access token, which this app does not use).
6. The frontend stores the ID token and sends it as the `Authorization: Bearer`
   header on API calls.
7. The backend validates it on each request against the tenant JWKS: RS256
   signature, issuer, expiry, tenant (`tid`), and audience equal to the client
   id. It then maps the token's UPN to a CRM user.

In `entra` mode the Microsoft **ID token** is the API bearer credential; the CRM
does not mint its own JWT. The frontend refreshes it silently every 20 minutes
via `acquireTokenSilent`.

A Microsoft Graph access token is addressed to Graph (`aud` = Graph), so it
fails the audience check and cannot be used against this API.

The `nonce` claim is validated by MSAL in the browser when it processes the
authentication response. The backend receives the token afterwards and cannot
re-check the nonce.

Because the redirect URIs are registered as `spa`, Microsoft expires their
refresh tokens after 24 hours. Users are silently re-authenticated roughly once
a day through the existing Microsoft session — normally with no visible prompt.
Daily re-authentication in logs is expected behaviour, not a fault.

## User Mapping and Provisioning

Users are matched on the token's user principal name, taken from the first
claim present among `preferred_username`, `upn`, `email`, and lower-cased. It is
compared against `users.email` in the CRM.

| Situation | Result |
| --- | --- |
| Existing active CRM user | Signs in; existing role and per-section permissions preserved. |
| Existing inactive CRM user | Rejected. |
| Existing user whose UPN is in `ENTRA_ADMIN_UPNS` | Promoted to `ADMIN` on sign-in. |
| Unknown user, UPN **not** in `ENTRA_ADMIN_UPNS` | Created just-in-time as `USER`, with **every section HIDDEN** until an admin grants access. |
| Unknown user, UPN **in** `ENTRA_ADMIN_UPNS` | Created just-in-time as `ADMIN` with full access. |

`ENTRA_ADMIN_UPNS` is a comma-separated list of UPNs, for example:

```env
ENTRA_ADMIN_UPNS=first.admin@borusan.com,second.admin@borusan.com
```

It exists to solve the bootstrap problem: with no local login there would
otherwise be no way to obtain an initial administrator. Keep the list short,
treat it as a privileged configuration value, and review it after rollout.
Day-to-day role and section-permission management remains in CRM **User
Management**, which is the source of truth.

Because it is evaluated on every sign-in, `ENTRA_ADMIN_UPNS` is also the
recovery path if the last CRM admin is accidentally demoted or deactivated: add
the UPN, restart the backend, and have that person sign in again. The full
procedure is in the README under **"Locked Out? Admin Recovery Procedure"** —
that is the canonical operator-facing copy.

Newly provisioned non-admin users hold no explicit permission rows; the section
middleware falls back to the non-admin default of HIDDEN for every section.

## Cutover Checklist

1. Confirm at least one CRM user's `email` exactly matches an administrator's
   Entra UPN, **or** list that UPN in `ENTRA_ADMIN_UPNS`. There is no local
   login, so this is the only way in.
2. Verify the Azure registration uses the **SPA** platform with the exact
   `/auth/callback` URI.
3. Build the frontend image with the `NEXT_PUBLIC_ENTRA_*` build args set.
4. Run `alembic upgrade head` so `users.password_hash` is dropped.
5. Complete one real sign-in end to end.

### Availability risk to accept explicitly

With no local credential path, **an Entra ID or tenant-wide outage makes the CRM
completely inaccessible, including to administrators.** There is no break-glass
account, by design — that is the direct consequence of the "no internal user
information" requirement. The dependency is the same one that already applies to
Microsoft 365, so in practice a tenant outage means most internal tooling is
down anyway. If Information Security later wants a bounded exception, it should
be an explicit, audited decision rather than a leftover code path.

## Security Notes

- Use HTTPS outside local development.
- No client secret is used, stored, or required by this application.
- No password or other local credential material is stored in the database.
- Never commit `.env`, tenant IDs, client IDs, or Microsoft tokens.
- The frontend stores the bearer token in `localStorage`. This should be
  reviewed with Information Security before production if HttpOnly session
  cookies are required.
- API documentation endpoints (`/docs`, `/redoc`, `/openapi.json`) return 404
  unless `ENVIRONMENT=development`.

## Local Testing

Start both services, then check:

```text
http://localhost:3000/api/backend/auth/config
http://localhost:3000/auth/callback
```

The first returns `{"auth_mode": "entra"}`. The second must return the minimal
"Completing Microsoft sign-in..." page **without** redirecting to the login
page — if it redirects or 404s, the popup cannot complete and sign-in will fail.

`POST /api/backend/auth/login` must return **HTTP 404**: the endpoint no longer
exists. Together with a `users` table that has no `password_hash` column, that
is the check that the local credential path is gone rather than merely disabled.
