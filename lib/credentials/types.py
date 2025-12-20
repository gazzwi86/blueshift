"""
Credential Types
================

Dataclass definitions for harness credentials.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class HarnessCredentials:
    """
    Credentials for running the Blueshift agent harness.

    These are GENERIC credentials used by the harness itself,
    not project-specific credentials.
    """
    # Anthropic (optional - Claude Code subscription works as fallback)
    anthropic_api_key: str = ""

    # AWS credentials (either access keys OR profile)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "ap-southeast-2"
    aws_profile: Optional[str] = None

    # Slack (optional)
    slack_bot_token: Optional[str] = None
    slack_app_token: Optional[str] = None
    slack_signing_secret: Optional[str] = None

    # GitHub (optional)
    github_token: Optional[str] = None

    # Context7 (optional)
    context7_api_key: Optional[str] = None

    def has_aws_keys(self) -> bool:
        """Check if AWS access keys are configured."""
        return bool(self.aws_access_key_id and self.aws_secret_access_key)

    def has_aws_profile(self) -> bool:
        """Check if AWS profile is configured."""
        return bool(self.aws_profile)

    def has_aws(self) -> bool:
        """Check if any AWS credentials are configured."""
        return self.has_aws_keys() or self.has_aws_profile()

    def has_slack(self) -> bool:
        """Check if Slack credentials are configured."""
        return bool(self.slack_bot_token and self.slack_app_token)

    def has_github(self) -> bool:
        """Check if GitHub token is configured."""
        return bool(self.github_token)


# Backward compatibility alias
Credentials = HarnessCredentials
