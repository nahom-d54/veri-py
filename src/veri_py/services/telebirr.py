"""Telebirr verification service."""

from __future__ import annotations

from ..core.config import VerifierSettings
from ..core.http import HTTPClient
from ..models import TelebirrReceipt
from ..parsers.telebirr import is_valid_telebirr_receipt, parse_telebirr_html


class TelebirrService:
    """Verify Telebirr receipts from the primary Ethio Telecom receipt URL."""

    def __init__(self, http_client: HTTPClient, settings: VerifierSettings) -> None:
        self.http = http_client
        self.settings = settings

    async def verify(self, reference: str) -> TelebirrReceipt | None:
        """Verify Telebirr receipt asynchronously."""
        primary_result = await self._fetch_from_primary_async(reference)
        if is_valid_telebirr_receipt(primary_result):
            return primary_result
        return None

    def verify_sync(self, reference: str) -> TelebirrReceipt | None:
        """Verify Telebirr receipt synchronously."""
        primary_result = self._fetch_from_primary_sync(reference)
        if is_valid_telebirr_receipt(primary_result):
            return primary_result
        return None

    async def _fetch_from_primary_async(self, reference: str) -> TelebirrReceipt | None:
        url = f"{self.settings.telebirr_primary_base_url}{reference}"
        try:
            html = await self.http.get_text_async(url, timeout=30.0, retries=0)
            return parse_telebirr_html(html)
        except Exception:
            return None

    def _fetch_from_primary_sync(self, reference: str) -> TelebirrReceipt | None:
        url = f"{self.settings.telebirr_primary_base_url}{reference}"
        try:
            html = self.http.get_text_sync(url, timeout=30.0, retries=0)
            return parse_telebirr_html(html)
        except Exception:
            return None
