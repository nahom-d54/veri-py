"""M-Pesa verification service."""

from __future__ import annotations

import base64
from typing import Any

from ..core.config import VerifierSettings
from ..core.http import HTTPClient
from ..exceptions import VerifierError
from ..models import MpesaVerifyResult
from ..parsers.pdf import extract_pdf_text, parse_mpesa_receipt_text


class MpesaService:
    """Verify M-Pesa transactions against the primary endpoint only."""

    def __init__(self, http_client: HTTPClient, settings: VerifierSettings) -> None:
        self.http = http_client
        self.settings = settings

    async def verify(self, transaction_id: str) -> MpesaVerifyResult:
        """Verify M-Pesa transaction asynchronously.

        Raises:
            VerifierError: If the request times out or transport fails.
        """
        url = self.settings.mpesa_primary_base_url

        params = {"trxNo": transaction_id}
        try:
            data = await self._fetch_json_async(url, params=params)
        except Exception as exc:
            raise VerifierError(f"M-Pesa request failed (timeout/transport): {exc}") from exc

        if data.get("responseCode") != "0" or not data.get("base64Data"):
            return MpesaVerifyResult(
                success=False,
                error=f"API Error: {data.get('responseDescription', 'Unknown error')}",
            )

        try:
            pdf_bytes = base64.b64decode(str(data["base64Data"]))
            return parse_mpesa_receipt_text(extract_pdf_text(pdf_bytes))
        except Exception as exc:
            return MpesaVerifyResult(success=False, error=f"Failed to process PDF data: {exc}")

    def verify_sync(self, transaction_id: str) -> MpesaVerifyResult:
        """Verify M-Pesa transaction synchronously.

        Raises:
            VerifierError: If the request times out or transport fails.
        """
        url = self.settings.mpesa_primary_base_url

        params = {"trxNo": transaction_id}
        try:
            data = self._fetch_json_sync(url, params=params)
        except Exception as exc:
            raise VerifierError(f"M-Pesa request failed (timeout/transport): {exc}") from exc

        if data.get("responseCode") != "0" or not data.get("base64Data"):
            return MpesaVerifyResult(
                success=False,
                error=f"API Error: {data.get('responseDescription', 'Unknown error')}",
            )

        try:
            pdf_bytes = base64.b64decode(str(data["base64Data"]))
            return parse_mpesa_receipt_text(extract_pdf_text(pdf_bytes))
        except Exception as exc:
            return MpesaVerifyResult(success=False, error=f"Failed to process PDF data: {exc}")

    async def _fetch_json_async(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        payload = await self.http.get_json_async(
            url,
            timeout=60.0,
            retries=0,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://m-pesabusiness.safaricom.et/",
            },
            params=params,
        )
        if not isinstance(payload, dict):
            raise VerifierError("M-Pesa API returned non-object JSON payload")
        return payload

    def _fetch_json_sync(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        payload = self.http.get_json_sync(
            url,
            timeout=60.0,
            retries=0,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://m-pesabusiness.safaricom.et/",
            },
            params=params,
        )
        if not isinstance(payload, dict):
            raise VerifierError("M-Pesa API returned non-object JSON payload")
        return payload
