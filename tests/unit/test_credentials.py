"""
Credential Tests
================

Unit tests for the credential management module.
"""

import pytest
from lib.credentials.types import HarnessCredentials
from lib.credentials.validator import (
    check_aws,
    check_slack,
    check_github,
    validate_credentials,
    CredentialCheckResult,
)
from lib.core.types import ValidationLevel


class TestHarnessCredentials:
    """Tests for HarnessCredentials dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        creds = HarnessCredentials()
        assert creds.anthropic_api_key == ""
        assert creds.aws_access_key_id is None
        assert creds.aws_region == "ap-southeast-2"

    def test_has_aws_keys(self):
        """Test AWS key detection."""
        creds = HarnessCredentials(
            aws_access_key_id="AKIATEST",
            aws_secret_access_key="secret"
        )
        assert creds.has_aws_keys() is True
        assert creds.has_aws_profile() is False
        assert creds.has_aws() is True

    def test_has_aws_profile(self):
        """Test AWS profile detection."""
        creds = HarnessCredentials(aws_profile="my-profile")
        assert creds.has_aws_keys() is False
        assert creds.has_aws_profile() is True
        assert creds.has_aws() is True

    def test_has_slack(self):
        """Test Slack credential detection."""
        creds = HarnessCredentials(
            slack_bot_token="xoxb-test",
            slack_app_token="xapp-test"
        )
        assert creds.has_slack() is True

    def test_has_slack_partial(self):
        """Test that partial Slack creds don't count."""
        creds = HarnessCredentials(slack_bot_token="xoxb-test")
        assert creds.has_slack() is False

    def test_has_github(self):
        """Test GitHub token detection."""
        creds = HarnessCredentials(github_token="ghp_test")
        assert creds.has_github() is True


class TestCredentialChecks:
    """Tests for individual check functions."""

    def test_check_aws_with_profile(self):
        """Test AWS check with profile configured."""
        creds = HarnessCredentials(aws_profile="test-profile")
        result = check_aws(creds)
        assert result.passed is True
        assert "profile: test-profile" in result.message
        assert result.level == ValidationLevel.INFO

    def test_check_aws_with_keys(self):
        """Test AWS check with access keys."""
        creds = HarnessCredentials(
            aws_access_key_id="AKIA...",
            aws_secret_access_key="secret",
            aws_region="us-east-1"
        )
        result = check_aws(creds)
        assert result.passed is True
        assert "access keys" in result.message
        assert result.level == ValidationLevel.INFO

    def test_check_aws_missing(self):
        """Test AWS check when not configured."""
        creds = HarnessCredentials()
        result = check_aws(creds)
        assert result.passed is False
        assert result.level == ValidationLevel.WARNING

    def test_check_slack_configured(self):
        """Test Slack check when configured."""
        creds = HarnessCredentials(
            slack_bot_token="xoxb-test",
            slack_app_token="xapp-test"
        )
        result = check_slack(creds)
        assert result.passed is True
        assert result.level == ValidationLevel.INFO

    def test_check_slack_missing(self):
        """Test Slack check when not configured."""
        creds = HarnessCredentials()
        result = check_slack(creds)
        # Slack is optional, so still passes
        assert result.passed is True
        assert result.level == ValidationLevel.WARNING

    def test_check_github_configured(self):
        """Test GitHub check when configured."""
        creds = HarnessCredentials(github_token="ghp_test")
        result = check_github(creds)
        assert result.passed is True

    def test_check_github_missing(self):
        """Test GitHub check when not configured."""
        creds = HarnessCredentials()
        result = check_github(creds)
        assert result.passed is True  # Optional
        assert result.level == ValidationLevel.WARNING


class TestValidateCredentials:
    """Tests for the validate_credentials function."""

    def test_validate_all_configured(self):
        """Test validation with all credentials configured."""
        creds = HarnessCredentials(
            anthropic_api_key="sk-test",
            aws_profile="test",
            slack_bot_token="xoxb",
            slack_app_token="xapp",
            github_token="ghp",
            context7_api_key="ctx7"
        )
        results = validate_credentials(creds)
        assert all(r.passed for r in results)

    def test_validate_minimal(self):
        """Test validation with minimal credentials."""
        creds = HarnessCredentials()
        results = validate_credentials(creds)
        # Should have warnings but not errors
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        assert len(errors) == 0

    def test_validate_custom_checks(self):
        """Test validation with custom check list."""
        creds = HarnessCredentials(aws_profile="test")
        results = validate_credentials(creds, checks=[check_aws])
        assert len(results) == 1
        assert results[0].passed is True
