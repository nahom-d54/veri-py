# Agent notes (veri-py)

Guidance for AI coding agents and automation working in this repository.

## Project

- **Package:** `veri-py` — typed Python toolkit for Ethiopian payment receipt verification (CBE, Telebirr, Dashen, Abyssinia, CBE Birr, M-Pesa) and image-based detection.
- **Python:** 3.12+ (`requires-python` in [`pyproject.toml`](pyproject.toml)).
- **Layout:** Hatch build; code under [`src/veri_py/`](src/veri_py/), tests under [`tests/`](tests/).

## Commands (local)

```bash
pip install -e ".[dev]"
pytest -q
ruff check src tests
mypy src
```

Optional extras: `browser` (Playwright), `socks`, `ocr` — see README.

## Conventions

- Prefer extending existing clients, HTTP helpers, and parsers over duplicating logic.
- `VerifierSettings` / env vars for configuration; keep provider-specific URLs in config when they are user-overridable.
- Async entry points use `AsyncVerifierClient`; sync uses `VerifierClient`.

## CI

- **`.github/workflows/ci.yml`** — runs on pushes and pull requests targeting `master`: Ruff, Mypy, pytest on Python 3.12 and 3.13.
- **`.github/workflows/publish-pypi.yml`** — runs when a tag matching `v*` is pushed; builds with `python -m build` and publishes with [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish).

## PyPI releases

1. Bump `version` in [`pyproject.toml`](pyproject.toml) to match the release.
2. Tag: `git tag vX.Y.Z` and push the tag. The publish workflow uploads to PyPI.
3. Configure **trusted publishing** on PyPI for this GitHub repo (recommended): see [PyPI trusted publishers](https://docs.pypi.org/trusted-publishers/). If the package lives inside a monorepo subdirectory, workflows may need to live at the repository root with an appropriate `working-directory` or path filters.

## Related docs

- [`README.md`](README.md) — user-facing API, configuration, and behavior.
- [`CONTRIBUTORS.md`](CONTRIBUTORS.md) — contribution process.
