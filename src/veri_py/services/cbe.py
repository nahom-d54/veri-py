"""Commercial Bank of Ethiopia (CBE) verification service."""

from __future__ import annotations

from ..core.config import DirectServiceProxyMode, VerifierSettings
from ..core.http import HTTPClient
from ..core.playwright_proxy import playwright_proxy_from_url
from ..models import VerifyResult
from ..parsers.pdf import extract_pdf_text, parse_cbe_receipt_text


class CBEService:
    """Verify CBE transaction receipts via direct PDF fetch + optional browser fallback."""

    def __init__(self, http_client: HTTPClient, settings: VerifierSettings) -> None:
        self.http = http_client
        self.settings = settings

    async def verify(self, reference: str, account_suffix: str) -> VerifyResult:
        """Verify CBE transaction asynchronously."""
        full_id = f"{reference}{account_suffix}"
        url = self.settings.cbe_primary_base_url

        params = {"id": full_id}

        try:
            pdf_bytes = await self.http.get_bytes_async(
                url,
                verify_tls=False,
                timeout=30.0,
                retries=0,
                headers={
                    "Accept": "application/pdf",
                },
                params=params,
            )
            return parse_cbe_receipt_text(extract_pdf_text(pdf_bytes))
        except Exception as direct_error:
            if not self.settings.enable_cbe_browser_fallback:
                return VerifyResult(success=False, error=f"Direct fetch failed: {direct_error}")

        try:
            fallback_pdf_bytes = await self._fetch_pdf_with_playwright_async(url)
            if not fallback_pdf_bytes:
                return VerifyResult(success=False, error="No PDF detected via browser fallback.")
            return parse_cbe_receipt_text(extract_pdf_text(fallback_pdf_bytes))
        except Exception as browser_error:
            return VerifyResult(success=False, error=f"Both direct and browser fallback failed: {browser_error}")

    def verify_sync(self, reference: str, account_suffix: str) -> VerifyResult:
        """Verify CBE transaction synchronously."""
        full_id = f"{reference}{account_suffix}"
        url = self.settings.cbe_primary_base_url
        params = {"id": full_id}

        try:
            pdf_bytes = self.http.get_bytes_sync(
                url,
                verify_tls=False,
                timeout=30.0,
                retries=0,
                headers={
                    "Accept": "application/pdf",
                },
                params=params,
            )
            return parse_cbe_receipt_text(extract_pdf_text(pdf_bytes))
        except Exception as direct_error:
            if not self.settings.enable_cbe_browser_fallback:
                return VerifyResult(success=False, error=f"Direct fetch failed: {direct_error}")

        try:
            fallback_pdf_bytes = self._fetch_pdf_with_playwright_sync(url)
            if not fallback_pdf_bytes:
                return VerifyResult(success=False, error="No PDF detected via browser fallback.")
            return parse_cbe_receipt_text(extract_pdf_text(fallback_pdf_bytes))
        except Exception as browser_error:
            return VerifyResult(success=False, error=f"Both direct and browser fallback failed: {browser_error}")

    async def _fetch_pdf_with_playwright_async(self, url: str) -> bytes | None:
        """Fetch PDF using Playwright async API when direct fetch is blocked."""
        proxy_url = self.settings.network_proxy_url
        mode = self.settings.direct_service_proxy_mode

        if not proxy_url or mode == DirectServiceProxyMode.ALWAYS_PROXY:
            mapped = playwright_proxy_from_url(proxy_url) if proxy_url else None
            return await self._run_playwright_async(url, mapped)

        try:
            return await self._run_playwright_async(url, None)
        except Exception:
            return await self._run_playwright_async(url, playwright_proxy_from_url(proxy_url))

    def _fetch_pdf_with_playwright_sync(self, url: str) -> bytes | None:
        """Fetch PDF using Playwright sync API when direct fetch is blocked."""
        proxy_url = self.settings.network_proxy_url
        mode = self.settings.direct_service_proxy_mode

        if not proxy_url or mode == DirectServiceProxyMode.ALWAYS_PROXY:
            mapped = playwright_proxy_from_url(proxy_url) if proxy_url else None
            return self._run_playwright_sync(url, mapped)

        try:
            return self._run_playwright_sync(url, None)
        except Exception:
            return self._run_playwright_sync(url, playwright_proxy_from_url(proxy_url))

    async def _run_playwright_async(self, url: str, proxy: dict[str, str] | None) -> bytes | None:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is not installed. Install with: pip install veri-py[browser]") from exc

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                context = await browser.new_context(ignore_https_errors=True, proxy=proxy)
                page = await context.new_page()
                response = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(6000)

                if response is not None:
                    content_type = response.headers.get("content-type", "")
                    if "pdf" in content_type.lower():
                        return await response.body()
                return None
            finally:
                await browser.close()

    def _run_playwright_sync(self, url: str, proxy: dict[str, str] | None) -> bytes | None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is not installed. Install with: pip install veri-py[browser]") from exc

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                ctx_kw: dict[str, object] = {"ignore_https_errors": True}
                if proxy:
                    ctx_kw["proxy"] = proxy
                context = browser.new_context(**ctx_kw)
                page = context.new_page()
                response = page.goto(url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(6000)

                if response is not None:
                    content_type = response.headers.get("content-type", "")
                    if "pdf" in content_type.lower():
                        return response.body()
                return None
            finally:
                browser.close()
