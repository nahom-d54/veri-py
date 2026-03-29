"""Dashen verification service."""

from __future__ import annotations

import asyncio
import time

from ..core.config import VerifierSettings
from ..core.http import HTTPClient
from ..models import DashenVerifyResult
from ..parsers.pdf import extract_pdf_text, parse_dashen_receipt_text


class DashenService:
    """Verify Dashen receipt references with retry behavior aligned to TS service."""

    def __init__(self, http_client: HTTPClient, settings: VerifierSettings) -> None:
        self.http = http_client
        self.settings = settings

    async def verify(self, transaction_reference: str) -> DashenVerifyResult:
        """Verify Dashen transaction asynchronously."""
        url = f"{self.settings.dashen_primary_base_url}{transaction_reference}"
        max_retries = 5
        retry_delay_seconds = 2

        for attempt in range(1, max_retries + 1):
            try:
                pdf_bytes = await self.http.get_bytes_async(
                    url,
                    verify_tls=False,
                    timeout=60.0,
                    retries=0,
                    headers={"Accept": "application/pdf"},
                )
                return parse_dashen_receipt_text(extract_pdf_text(pdf_bytes))
            except Exception as exc:
                if attempt == max_retries:
                    return DashenVerifyResult(
                        success=False,
                        error=f"Failed to fetch receipt after {max_retries} attempts: {exc}",
                    )
                await asyncio.sleep(retry_delay_seconds)

        return DashenVerifyResult(success=False, error="Unknown error in retry loop")

    def verify_sync(self, transaction_reference: str) -> DashenVerifyResult:
        """Verify Dashen transaction synchronously."""
        url = f"{self.settings.dashen_primary_base_url}{transaction_reference}"
        max_retries = 5
        retry_delay_seconds = 2

        for attempt in range(1, max_retries + 1):
            try:
                pdf_bytes = self.http.get_bytes_sync(
                    url,
                    verify_tls=False,
                    timeout=60.0,
                    retries=0,
                    headers={"Accept": "application/pdf"},
                )
                return parse_dashen_receipt_text(extract_pdf_text(pdf_bytes))
            except Exception as exc:
                if attempt == max_retries:
                    return DashenVerifyResult(
                        success=False,
                        error=f"Failed to fetch receipt after {max_retries} attempts: {exc}",
                    )
                time.sleep(retry_delay_seconds)

        return DashenVerifyResult(success=False, error="Unknown error in retry loop")
