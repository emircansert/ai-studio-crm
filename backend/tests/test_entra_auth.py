import time
import unittest
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt

from app.core import entra
from app.core.config import settings
from app.core.entra import EntraAuthError, EntraTokenValidator, extract_display_name, extract_upn

TENANT_ID = "11111111-2222-3333-4444-555555555555"
CLIENT_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
KID = "test-key-1"


def _generate_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


PRIVATE_PEM, PUBLIC_PEM = _generate_keypair()
JWK_DICT = {**jwk.construct(PUBLIC_PEM, "RS256").to_dict(), "kid": KID, "use": "sig"}
OTHER_PRIVATE_PEM, OTHER_PUBLIC_PEM = _generate_keypair()


def make_token(
    *,
    upn: str = "audit.user@borusan.com",
    audience: str | None = None,
    issuer: str | None = None,
    expires_in: int = 600,
    kid: str = KID,
    private_pem: str = PRIVATE_PEM,
    include_upn: bool = True,
) -> str:
    now = int(time.time())
    claims = {
        "sub": str(uuid.uuid4()),
        "aud": audience or f"api://{CLIENT_ID}",
        "iss": issuer or f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
        "iat": now,
        "exp": now + expires_in,
        "name": "Audit User",
    }
    if include_upn:
        claims["preferred_username"] = upn
    return jwt.encode(claims, private_pem, algorithm="RS256", headers={"kid": kid})


class EntraTokenValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._saved = (settings.entra_tenant_id, settings.entra_client_id, settings.entra_audience_raw)
        settings.entra_tenant_id = TENANT_ID
        settings.entra_client_id = CLIENT_ID
        settings.entra_audience_raw = ""

    @classmethod
    def tearDownClass(cls) -> None:
        settings.entra_tenant_id, settings.entra_client_id, settings.entra_audience_raw = cls._saved

    def _validator(self, jwks: dict | None = None) -> EntraTokenValidator:
        return EntraTokenValidator(jwks_loader=lambda: jwks if jwks is not None else {"keys": [JWK_DICT]})

    def test_valid_token_returns_claims(self) -> None:
        claims = self._validator().validate(make_token())
        self.assertEqual(claims["preferred_username"], "audit.user@borusan.com")
        self.assertEqual(extract_upn(claims), "audit.user@borusan.com")
        self.assertEqual(extract_display_name(claims, "x"), "Audit User")

    def test_bare_client_id_audience_accepted(self) -> None:
        claims = self._validator().validate(make_token(audience=CLIENT_ID))
        self.assertIn("aud", claims)

    def test_expired_token_rejected(self) -> None:
        with self.assertRaises(EntraAuthError):
            self._validator().validate(make_token(expires_in=-300))

    def test_wrong_audience_rejected(self) -> None:
        with self.assertRaises(EntraAuthError):
            self._validator().validate(make_token(audience="api://some-other-app"))

    def test_wrong_issuer_rejected(self) -> None:
        with self.assertRaises(EntraAuthError):
            self._validator().validate(make_token(issuer="https://evil.example.com/v2.0"))

    def test_unknown_kid_rejected(self) -> None:
        with self.assertRaises(EntraAuthError):
            self._validator().validate(make_token(kid="unknown-kid"))

    def test_forged_signature_rejected(self) -> None:
        # Token signed by a different private key but claiming our kid.
        with self.assertRaises(EntraAuthError):
            self._validator().validate(make_token(private_pem=OTHER_PRIVATE_PEM))

    def test_upn_missing_rejected(self) -> None:
        claims = self._validator().validate(make_token(include_upn=False))
        with self.assertRaises(EntraAuthError):
            extract_upn(claims)

    def test_upn_normalized_to_lowercase(self) -> None:
        claims = self._validator().validate(make_token(upn="Some.User@BORUSAN.COM"))
        self.assertEqual(extract_upn(claims), "some.user@borusan.com")

    def test_malformed_token_rejected(self) -> None:
        with self.assertRaises(EntraAuthError):
            self._validator().validate("not-a-jwt")

    def test_unconfigured_audience_fails_closed(self) -> None:
        saved = (settings.entra_client_id, settings.entra_audience_raw)
        settings.entra_client_id = ""
        settings.entra_audience_raw = ""
        try:
            with self.assertRaises(EntraAuthError):
                self._validator().validate(make_token())
        finally:
            settings.entra_client_id, settings.entra_audience_raw = saved


class DocsExposureTests(unittest.TestCase):
    def test_environment_fail_closed(self) -> None:
        saved = settings.environment
        try:
            for value, expected in [
                ("development", True),
                ("dev", True),
                ("local", True),
                ("production", False),
                ("staging", False),
                ("", False),
                ("PRODUCTION", False),
                ("Development", True),
                ("garbage-value", False),
            ]:
                settings.environment = value
                self.assertEqual(settings.is_development, expected, value)
        finally:
            settings.environment = saved


class SectionAccessUpnTests(unittest.TestCase):
    def test_default_rows_keyed_by_upn(self) -> None:
        from app.core.section_access import default_access_rows_for_user, user_upn
        from app.models import User

        user = User(email="Mixed.Case@Borusan.com", full_name="X", password_hash="x", role="USER")
        self.assertEqual(user_upn(user), "mixed.case@borusan.com")
        rows = list(default_access_rows_for_user(user))
        self.assertTrue(all(row.user_upn == "mixed.case@borusan.com" for row in rows))
        self.assertTrue(all(row.access_level == "HIDDEN" for row in rows))


if __name__ == "__main__":
    unittest.main()
