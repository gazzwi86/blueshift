"""
Credential Management
=====================

Load and validate credentials for the Blueshift harness.

This module handles GENERIC harness credentials only:
- AWS (access keys or profile)
- Anthropic API key
- Slack (optional)
- GitHub (optional)
- Context7 (optional)

Project-specific credentials (Snowflake, SharePoint, etc.) should be
defined in your project's configuration, not here.
"""

from .types import HarnessCredentials
from .loader import load_env_file, get_credentials
from .validator import validate_credentials, check_aws, check_slack, check_github
from .mcp_env import get_env_for_mcp_servers

__all__ = [
    # Types
    "HarnessCredentials",
    # Loader
    "load_env_file",
    "get_credentials",
    # Validator
    "validate_credentials",
    "check_aws",
    "check_slack",
    "check_github",
    # MCP
    "get_env_for_mcp_servers",
]
