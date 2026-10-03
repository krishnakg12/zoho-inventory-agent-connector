"""
Configuration management for Zoho Inventory MCP Connector.
Enforces validation, secret handling, tenant isolation, and operational defaults.
"""

from typing import Literal, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def derive_accounts_url(base_url: str) -> str:
    """Derive official Zoho Accounts URL from base API URL domain/region."""
    lower_base = base_url.lower()
    if ".in" in lower_base:
        return "https://accounts.zoho.in"
    elif ".eu" in lower_base:
        return "https://accounts.zoho.eu"
    elif ".com.au" in lower_base:
        return "https://accounts.zoho.com.au"
    elif ".jp" in lower_base:
        return "https://accounts.zoho.jp"
    elif ".ca" in lower_base:
        return "https://accounts.zoho.ca"
    return "https://accounts.zoho.com"


class Settings(BaseSettings):
    """Application configuration and credentials loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Operating Mode
    app_mode: Literal["mock", "live"] = Field(
        default="mock",
        description="Operating mode: 'mock' for deterministic offline testing/demo, 'live' for real Zoho API.",
    )

    # Zoho Merchant Context (Locked to server configuration; never agent-controlled)
    zoho_organization_id: Optional[str] = Field(
        default=None,
        description="The locked numeric organization ID for the merchant in Zoho Inventory.",
    )

    # OAuth 2.0 Credentials
    zoho_client_id: Optional[str] = Field(
        default=None,
        description="Zoho OAuth Client ID.",
    )
    zoho_client_secret: Optional[str] = Field(
        default=None,
        description="Zoho OAuth Client Secret.",
    )
    zoho_refresh_token: Optional[str] = Field(
        default=None,
        description="Zoho OAuth permanent Refresh Token.",
    )

    # Endpoints
    zoho_base_url: str = Field(
        default="https://www.zohoapis.com/inventory/v1",
        description="Base URL for the Zoho Inventory REST API.",
    )
    zoho_accounts_url: Optional[str] = Field(
        default=None,
        description="Base URL for Zoho Accounts OAuth server (auto-derived if omitted).",
    )

    # Resilience & Rate Limiting (Safety headroom below Zoho's 100 req/min)
    rate_limit_requests_per_minute: int = Field(
        default=60,
        ge=1,
        le=100,
        description="Client-side request rate limit per minute.",
    )
    max_concurrent_requests: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent HTTP requests allowed.",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retries for transient failures.",
    )
    request_timeout_seconds: float = Field(
        default=15.0,
        gt=0.0,
        le=60.0,
        description="HTTP request timeout in seconds.",
    )

    # Context Window & Pagination Protections
    default_page_size: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Default number of records per page.",
    )
    max_page_size: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Hard upper bound for records per page.",
    )
    max_response_bytes: int = Field(
        default=65536,
        ge=256,
        description="Maximum serialized response size in bytes before explicit truncation.",
    )

    # Observability
    log_level: str = Field(default="INFO", description="Log level.")
    log_json: bool = Field(default=False, description="Format logs as JSON.")

    @field_validator("zoho_base_url")
    @classmethod
    def clean_base_url(cls, v: str) -> str:
        url = v.rstrip("/")
        # If user passes e.g. https://zohoapis.in without /inventory/v1, normalize it
        if not url.endswith("/inventory/v1"):
            url = f"{url}/inventory/v1"
        return url

    @model_validator(mode="after")
    def validate_and_derive(self) -> "Settings":
        # Auto-derive accounts URL if not explicitly provided
        if not self.zoho_accounts_url:
            self.zoho_accounts_url = derive_accounts_url(self.zoho_base_url)
        else:
            self.zoho_accounts_url = self.zoho_accounts_url.rstrip("/")

        # Validate credentials when live mode is requested
        if self.app_mode == "live":
            missing = []
            placeholders = ["YOUR_NUMERIC_ORGANIZATION_ID", "YOUR_GENERATED_PERMANENT_REFRESH_TOKEN", "your_zoho_client_id_here"]
            if not self.zoho_organization_id or self.zoho_organization_id in placeholders:
                missing.append("ZOHO_ORGANIZATION_ID")
            if not self.zoho_client_id or self.zoho_client_id in placeholders:
                missing.append("ZOHO_CLIENT_ID")
            if not self.zoho_client_secret or self.zoho_client_secret in placeholders:
                missing.append("ZOHO_CLIENT_SECRET")
            if not self.zoho_refresh_token or self.zoho_refresh_token in placeholders:
                missing.append("ZOHO_REFRESH_TOKEN")

            if missing:
                raise ValueError(
                    f"Live mode requires valid Zoho credentials. Missing or placeholder values for: {', '.join(missing)}"
                )
        return self


# Global singleton cache for settings
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Retrieve global cached settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reset_settings(new_settings: Optional[Settings] = None) -> None:
    """Reset cached settings (primarily for test isolation)."""
    global _settings_instance
    _settings_instance = new_settings
