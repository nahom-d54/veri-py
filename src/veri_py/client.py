"""Public sync/async clients for veri-py consumers."""

from __future__ import annotations

from .core.config import DirectServiceProxyMode, VerifierSettings
from .core.http import HTTPClient
from .models import (
    CBEBirrError,
    CBEBirrReceipt,
    DashenVerifyResult,
    ImageAutoVerifyResult,
    ImageErrorResult,
    ImageForwardResult,
    MpesaVerifyResult,
    TelebirrReceipt,
    VerifyResult,
)
from .services.abyssinia import AbyssiniaService
from .services.cbe import CBEService
from .services.cbebirr import CBEBirrService
from .services.dashen import DashenService
from .services.image import ImageService
from .services.mpesa import MpesaService
from .services.telebirr import TelebirrService


def _resolve_settings(
    settings: VerifierSettings | None,
    *,
    proxy: str | None,
    direct_service_proxy_mode: DirectServiceProxyMode | None,
) -> VerifierSettings:
    base = settings or VerifierSettings()
    updates: dict[str, object] = {}
    if proxy is not None:
        updates["network_proxy_url"] = proxy
    if direct_service_proxy_mode is not None:
        updates["direct_service_proxy_mode"] = direct_service_proxy_mode
    if not updates:
        return base
    return base.model_copy(update=updates)


class AsyncVerifierClient:
    """Async-first API for all verification providers."""

    def __init__(
        self,
        settings: VerifierSettings | None = None,
        *,
        proxy: str | None = None,
        direct_service_proxy_mode: DirectServiceProxyMode | None = None,
    ) -> None:
        self.settings = _resolve_settings(
            settings,
            proxy=proxy,
            direct_service_proxy_mode=direct_service_proxy_mode,
        )
        self.http = HTTPClient(self.settings)

        self.abyssinia_service = AbyssiniaService(self.http, self.settings)
        self.cbe_service = CBEService(self.http, self.settings)
        self.cbebirr_service = CBEBirrService(self.http, self.settings)
        self.dashen_service = DashenService(self.http, self.settings)
        self.mpesa_service = MpesaService(self.http, self.settings)
        self.telebirr_service = TelebirrService(self.http, self.settings)
        self.image_service = ImageService(
            self.settings,
            self.cbe_service,
            self.telebirr_service,
        )

    async def verify_cbe(self, reference: str, account_suffix: str) -> VerifyResult:
        """Verify a CBE receipt."""
        return await self.cbe_service.verify(reference, account_suffix)

    async def verify_telebirr(self, reference: str) -> TelebirrReceipt | None:
        """Verify a Telebirr receipt."""
        return await self.telebirr_service.verify(reference)

    async def verify_dashen(self, reference: str) -> DashenVerifyResult:
        """Verify a Dashen receipt."""
        return await self.dashen_service.verify(reference)

    async def verify_abyssinia(self, reference: str, suffix: str) -> VerifyResult:
        """Verify an Abyssinia transaction."""
        return await self.abyssinia_service.verify(reference, suffix)

    async def verify_cbebirr(
        self,
        receipt_number: str,
        phone_number: str,
        api_key: str,
    ) -> CBEBirrReceipt | CBEBirrError:
        """Verify a CBE Birr receipt."""
        return await self.cbebirr_service.verify(receipt_number, phone_number, api_key)

    async def verify_mpesa(self, transaction_id: str) -> MpesaVerifyResult:
        """Verify an M-Pesa receipt."""
        return await self.mpesa_service.verify(transaction_id)

    async def verify_image(
        self,
        image_bytes: bytes,
        *,
        auto_verify: bool = False,
        account_suffix: str | None = None,
    ) -> ImageAutoVerifyResult | ImageForwardResult | ImageErrorResult:
        """Detect and optionally auto-verify receipt from image bytes."""
        return await self.image_service.verify(
            image_bytes,
            auto_verify=auto_verify,
            account_suffix=account_suffix,
        )


class VerifierClient:
    """Synchronous API for all verification providers."""

    def __init__(
        self,
        settings: VerifierSettings | None = None,
        *,
        proxy: str | None = None,
        direct_service_proxy_mode: DirectServiceProxyMode | None = None,
    ) -> None:
        self.settings = _resolve_settings(
            settings,
            proxy=proxy,
            direct_service_proxy_mode=direct_service_proxy_mode,
        )
        self.http = HTTPClient(self.settings)

        self.abyssinia_service = AbyssiniaService(self.http, self.settings)
        self.cbe_service = CBEService(self.http, self.settings)
        self.cbebirr_service = CBEBirrService(self.http, self.settings)
        self.dashen_service = DashenService(self.http, self.settings)
        self.mpesa_service = MpesaService(self.http, self.settings)
        self.telebirr_service = TelebirrService(self.http, self.settings)
        self.image_service = ImageService(
            self.settings,
            self.cbe_service,
            self.telebirr_service,
        )

    def verify_cbe(self, reference: str, account_suffix: str) -> VerifyResult:
        """Verify a CBE receipt."""
        return self.cbe_service.verify_sync(reference, account_suffix)

    def verify_telebirr(self, reference: str) -> TelebirrReceipt | None:
        """Verify a Telebirr receipt."""
        return self.telebirr_service.verify_sync(reference)

    def verify_dashen(self, reference: str) -> DashenVerifyResult:
        """Verify a Dashen receipt."""
        return self.dashen_service.verify_sync(reference)

    def verify_abyssinia(self, reference: str, suffix: str) -> VerifyResult:
        """Verify an Abyssinia transaction."""
        return self.abyssinia_service.verify_sync(reference, suffix)

    def verify_cbebirr(
        self,
        receipt_number: str,
        phone_number: str,
        api_key: str,
    ) -> CBEBirrReceipt | CBEBirrError:
        """Verify a CBE Birr receipt."""
        return self.cbebirr_service.verify_sync(receipt_number, phone_number, api_key)

    def verify_mpesa(self, transaction_id: str) -> MpesaVerifyResult:
        """Verify an M-Pesa receipt."""
        return self.mpesa_service.verify_sync(transaction_id)

    def verify_image(
        self,
        image_bytes: bytes,
        *,
        auto_verify: bool = False,
        account_suffix: str | None = None,
    ) -> ImageAutoVerifyResult | ImageForwardResult | ImageErrorResult:
        """Detect and optionally auto-verify receipt from image bytes."""
        return self.image_service.verify_sync(
            image_bytes,
            auto_verify=auto_verify,
            account_suffix=account_suffix,
        )
