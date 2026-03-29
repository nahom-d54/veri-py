"""Environment-backed configuration for veri-py."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DirectServiceProxyMode(StrEnum):
    """How outbound proxy is applied to direct verification HTTP traffic (not vision/LLM)."""

    ALWAYS_PROXY = "always_proxy"
    RETRY_WITH_PROXY = "retry_with_proxy"


class VerifierSettings(BaseSettings):
    """Typed settings used across all provider services."""

    request_timeout_seconds: float = Field(default=30.0, alias="VERI_REQUEST_TIMEOUT_SECONDS")
    request_retries: int = Field(default=2, alias="VERI_REQUEST_RETRIES")
    request_retry_delay_seconds: float = Field(default=0.75, alias="VERI_RETRY_DELAY_SECONDS")
    verify_tls: bool = Field(default=True, alias="VERI_VERIFY_TLS")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        alias="VERI_USER_AGENT",
    )

    network_proxy_url: str | None = Field(default=None, alias="VERI_PROXY_URL")
    direct_service_proxy_mode: DirectServiceProxyMode = Field(
        default=DirectServiceProxyMode.ALWAYS_PROXY,
        alias="VERI_DIRECT_SERVICE_PROXY_MODE",
    )

    skip_primary_verification: bool = Field(default=False, alias="SKIP_PRIMARY_VERIFICATION")
    fallback_proxies: str = Field(default="", alias="FALLBACK_PROXIES")

    telebirr_primary_base_url: str = Field(
        default="https://transactioninfo.ethiotelecom.et/receipt/",
        alias="TELEBIRR_PRIMARY_BASE_URL",
    )
    mpesa_primary_base_url: str = Field(
        default="https://m-pesabusiness.safaricom.et/api/receipt/getReceipt",
        alias="MPESA_PRIMARY_BASE_URL",
    )
    dashen_primary_base_url: str = Field(
        default="https://receipt.dashensuperapp.com/receipt/",
        alias="DASHEN_PRIMARY_BASE_URL",
    )
    abyssinia_primary_base_url: str = Field(
        default="https://cs.bankofabyssinia.com/api/onlineSlip/getDetails/",
        alias="ABYSSINIA_PRIMARY_BASE_URL",
    )
    cbebirr_primary_base_url: str = Field(
        default="https://cbepay1.cbe.com.et/aureceipt/",
        alias="CBEBIRR_PRIMARY_BASE_URL",
    )
    cbe_primary_base_url: str = Field(
        default="https://apps.cbe.com.et:100/",
        alias="CBE_PRIMARY_BASE_URL",
    )

    openai_api_key: str | None = Field(default=None, alias="VERI_OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="VERI_OPENAI_BASE_URL",
    )
    openai_vision_model: str = Field(default="gpt-4o-mini", alias="VERI_OPENAI_VISION_MODEL")

    enable_cbe_browser_fallback: bool = Field(default=False, alias="CBE_BROWSER_FALLBACK")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def fallback_proxy_urls(self) -> list[str]:
        """Return normalized fallback proxy URL list from comma-separated env value."""
        return [url.strip() for url in self.fallback_proxies.split(",") if url.strip()]
