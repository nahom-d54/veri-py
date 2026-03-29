"""Common parser utilities shared by provider parsers."""

from __future__ import annotations

from datetime import datetime


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace while preserving semantic content."""
    return " ".join(text.split())


def title_case(value: str | None) -> str | None:
    """Convert string to title case; preserve None."""
    if value is None:
        return None
    return value.lower().title().strip()


def parse_amount(value: str | None) -> float | None:
    """Parse currency-like numeric strings into float values."""
    if not value:
        return None
    cleaned = value.replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_datetime_flexible(value: str | None) -> datetime | None:
    """Parse dates from multiple known provider formats."""
    if not value:
        return None

    candidate = value.strip()
    patterns = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%m/%d/%Y, %I:%M:%S %p",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
    ]

    for pattern in patterns:
        try:
            return datetime.strptime(candidate, pattern)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None
