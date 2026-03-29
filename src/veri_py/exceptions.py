"""Custom exceptions used by veri-py services."""


class VerifierError(Exception):
    """Base exception for verification operations."""


class ConfigurationError(VerifierError):
    """Raised when required settings are missing or invalid."""


class ParsingError(VerifierError):
    """Raised when receipt parsing fails irrecoverably."""


class TelebirrVerificationError(VerifierError):
    """Raised when Telebirr fallback proxy returns explicit transport-level failure."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.details = details
