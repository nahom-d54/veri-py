# veri-py

Typed Python toolkit for verifying Ethiopian payment receipts: **CBE**, **Telebirr**, **Dashen**, **Bank of Abyssinia**, **CBE Birr**, **M-Pesa**, plus **image-based** receipt detection and optional auto-verification. The API mirrors the Node/TypeScript [verifier-api](https://github.com/Vixen878/verifier-api) service layer so integrations can share similar contracts.

**Requirements:** Python 3.12+

---

## Contents

- [Features](#features)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Public API](#public-api)
- [Configuration](#configuration)
- [Networking and proxies](#networking-and-proxies)
- [Image verification (vision)](#image-verification-vision)
- [Provider-specific notes](#provider-specific-notes)
- [Models and errors](#models-and-errors)
- [Advanced usage](#advanced-usage)
- [Development](#development)
- [Publishing](#publishing)
- [License](#license)

---

## Features

| Capability | Description |
|------------|-------------|
| **Pydantic models** | Request/response types aligned with the TS API (`VerifyResult`, `TelebirrReceipt`, `DashenVerifyResult`, etc.). |
| **Async and sync** | `AsyncVerifierClient` for `asyncio` apps; `VerifierClient` for scripts and blocking code. |
| **Environment or code config** | `VerifierSettings` via `.env`, environment variables, or explicit constructor arguments. |
| **Direct-service HTTP** | Shared `httpx` client with retries, TLS options, and configurable **outbound proxy** behavior. |
| **Vision** | OpenAI-compatible chat completions with **structured output** (`ImageDetectionResult`); not routed through the verification proxy. |

---

## Installation

**From PyPI**

```bash
pip install veri-py
```

**Editable install** (from this directory)

```bash
pip install -e .
```

### Optional extras

| Extra | Purpose |
|-------|---------|
| `socks` | Installs `httpx[socks]` so `VERI_PROXY_URL` can use `socks5://` (and similar) for **verification** HTTP traffic. |
| `browser` | [Playwright](https://playwright.dev/python/) for CBE PDF fetch when the direct HTTP download fails (`CBE_BROWSER_FALLBACK`). |
| `ocr` | Pillow, for extending image handling if you build on top of the package. |
| `dev` | Tests (`pytest`, `respx`), `ruff`, `mypy`, `build`, `twine`. |

```bash
pip install veri-py[browser,socks]
pip install -e ".[dev]"   # local development
```

---

## Quick start

### Async

```python
import asyncio
from veri_py import AsyncVerifierClient

async def main() -> None:
    client = AsyncVerifierClient()
    result = await client.verify_cbe(reference="FT2513001V2G", account_suffix="39003377")
    print(result)

asyncio.run(main())
```

### Sync

```python
from veri_py import VerifierClient

client = VerifierClient()
receipt = client.verify_telebirr(reference="CE2513001XYT")
print(receipt)
```

### Explicit settings (no `.env` required)

```python
from veri_py import AsyncVerifierClient, VerifierSettings

settings = VerifierSettings(
    openai_api_key="sk-...",  # required for verify_image
    openai_base_url="https://api.openai.com/v1",
    openai_vision_model="gpt-4o-mini",
)
client = AsyncVerifierClient(settings)
```

Constructor shortcuts merge into the resolved settings:

```python
from veri_py import AsyncVerifierClient, DirectServiceProxyMode

client = AsyncVerifierClient(
    proxy="http://proxy.example.com:8080",
    direct_service_proxy_mode=DirectServiceProxyMode.RETRY_WITH_PROXY,
)
```

---

## Public API

### `AsyncVerifierClient` / `VerifierClient`

Both expose the same verification methods; async methods are `await`ed on `AsyncVerifierClient`, and sync counterparts are used on `VerifierClient`.

| Method | Arguments | Returns (success path) |
|--------|-------------|-------------------------|
| `verify_cbe` | `reference`, `account_suffix` | `VerifyResult` |
| `verify_telebirr` | `reference` | `TelebirrReceipt \| None` |
| `verify_dashen` | `reference` (transaction ref) | `DashenVerifyResult` |
| `verify_abyssinia` | `reference`, `suffix` | `VerifyResult` |
| `verify_cbebirr` | `receipt_number`, `phone_number`, `api_key` | `CBEBirrReceipt \| CBEBirrError` |
| `verify_mpesa` | `transaction_id` | `MpesaVerifyResult` |
| `verify_image` | `image_bytes`, `auto_verify=False`, `account_suffix=None` | `ImageAutoVerifyResult \| ImageForwardResult \| ImageErrorResult` |

**`verify_image`**

- `auto_verify=False`: returns routing hints (`ImageForwardResult`) or errors (`ImageErrorResult`).
- `auto_verify=True`: after detection, calls Telebirr or CBE verification as appropriate. For CBE, **`account_suffix`** is required.

Each client also exposes:

- `settings: VerifierSettings` — resolved configuration.
- `*_service` attributes (e.g. `cbe_service`, `telebirr_service`) for lower-level access; see [Advanced usage](#advanced-usage).

---

## Configuration

Settings are defined in [`VerifierSettings`](https://github.com/Vixen878/verifier-api/blob/main/veri-py/src/veri_py/core/config.py) (`pydantic-settings`). Values load from the process environment and optional `.env` (case-insensitive keys). You can override by passing a `VerifierSettings` instance or by using `AsyncVerifierClient(..., proxy=..., direct_service_proxy_mode=...)`.

### Environment variables (reference)

#### HTTP transport (all direct verification requests)

| Variable | Default | Description |
|----------|---------|---------------|
| `VERI_REQUEST_TIMEOUT_SECONDS` | `30` | Per-request timeout (seconds). |
| `VERI_REQUEST_RETRIES` | `2` | Retries **within** a single proxy phase (direct-only or proxy-only), with backoff. |
| `VERI_RETRY_DELAY_SECONDS` | `0.75` | Backoff multiplier base between retries. |
| `VERI_VERIFY_TLS` | `true` | TLS certificate verification for httpx (per-request overrides exist where services need it). |
| `VERI_USER_AGENT` | Chrome-like string | Default `User-Agent` header. |

#### Outbound proxy (direct services only, not vision)

| Variable | Default | Description |
|----------|---------|---------------|
| `VERI_PROXY_URL` | *(empty)* | HTTP(S) or SOCKS proxy URL for **verification** traffic (install `veri-py[socks]` for SOCKS). |
| `VERI_DIRECT_SERVICE_PROXY_MODE` | `always_proxy` | `always_proxy` or `retry_with_proxy`. See [Networking and proxies](#networking-and-proxies). |

#### Provider base URLs

Override only if endpoints change or you use test doubles.

| Variable | Purpose |
|----------|---------|
| `TELEBIRR_PRIMARY_BASE_URL` | Telebirr primary receipt page base. |
| `MPESA_PRIMARY_BASE_URL` | M-Pesa receipt API base. |
| `DASHEN_PRIMARY_BASE_URL` | Dashen receipt PDF base. |
| `ABYSSINIA_PRIMARY_BASE_URL` | Abyssinia JSON API base. |
| `CBEBIRR_PRIMARY_BASE_URL` | CBE Birr PDF base. |
| `CBE_PRIMARY_BASE_URL` | CBE transaction PDF base. |

#### Vision (OpenAI-compatible)

| Variable | Default | Description |
|----------|---------|---------------|
| `VERI_OPENAI_API_KEY` | *(none)* | API key for `verify_image` (or dummy value if your server ignores auth). |
| `VERI_OPENAI_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible server implementing the same chat + structured-parse flow. |
| `VERI_OPENAI_VISION_MODEL` | `gpt-4o-mini` | Vision-capable model name on that server. |

#### CBE browser fallback

| Variable | Default | Description |
|----------|---------|---------------|
| `CBE_BROWSER_FALLBACK` | `false` | If `true`, after failed direct PDF fetch, use Playwright (`veri-py[browser]`). Proxy behavior follows `VERI_DIRECT_SERVICE_PROXY_MODE`. |

---

## Networking and proxies

Two mechanisms interact; they are **not** interchangeable:

1. **`VERI_PROXY_URL` + `VERI_DIRECT_SERVICE_PROXY_MODE`** — Applies to **httpx** traffic to banks/M-Pesa/etc., and to **Playwright** when browser fallback runs. **Does not** apply to the OpenAI SDK used for `verify_image`.

2. **Vision** — Uses the default OpenAI client connection to `VERI_OPENAI_BASE_URL` (no package-level HTTP proxy).

### `DirectServiceProxyMode`

| Mode | When `VERI_PROXY_URL` is set |
|------|-------------------------------|
| **`always_proxy`** (default) | Every direct-service request uses the proxy from the first attempt. |
| **`retry_with_proxy`** | First run the full retry sequence **without** a proxy. If it fails with **timeout or transport error**, the same logical request runs again **with** the proxy. **`HTTPStatusError` (4xx/5xx)** is not switched to the proxy path; it propagates after inner retries. |

M-Pesa uses the **primary** endpoint only; if it fails, the service surfaces an error rather than a separate fallback chain.

---

## Image verification (vision)

`verify_image` sends the image to the configured OpenAI-compatible API and parses a structured [`ImageDetectionResult`](https://github.com/Vixen878/verifier-api/blob/main/veri-py/src/veri_py/models.py) (receipt type: Telebirr vs CBE, plus transaction id/number fields). Your server must support the SDK’s structured parse path used in code (`beta.chat.completions.parse` with a Pydantic model).

---

## Provider-specific notes

| Provider | Behavior |
|----------|----------|
| **CBE** | Fetches a PDF by reference + account suffix; parses text. Optional Playwright fallback if `CBE_BROWSER_FALLBACK` and `[browser]` installed. |
| **Telebirr** | Primary Ethio Telecom receipt HTML page. |
| **Dashen** | PDF download with internal retry loop. |
| **Abyssinia** | JSON API with field mapping to `VerifyResult`. |
| **CBE Birr** | PDF with bearer `api_key` per request. |
| **M-Pesa** | Primary JSON API only. |

---

## Models and errors

- **Models:** [`veri_py.models`](https://github.com/Vixen878/verifier-api/blob/main/veri-py/src/veri_py/models.py) — result types, image flow types, and optional request DTOs (`CBERequest`, `TelebirrRequest`, …) for validation at your API boundary.
- **Exceptions:** [`veri_py.exceptions`](https://github.com/Vixen878/verifier-api/blob/main/veri-py/src/veri_py/exceptions.py) — `VerifierError`, `ConfigurationError`, `ParsingError`, `TelebirrVerificationError`.

---

## Advanced usage

### Services and parsers

For custom flows you can use service classes from `veri_py.services` and parsers from `veri_py.parsers` with your own `HTTPClient` and `VerifierSettings`. The package layout:

```text
veri_py/
  core/
    config.py          # VerifierSettings, DirectServiceProxyMode
    http.py            # HTTPClient (retries + proxy modes)
    playwright_proxy.py
  parsers/
    common.py
    pdf.py
    telebirr.py
  services/
    abyssinia.py
    cbe.py
    cbebirr.py
    dashen.py
    image.py
    mpesa.py
    telebirr.py
  client.py
  models.py
  exceptions.py
```

### Imports

```python
from veri_py import (
    AsyncVerifierClient,
    VerifierClient,
    VerifierSettings,
    DirectServiceProxyMode,
)
from veri_py.exceptions import ConfigurationError, VerifierError
```

---

## Development

```bash
cd veri-py
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src
```

---

## Publishing

Maintainers can build and upload wheels/sdists after `twine` and `build` are available (included in `[dev]`):

```bash
cd veri-py
python -m build
twine check dist/*
twine upload dist/*
```

Use [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) or API tokens as recommended.

---

## License

MIT. See [`LICENSE`](LICENSE) in this directory.
