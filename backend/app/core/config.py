from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Borusan AI Studio CRM"
    database_url: str = Field(
        default="mssql+pyodbc://@localhost\\SQLEXPRESS01/BorusanAIEcosystemCRM?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes",
        alias="DATABASE_URL",
    )
    # Deployment environment. Anything other than an explicit development value
    # is treated as production (fail closed) for things like API docs exposure.
    environment: str = Field(default="production", alias="ENVIRONMENT")
    # AUTH_MODE selects the authentication backend:
    #   "local" - legacy email/password with app-issued HS256 JWTs (development only).
    #   "entra" - Microsoft Entra ID (Azure AD) OIDC bearer tokens; local passwords disabled.
    auth_mode: str = Field(default="local", alias="AUTH_MODE")
    jwt_secret_key: str = Field(default="change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    # Microsoft Entra ID (Azure AD) settings; required when AUTH_MODE=entra.
    entra_tenant_id: str = Field(default="", alias="ENTRA_TENANT_ID")
    entra_client_id: str = Field(default="", alias="ENTRA_CLIENT_ID")
    # Audience accepted on incoming tokens. Defaults to both the api://<client-id>
    # Application ID URI form and the bare client id, which covers common setups.
    entra_audience_raw: str = Field(default="", alias="ENTRA_AUDIENCE")
    entra_issuer_override: str = Field(default="", alias="ENTRA_ISSUER")
    entra_jwks_url_override: str = Field(default="", alias="ENTRA_JWKS_URL")
    # Comma-separated UPNs that are bootstrapped as ADMIN on first Entra sign-in.
    entra_admin_upns_raw: str = Field(default="", alias="ENTRA_ADMIN_UPNS")
    backend_cors_origins_raw: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
        alias="BACKEND_CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def backend_cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.backend_cors_origins_raw.replace("\n", ",").split(",")
            if origin.strip() and origin.strip() != "*"
        ]

    @property
    def is_development(self) -> bool:
        return self.environment.strip().lower() in {"development", "dev", "local"}

    @property
    def is_entra_auth(self) -> bool:
        return self.auth_mode.strip().lower() == "entra"

    @property
    def entra_issuer(self) -> str:
        if self.entra_issuer_override:
            return self.entra_issuer_override
        return f"https://login.microsoftonline.com/{self.entra_tenant_id}/v2.0"

    @property
    def entra_jwks_url(self) -> str:
        if self.entra_jwks_url_override:
            return self.entra_jwks_url_override
        return f"https://login.microsoftonline.com/{self.entra_tenant_id}/discovery/v2.0/keys"

    @property
    def entra_audiences(self) -> list[str]:
        if self.entra_audience_raw.strip():
            return [item.strip() for item in self.entra_audience_raw.split(",") if item.strip()]
        if not self.entra_client_id:
            return []
        return [f"api://{self.entra_client_id}", self.entra_client_id]

    @property
    def entra_admin_upns(self) -> set[str]:
        return {
            upn.strip().lower()
            for upn in self.entra_admin_upns_raw.split(",")
            if upn.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
