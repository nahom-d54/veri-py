"""Telebirr verification service."""

from __future__ import annotations

import json

from ..core.config import VerifierSettings
from ..core.http import HTTPClient
from ..exceptions import TelebirrVerificationError
from ..models import TelebirrReceipt
from ..parsers.telebirr import is_valid_telebirr_receipt, parse_telebirr_html, parse_telebirr_json


class TelebirrService:
    """Verify Telebirr receipts using primary source with fallback proxy pool."""

    def __init__(self, http_client: HTTPClient, settings: VerifierSettings) -> None:
        self.http = http_client
        self.settings = settings

    async def verify(self, reference: str) -> TelebirrReceipt | None:
        """Verify Telebirr receipt asynchronously."""
        if not self.settings.skip_primary_verification:
            primary_result = await self._fetch_from_primary_async(reference)
            if is_valid_telebirr_receipt(primary_result):
                return primary_result

        if not self.settings.fallback_proxy_urls and self.settings.skip_primary_verification:
            return None

        for proxy_base in self.settings.fallback_proxy_urls:
            try:
                fallback_result = await self._fetch_from_proxy_async(reference, proxy_base)
                if is_valid_telebirr_receipt(fallback_result):
                    return fallback_result
            except TelebirrVerificationError:
                continue

        return None

    def verify_sync(self, reference: str) -> TelebirrReceipt | None:
        """Verify Telebirr receipt synchronously."""
        if not self.settings.skip_primary_verification:
            primary_result = self._fetch_from_primary_sync(reference)
            if is_valid_telebirr_receipt(primary_result):
                return primary_result

        if not self.settings.fallback_proxy_urls and self.settings.skip_primary_verification:
            return None

        for proxy_base in self.settings.fallback_proxy_urls:
            try:
                fallback_result = self._fetch_from_proxy_sync(reference, proxy_base)
                if is_valid_telebirr_receipt(fallback_result):
                    return fallback_result
            except TelebirrVerificationError:
                continue

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

    async def _fetch_from_proxy_async(self, reference: str, proxy_base: str) -> TelebirrReceipt | None:
        url = self._proxy_url(proxy_base, reference)
        try:
            response = await self.http.request_async(
                "GET",
                url,
                timeout=30.0,
                retries=0,
                raise_for_status=False,
                headers={
                    "Accept": "application/json",
                },
            )
            return self._parse_proxy_response(response.text)
        except Exception as exc:
            raise TelebirrVerificationError(
                "The fallback proxy server is unreachable or timed out.",
                str(exc),
            ) from exc

    def _fetch_from_proxy_sync(self, reference: str, proxy_base: str) -> TelebirrReceipt | None:
        url = self._proxy_url(proxy_base, reference)
        try:
            response = self.http.request_sync(
                "GET",
                url,
                timeout=30.0,
                retries=0,
                raise_for_status=False,
                headers={
                    "Accept": "application/json",
                },
            )
            return self._parse_proxy_response(response.text)
        except Exception as exc:
            raise TelebirrVerificationError(
                "The fallback proxy server is unreachable or timed out.",
                str(exc),
            ) from exc

    @staticmethod
    def _proxy_url(proxy_base: str, reference: str) -> str:
        if "{reference}" in proxy_base:
            return proxy_base.format(reference=reference)
        return f"{proxy_base}{reference}"

    @staticmethod
    def _parse_proxy_response(response_text: str) -> TelebirrReceipt | None:
        try:
            payload = json.loads(response_text)
            if isinstance(payload, dict):
                if payload.get("success") is False and payload.get("error"):
                    raise TelebirrVerificationError(str(payload["error"]), str(payload.get("details")))

                parsed_json = parse_telebirr_json(payload)
                if parsed_json is not None:
                    return parsed_json
        except json.JSONDecodeError:
            pass

        return parse_telebirr_html(response_text)
