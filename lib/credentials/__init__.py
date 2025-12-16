"""
Credential Validation Framework

Validates that required credentials are available before agent execution begins.
Supports multiple credential sources and fail-fast behavior.

Usage:
    from lib.credentials import CredentialValidator, CredentialSpec

    validator = CredentialValidator()

    # Define required credentials
    validator.require("AWS_ACCESS_KEY_ID", source="env", required=True)
    validator.require("SLACK_BOT_TOKEN", source="env", required=False)  # Optional

    # Validate all
    result = validator.validate()
    if not result.valid:
        print(f"Missing: {result.missing}")
        sys.exit(1)
"""

from .validator import CredentialValidator, CredentialSpec, ValidationResult

__all__ = [
    "CredentialValidator",
    "CredentialSpec",
    "ValidationResult",
]
