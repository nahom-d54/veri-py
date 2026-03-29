"""Bank of Abyssinia verification service."""

from __future__ import annotations

from typing import Any

from ..core.config import VerifierSettings
from ..core.http import HTTPClient
from ..models import VerifyResult
from ..parsers.common import parse_amount, parse_datetime_flexible


class AbyssiniaService:
    """Fetch and map Abyssinia JSON receipt details."""

    def __init__(self, http_client: HTTPClient, settings: VerifierSettings) -> None:
        self.http = http_client
        self.settings = settings

    async def verify(self, reference: str, suffix: str) -> VerifyResult:
        """Verify Abyssinia transaction asynchronously."""
        url = self.settings.abyssinia_primary_base_url
        params = {"id": f"{reference}{suffix}"}
        try:
            payload = await self.http.get_json_async(
                url,
                timeout=30.0,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
                retries=1,
                params=params,
            )
        except Exception:
            return VerifyResult(success=False, error="Failed to verify Abyssinia transaction")

        return self._map_payload(payload)

    def verify_sync(self, reference: str, suffix: str) -> VerifyResult:
        """Verify Abyssinia transaction synchronously."""
        url = self.settings.abyssinia_primary_base_url
        params = {"id": f"{reference}{suffix}"}
        try:
            payload = self.http.get_json_sync(
                url,
                timeout=30.0,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
                retries=1,
                params=params,
            )
        except Exception:
            return VerifyResult(success=False, error="Failed to verify Abyssinia transaction")

        return self._map_payload(payload)

    def _map_payload(self, payload: dict[str, Any] | list[Any]) -> VerifyResult:
        if not isinstance(payload, dict):
            return VerifyResult(success=False, error="Invalid response structure from Abyssinia API")

        header = payload.get("header")
        body = payload.get("body")

        if not isinstance(header, dict) or not isinstance(body, list):
            return VerifyResult(success=False, error="Invalid response structure from Abyssinia API")

        if header.get("status") != "success":
            return VerifyResult(success=False, error=f"API returned error status: {header.get('status')}")

        if not body:
            return VerifyResult(success=False, error="No transaction data found in response body")

        transaction = body[0] if isinstance(body[0], dict) else {}

        result = VerifyResult(
            success=True,
            payer=transaction.get("Payer's Name"),
            payerAccount=transaction.get("Source Account"),
            receiver=transaction.get("Source Account Name"),
            receiverAccount=None,
            amount=parse_amount(str(transaction.get("Transferred Amount", "")).replace("ETB", "").strip()),
            date=parse_datetime_flexible(transaction.get("Transaction Date")),
            reference=transaction.get("Transaction Reference"),
            reason=transaction.get("Narrative") or None,
        )

        if not result.reference or result.amount is None or not result.payer:
            return VerifyResult(success=False, error="Missing essential fields in transaction data")

        return result
