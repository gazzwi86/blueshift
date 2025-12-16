"""
Credential Validator

Validates credentials from various sources (environment, files, AWS Secrets Manager)
with fail-fast behavior for required credentials.
"""

import os
import subprocess
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class CredentialSource(Enum):
    """Where credentials can be loaded from."""
    ENV = "env"           # Environment variable
    DOTENV = "dotenv"     # .env file
    AWS_SECRET = "aws_secret"  # AWS Secrets Manager
    FILE = "file"         # Direct file path


@dataclass
class CredentialSpec:
    """Specification for a required credential."""
    name: str
    source: CredentialSource
    required: bool = True
    description: str = ""
    validation_fn: callable = None  # Optional validation function

    # For AWS Secrets Manager
    secret_name: str = None
    secret_key: str = None

    # For file source
    file_path: str = None


@dataclass
class CredentialValue:
    """A validated credential value."""
    name: str
    value: str
    source: CredentialSource
    valid: bool
    error: Optional[str] = None

    @property
    def masked_value(self) -> str:
        """Return masked value for display."""
        if not self.value:
            return "<empty>"
        if len(self.value) <= 8:
            return "*" * len(self.value)
        return self.value[:4] + "*" * (len(self.value) - 8) + self.value[-4:]


@dataclass
class ValidationResult:
    """Result of credential validation."""
    valid: bool
    credentials: dict[str, CredentialValue] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    invalid: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def print_status(self) -> None:
        """Print credential status to console."""
        print("\n" + "=" * 60)
        print("  CREDENTIAL VALIDATION")
        print("=" * 60)

        if self.valid:
            print("\n  Status: VALID")
        else:
            print("\n  Status: INVALID")

        print("\n  Credentials:")
        for name, cred in self.credentials.items():
            status = "[OK]" if cred.valid else "[MISSING]" if not cred.value else "[INVALID]"
            print(f"    {status} {name}: {cred.masked_value}")

        if self.missing:
            print(f"\n  Missing ({len(self.missing)}): {', '.join(self.missing)}")

        if self.invalid:
            print(f"\n  Invalid ({len(self.invalid)}): {', '.join(self.invalid)}")

        if self.warnings:
            print("\n  Warnings:")
            for warning in self.warnings:
                print(f"    - {warning}")

        print("\n" + "=" * 60 + "\n")


class CredentialValidator:
    """
    Validates credentials from various sources.

    Supports:
    - Environment variables
    - .env files (using python-dotenv if available)
    - AWS Secrets Manager
    - Direct file paths
    """

    def __init__(self, dotenv_path: Path = None):
        self.dotenv_path = dotenv_path or Path(".env")
        self.specs: list[CredentialSpec] = []
        self._dotenv_loaded = False

    def require(
        self,
        name: str,
        source: str | CredentialSource = "env",
        required: bool = True,
        description: str = "",
        validation_fn: callable = None,
        **kwargs
    ) -> "CredentialValidator":
        """
        Add a required credential.

        Args:
            name: Credential name (e.g., "AWS_ACCESS_KEY_ID")
            source: Where to load from ("env", "dotenv", "aws_secret", "file")
            required: If True, validation fails if missing
            description: Human-readable description
            validation_fn: Optional function to validate the value
            **kwargs: Additional args (secret_name, secret_key, file_path)

        Returns:
            self for chaining
        """
        if isinstance(source, str):
            source = CredentialSource(source)

        spec = CredentialSpec(
            name=name,
            source=source,
            required=required,
            description=description,
            validation_fn=validation_fn,
            secret_name=kwargs.get("secret_name"),
            secret_key=kwargs.get("secret_key"),
            file_path=kwargs.get("file_path")
        )

        self.specs.append(spec)
        return self

    def require_aws(self) -> "CredentialValidator":
        """Add standard AWS credential requirements."""
        self.require("AWS_ACCESS_KEY_ID", required=True, description="AWS access key")
        self.require("AWS_SECRET_ACCESS_KEY", required=True, description="AWS secret key")
        self.require("AWS_REGION", required=True, description="AWS region")
        return self

    def require_snowflake(self) -> "CredentialValidator":
        """Add Snowflake credential requirements."""
        self.require("SNOWFLAKE_ACCOUNT", required=True)
        self.require("SNOWFLAKE_USER", required=True)
        self.require("SNOWFLAKE_PASSWORD", required=True)
        self.require("SNOWFLAKE_WAREHOUSE", required=True)
        self.require("SNOWFLAKE_DATABASE", required=True)
        self.require("SNOWFLAKE_SCHEMA", required=True)
        return self

    def require_sharepoint(self) -> "CredentialValidator":
        """Add SharePoint credential requirements."""
        self.require("SHAREPOINT_CLIENT_ID", required=True)
        self.require("SHAREPOINT_CLIENT_SECRET", required=True)
        self.require("SHAREPOINT_TENANT_ID", required=True)
        self.require("SHAREPOINT_SITE_URL", required=True)
        return self

    def require_slack(self, required: bool = False) -> "CredentialValidator":
        """Add Slack credential requirements (optional by default)."""
        self.require("SLACK_BOT_TOKEN", required=required, description="Slack bot token (xoxb-...)")
        self.require("SLACK_APP_TOKEN", required=required, description="Slack app token (xapp-...)")
        return self

    def _load_dotenv(self) -> None:
        """Load .env file if available."""
        if self._dotenv_loaded:
            return

        if not self.dotenv_path.exists():
            return

        try:
            from dotenv import load_dotenv
            load_dotenv(self.dotenv_path)
            self._dotenv_loaded = True
        except ImportError:
            # Fallback: manually parse .env
            try:
                with open(self.dotenv_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, _, value = line.partition("=")
                            # Remove quotes
                            value = value.strip().strip('"').strip("'")
                            os.environ.setdefault(key.strip(), value)
                self._dotenv_loaded = True
            except Exception:
                pass

    def _get_from_env(self, name: str) -> Optional[str]:
        """Get credential from environment variable."""
        self._load_dotenv()
        return os.environ.get(name)

    def _get_from_aws_secret(self, spec: CredentialSpec) -> Optional[str]:
        """Get credential from AWS Secrets Manager."""
        if not spec.secret_name:
            return None

        try:
            result = subprocess.run(
                ["aws", "secretsmanager", "get-secret-value",
                 "--secret-id", spec.secret_name,
                 "--output", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)
            secret_string = data.get("SecretString", "{}")

            try:
                secret_dict = json.loads(secret_string)
                if spec.secret_key:
                    return secret_dict.get(spec.secret_key)
                return secret_string
            except json.JSONDecodeError:
                return secret_string

        except Exception:
            return None

    def _get_from_file(self, spec: CredentialSpec) -> Optional[str]:
        """Get credential from file."""
        if not spec.file_path:
            return None

        try:
            path = Path(spec.file_path).expanduser()
            if path.exists():
                return path.read_text().strip()
        except Exception:
            pass

        return None

    def _get_credential_value(self, spec: CredentialSpec) -> CredentialValue:
        """Get and validate a credential value."""
        value = None
        error = None

        # Get value based on source
        if spec.source in (CredentialSource.ENV, CredentialSource.DOTENV):
            value = self._get_from_env(spec.name)
        elif spec.source == CredentialSource.AWS_SECRET:
            value = self._get_from_aws_secret(spec)
        elif spec.source == CredentialSource.FILE:
            value = self._get_from_file(spec)

        # Validate if we have a value and a validation function
        valid = True
        if value and spec.validation_fn:
            try:
                if not spec.validation_fn(value):
                    valid = False
                    error = "Validation function returned False"
            except Exception as e:
                valid = False
                error = str(e)
        elif not value and spec.required:
            valid = False
            error = "Required credential not found"

        return CredentialValue(
            name=spec.name,
            value=value or "",
            source=spec.source,
            valid=valid if value else not spec.required,
            error=error
        )

    def validate(self) -> ValidationResult:
        """
        Validate all registered credentials.

        Returns:
            ValidationResult with status and details
        """
        credentials = {}
        missing = []
        invalid = []
        warnings = []

        for spec in self.specs:
            cred = self._get_credential_value(spec)
            credentials[spec.name] = cred

            if not cred.value:
                if spec.required:
                    missing.append(spec.name)
                else:
                    warnings.append(f"{spec.name} not set (optional)")
            elif not cred.valid:
                invalid.append(spec.name)

        overall_valid = len(missing) == 0 and len(invalid) == 0

        return ValidationResult(
            valid=overall_valid,
            credentials=credentials,
            missing=missing,
            invalid=invalid,
            warnings=warnings
        )

    def validate_and_exit(self) -> None:
        """Validate credentials and exit if invalid."""
        result = self.validate()
        result.print_status()

        if not result.valid:
            print("ERROR: Required credentials are missing or invalid.")
            print("Please update your .env file and try again.\n")
            exit(1)

    def test_aws_connectivity(self) -> bool:
        """Test that AWS credentials work."""
        try:
            result = subprocess.run(
                ["aws", "sts", "get-caller-identity"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False


# Convenience function for CLI usage
def validate_credentials(
    require_aws: bool = True,
    require_snowflake: bool = True,
    require_sharepoint: bool = True,
    require_slack: bool = False
) -> ValidationResult:
    """
    Validate credentials for a typical project setup.

    Args:
        require_aws: Require AWS credentials
        require_snowflake: Require Snowflake credentials
        require_sharepoint: Require SharePoint credentials
        require_slack: Require Slack credentials (usually optional)

    Returns:
        ValidationResult
    """
    validator = CredentialValidator()

    if require_aws:
        validator.require_aws()
    if require_snowflake:
        validator.require_snowflake()
    if require_sharepoint:
        validator.require_sharepoint()

    validator.require_slack(required=require_slack)

    return validator.validate()


# CLI entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate credentials")
    parser.add_argument("--validate", action="store_true", help="Run validation")
    parser.add_argument("--no-snowflake", action="store_true", help="Don't require Snowflake")
    parser.add_argument("--no-sharepoint", action="store_true", help="Don't require SharePoint")

    args = parser.parse_args()

    if args.validate:
        result = validate_credentials(
            require_snowflake=not args.no_snowflake,
            require_sharepoint=not args.no_sharepoint
        )
        result.print_status()
        exit(0 if result.valid else 1)
