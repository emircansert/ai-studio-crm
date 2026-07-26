"""Microsoft Entra ID (Azure AD) bearer-token validation.

The app registration exposes no custom API, so the frontend signs in with the
standard delegated scopes (openid/profile/email/User.Read) via MSAL
(authorization code + PKCE) and sends the resulting **OIDC ID token** as the
Bearer credential.

This module validates that ID token: RS256 signature against the tenant JWKS,
issuer, expiry, tenant (`tid`), and an audience equal to this application's
client id. A Microsoft Graph access token is addressed to Graph, not to this
application, so it fails the audience check and is correctly rejected.

The `nonce` claim is validated by MSAL in the browser when it processes the
authentication response; the backend receives the token later and cannot
re-check it.

No client secret is required for validation — only Microsoft's public keys.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from typing import Any, Callable

from jose import JWTError, jwt

from app.core.config import settings

JWKS_CACHE_TTL_SECONDS = 3600
# Claims that may carry the user principal name, in preference order.
UPN_CLAIMS = ("preferred_username", "upn", "email")


class EntraAuthError(Exception):
    """Raised when an Entra bearer token cannot be validated."""


def _default_jwks_loader() -> dict[str, Any]:
    if not settings.entra_tenant_id:
        raise EntraAuthError("ENTRA_TENANT_ID is not configured")
    with urllib.request.urlopen(settings.entra_jwks_url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


class EntraTokenValidator:
    """Validates Entra ID access tokens with a cached JWKS keyset.

    The JWKS loader is injectable so tests can supply a locally generated
    keyset instead of calling login.microsoftonline.com.
    """

    def __init__(self, jwks_loader: Callable[[], dict[str, Any]] | None = None) -> None:
        self._jwks_loader = jwks_loader or _default_jwks_loader
        self._jwks: dict[str, Any] | None = None
        self._jwks_fetched_at: float = 0.0
        self._lock = threading.Lock()

    def _get_keys(self, *, force_refresh: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            expired = (time.monotonic() - self._jwks_fetched_at) > JWKS_CACHE_TTL_SECONDS
            if self._jwks is None or expired or force_refresh:
                self._jwks = self._jwks_loader()
                self._jwks_fetched_at = time.monotonic()
            return list(self._jwks.get("keys") or [])

    def _key_for_token(self, token: str) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
        except JWTError as exc:
            raise EntraAuthError("Malformed bearer token") from exc
        kid = header.get("kid")
        if not kid:
            raise EntraAuthError("Bearer token has no key id")
        for keys in (self._get_keys(), self._get_keys(force_refresh=True)):
            for key in keys:
                if key.get("kid") == kid:
                    return key
        raise EntraAuthError("Signing key not found in tenant JWKS")

    def _validate_tenant(self, claims: dict[str, Any]) -> None:
        """Reject tokens minted by a tenant other than the configured one."""
        expected_tenant = settings.entra_tenant_id.strip()
        token_tenant = claims.get("tid")
        if expected_tenant and token_tenant and token_tenant != expected_tenant:
            raise EntraAuthError("Token was issued by an unexpected Microsoft tenant")

    def validate(self, token: str) -> dict[str, Any]:
        """Validate an Entra ID token and return its verified claims.

        Raises EntraAuthError on any failure (signature, issuer, audience,
        expiry, or tenant mismatch).
        """
        audiences = settings.entra_audiences
        if not audiences:
            raise EntraAuthError("ENTRA_CLIENT_ID / ENTRA_AUDIENCE is not configured")
        key = self._key_for_token(token)
        last_error: Exception | None = None
        # python-jose validates a single audience per call; accept any configured one.
        for audience in audiences:
            try:
                claims = jwt.decode(
                    token,
                    key,
                    algorithms=["RS256"],
                    audience=audience,
                    issuer=settings.entra_issuer,
                    options={"verify_at_hash": False},
                )
            except JWTError as exc:
                last_error = exc
                continue
            self._validate_tenant(claims)
            return claims
        raise EntraAuthError(f"Bearer token rejected: {last_error}") from last_error


def extract_upn(claims: dict[str, Any]) -> str:
    for claim in UPN_CLAIMS:
        value = claims.get(claim)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    raise EntraAuthError("Token does not contain a user principal name claim")


def extract_display_name(claims: dict[str, Any], fallback_upn: str) -> str:
    name = claims.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return fallback_upn


entra_validator = EntraTokenValidator()
