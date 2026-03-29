"""CBE Birr verification service."""

from __future__ import annotations

from ..core.config import VerifierSettings
from ..core.http import HTTPClient
from ..models import CBEBirrError, CBEBirrReceipt
from ..parsers.pdf import extract_pdf_text, parse_cbebirr_receipt_text


class CBEBirrService:
    """Verify CBE Birr receipts by TID + phone + API key."""

    def __init__(self, http_client: HTTPClient, settings: VerifierSettings) -> None:
        self.http = http_client
        self.settings = settings

    async def verify(self, receipt_number: str, phone_number: str, api_key: str) -> CBEBirrReceipt | CBEBirrError:
        """Verify CBE Birr receipt asynchronously."""
        url = self.settings.cbebirr_primary_base_url

        params = {"TID": f"{receipt_number}", "PH": f"{phone_number}"}
        try:
            pdf_bytes = await self.http.get_bytes_async(
                url,
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/pdf",
                },
                retries=1,
                params=params,
            )
            parsed = parse_cbebirr_receipt_text(extract_pdf_text(pdf_bytes))
            if parsed is None:
                return CBEBirrError(error="Failed to parse receipt data from PDF")
            return parsed
        except Exception as exc:
            return CBEBirrError(error=str(exc))

    def verify_sync(self, receipt_number: str, phone_number: str, api_key: str) -> CBEBirrReceipt | CBEBirrError:
        """Verify CBE Birr receipt synchronously."""
        url = self.settings.cbebirr_primary_base_url

        params = {"TID": f"{receipt_number}", "PH": f"{phone_number}"}

        try:
            pdf_bytes = self.http.get_bytes_sync(
                url,
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/pdf",
                },
                retries=1,
                params=params,
            )
            parsed = parse_cbebirr_receipt_text(extract_pdf_text(pdf_bytes))
            if parsed is None:
                return CBEBirrError(error="Failed to parse receipt data from PDF")
            return parsed
        except Exception as exc:
            return CBEBirrError(error=str(exc))
