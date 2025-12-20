"""
Credential Validator
====================

Validate harness credentials using functional, composable checks.
"""

from dataclasses import dataclass
from typing import Callable

from .types import HarnessCredentials
from ..core.types import ValidationLevel


@dataclass(frozen=True)
class CredentialCheckResult:
    """Result of a single credential check."""
    passed: bool
    message: str
    level: ValidationLevel = ValidationLevel.INFO

    def __str__(self) -> str:
        prefix = {
            ValidationLevel.ERROR: "[ERROR]",
            ValidationLevel.WARNING: "[WARN]",
            ValidationLevel.INFO: "[OK]",
        }[self.level]
        return f"{prefix} {self.message}"


# Individual check functions (pure, composable)

def check_aws(creds: HarnessCredentials) -> CredentialCheckResult:
    """Check if AWS credentials are configured."""
    if creds.has_aws_profile():
        return CredentialCheckResult(
            passed=True,
            message=f"AWS configured via profile: {creds.aws_profile}",
            level=ValidationLevel.INFO
        )
    elif creds.has_aws_keys():
        return CredentialCheckResult(
            passed=True,
            message=f"AWS configured via access keys (region: {creds.aws_region})",
            level=ValidationLevel.INFO
        )
    else:
        return CredentialCheckResult(
            passed=False,
            message="AWS credentials not configured (no access keys or profile)",
            level=ValidationLevel.WARNING
        )


def check_anthropic(creds: HarnessCredentials) -> CredentialCheckResult:
    """Check if Anthropic API key is configured."""
    if creds.anthropic_api_key:
        key_preview = creds.anthropic_api_key[:12] + "..."
        return CredentialCheckResult(
            passed=True,
            message=f"Anthropic API key configured ({key_preview})",
            level=ValidationLevel.INFO
        )
    else:
        return CredentialCheckResult(
            passed=True,  # Not required - Claude Code subscription works
            message="Anthropic API key not set (using Claude Code subscription)",
            level=ValidationLevel.WARNING
        )


def check_slack(creds: HarnessCredentials) -> CredentialCheckResult:
    """Check if Slack credentials are configured."""
    if creds.has_slack():
        return CredentialCheckResult(
            passed=True,
            message="Slack credentials configured",
            level=ValidationLevel.INFO
        )
    else:
        return CredentialCheckResult(
            passed=True,  # Optional
            message="Slack credentials not configured (optional)",
            level=ValidationLevel.WARNING
        )


def check_github(creds: HarnessCredentials) -> CredentialCheckResult:
    """Check if GitHub token is configured."""
    if creds.has_github():
        return CredentialCheckResult(
            passed=True,
            message="GitHub token configured",
            level=ValidationLevel.INFO
        )
    else:
        return CredentialCheckResult(
            passed=True,  # Optional
            message="GitHub token not configured (optional)",
            level=ValidationLevel.WARNING
        )


def check_context7(creds: HarnessCredentials) -> CredentialCheckResult:
    """Check if Context7 API key is configured."""
    if creds.context7_api_key:
        return CredentialCheckResult(
            passed=True,
            message="Context7 API key configured",
            level=ValidationLevel.INFO
        )
    else:
        return CredentialCheckResult(
            passed=True,  # Optional
            message="Context7 API key not configured (optional)",
            level=ValidationLevel.WARNING
        )


# Default checks to run
DEFAULT_CHECKS: list[Callable[[HarnessCredentials], CredentialCheckResult]] = [
    check_anthropic,
    check_aws,
    check_slack,
    check_github,
    check_context7,
]


def validate_credentials(
    creds: HarnessCredentials,
    checks: list[Callable[[HarnessCredentials], CredentialCheckResult]] = None,
    require_all: bool = False
) -> list[CredentialCheckResult]:
    """
    Validate credentials using composable check functions.

    Args:
        creds: Credentials to validate
        checks: List of check functions to run. Defaults to DEFAULT_CHECKS.
        require_all: If True, warnings become errors

    Returns:
        List of check results
    """
    if checks is None:
        checks = DEFAULT_CHECKS

    results = []
    for check in checks:
        result = check(creds)

        # Upgrade warnings to errors if require_all is True
        if require_all and result.level == ValidationLevel.WARNING and not result.passed:
            result = CredentialCheckResult(
                passed=False,
                message=result.message,
                level=ValidationLevel.ERROR
            )

        results.append(result)

    return results


def print_credential_status(creds: HarnessCredentials) -> None:
    """Print a formatted status of all credentials."""
    print("\nHarness Credential Status:")
    print("-" * 50)

    results = validate_credentials(creds)
    for result in results:
        print(f"  {result}")

    print("-" * 50)
