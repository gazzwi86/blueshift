"""
Credential Loader
=================

Load credentials from environment variables and .env files.
"""

import os
from pathlib import Path
from typing import Optional

from .types import HarnessCredentials


# Try to import dotenv
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


def load_env_file(env_path: Optional[Path] = None) -> None:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Path to .env file. Defaults to .env in harness root.
    """
    if env_path is None:
        from ..core.paths import get_harness_root
        env_path = get_harness_root() / ".env"

    if not env_path.exists():
        print(f"No .env file found at {env_path}")
        print("Using environment variables only")
        return

    if DOTENV_AVAILABLE:
        load_dotenv(env_path)
        print(f"Loaded credentials from {env_path}")
    else:
        # Manual .env parsing as fallback
        _manual_parse_env(env_path)
        print(f"Loaded credentials from {env_path} (manual parsing)")


def _manual_parse_env(env_path: Path) -> None:
    """
    Manually parse a .env file when python-dotenv is not available.

    Args:
        env_path: Path to the .env file
    """
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and value:
                    os.environ[key] = value


def get_credentials(env_path: Optional[Path] = None) -> HarnessCredentials:
    """
    Load harness credentials from environment.

    Args:
        env_path: Optional path to .env file

    Returns:
        HarnessCredentials object with loaded values
    """
    load_env_file(env_path)

    return HarnessCredentials(
        # Anthropic (optional)
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),

        # AWS
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        aws_region=os.environ.get("AWS_REGION", "ap-southeast-2"),
        aws_profile=os.environ.get("AWS_PROFILE"),

        # Slack
        slack_bot_token=os.environ.get("SLACK_BOT_TOKEN"),
        slack_app_token=os.environ.get("SLACK_APP_TOKEN"),
        slack_signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),

        # GitHub
        github_token=os.environ.get("GITHUB_TOKEN"),

        # Context7
        context7_api_key=os.environ.get("CONTEXT7_API_KEY"),
    )
