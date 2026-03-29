"""Shared HTTP transport with sync/async helpers and retry support."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from .config import DirectServiceProxyMode, VerifierSettings


class HTTPClient:
    """Transport helper used by all services for consistent request behavior."""

    def __init__(self, settings: VerifierSettings) -> None:
        self.settings = settings

    async def request_async(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
        retries: int | None = None,
        verify_tls: bool | None = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """Execute an async HTTP request with bounded retries."""
        attempts = (retries if retries is not None else self.settings.request_retries) + 1
        proxy_url = self.settings.network_proxy_url
        mode = self.settings.direct_service_proxy_mode

        if not proxy_url or mode == DirectServiceProxyMode.ALWAYS_PROXY:
            return await self._request_async_attempts(
                method,
                url,
                proxy=proxy_url,
                attempts=attempts,
                headers=headers,
                json_body=json_body,
                params=params,
                timeout=timeout,
                verify_tls=verify_tls,
                raise_for_status=raise_for_status,
            )

        try:
            return await self._request_async_attempts(
                method,
                url,
                proxy=None,
                attempts=attempts,
                headers=headers,
                json_body=json_body,
                params=params,
                timeout=timeout,
                verify_tls=verify_tls,
                raise_for_status=raise_for_status,
            )
        except httpx.HTTPStatusError:
            raise
        except (httpx.TimeoutException, httpx.TransportError):
            return await self._request_async_attempts(
                method,
                url,
                proxy=proxy_url,
                attempts=attempts,
                headers=headers,
                json_body=json_body,
                params=params,
                timeout=timeout,
                verify_tls=verify_tls,
                raise_for_status=raise_for_status,
            )

    async def _request_async_attempts(
        self,
        method: str,
        url: str,
        *,
        proxy: str | None,
        attempts: int,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
        verify_tls: bool | None = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=timeout or self.settings.request_timeout_seconds,
                    verify=self.settings.verify_tls if verify_tls is None else verify_tls,
                    proxy=proxy,
                    follow_redirects=True,
                    headers={
                        "User-Agent": self.settings.user_agent,
                        **(headers or {}),
                    },
                ) as client:
                    response = await client.request(method=method, url=url, json=json_body, params=params)
                    if raise_for_status:
                        response.raise_for_status()
                    return response
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt >= attempts:
                    raise
                await asyncio.sleep(self.settings.request_retry_delay_seconds * attempt)

        if last_error is not None:
            raise last_error
        raise RuntimeError("request_async failed without an explicit exception")

    def request_sync(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
        retries: int | None = None,
        verify_tls: bool | None = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """Execute a sync HTTP request with bounded retries."""
        attempts = (retries if retries is not None else self.settings.request_retries) + 1
        proxy_url = self.settings.network_proxy_url
        mode = self.settings.direct_service_proxy_mode

        if not proxy_url or mode == DirectServiceProxyMode.ALWAYS_PROXY:
            return self._request_sync_attempts(
                method,
                url,
                proxy=proxy_url,
                attempts=attempts,
                headers=headers,
                json_body=json_body,
                params=params,
                timeout=timeout,
                verify_tls=verify_tls,
                raise_for_status=raise_for_status,
            )

        try:
            return self._request_sync_attempts(
                method,
                url,
                proxy=None,
                attempts=attempts,
                headers=headers,
                json_body=json_body,
                params=params,
                timeout=timeout,
                verify_tls=verify_tls,
                raise_for_status=raise_for_status,
            )
        except httpx.HTTPStatusError:
            raise
        except (httpx.TimeoutException, httpx.TransportError):
            return self._request_sync_attempts(
                method,
                url,
                proxy=proxy_url,
                attempts=attempts,
                headers=headers,
                json_body=json_body,
                params=params,
                timeout=timeout,
                verify_tls=verify_tls,
                raise_for_status=raise_for_status,
            )

    def _request_sync_attempts(
        self,
        method: str,
        url: str,
        *,
        proxy: str | None,
        attempts: int,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
        verify_tls: bool | None = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(
                    timeout=timeout or self.settings.request_timeout_seconds,
                    verify=self.settings.verify_tls if verify_tls is None else verify_tls,
                    proxy=proxy,
                    follow_redirects=True,
                    headers={
                        "User-Agent": self.settings.user_agent,
                        **(headers or {}),
                    },
                ) as client:
                    response = client.request(method=method, url=url, json=json_body, params=params)
                    if raise_for_status:
                        response.raise_for_status()
                    return response
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt >= attempts:
                    raise
                time.sleep(self.settings.request_retry_delay_seconds * attempt)

        if last_error is not None:
            raise last_error
        raise RuntimeError("request_sync failed without an explicit exception")

    async def get_json_async(self, url: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        """GET JSON asynchronously."""
        response = await self.request_async("GET", url, **kwargs)
        return response.json()

    async def get_text_async(self, url: str, **kwargs: Any) -> str:
        """GET text asynchronously."""
        response = await self.request_async("GET", url, **kwargs)
        return response.text

    async def get_bytes_async(self, url: str, **kwargs: Any) -> bytes:
        """GET binary payload asynchronously."""
        response = await self.request_async("GET", url, **kwargs)
        return response.content

    async def post_json_async(
        self,
        url: str,
        json_body: dict[str, Any] | list[Any],
        **kwargs: Any,
    ) -> dict[str, Any] | list[Any]:
        """POST JSON asynchronously and parse JSON response."""
        response = await self.request_async("POST", url, json_body=json_body, **kwargs)
        return response.json()

    def get_json_sync(self, url: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        """GET JSON synchronously."""
        response = self.request_sync("GET", url, **kwargs)
        return response.json()

    def get_text_sync(self, url: str, **kwargs: Any) -> str:
        """GET text synchronously."""
        response = self.request_sync("GET", url, **kwargs)
        return response.text

    def get_bytes_sync(self, url: str, **kwargs: Any) -> bytes:
        """GET binary payload synchronously."""
        response = self.request_sync("GET", url, **kwargs)
        return response.content

    def post_json_sync(
        self,
        url: str,
        json_body: dict[str, Any] | list[Any],
        **kwargs: Any,
    ) -> dict[str, Any] | list[Any]:
        """POST JSON synchronously and parse JSON response."""
        response = self.request_sync("POST", url, json_body=json_body, **kwargs)
        return response.json()
