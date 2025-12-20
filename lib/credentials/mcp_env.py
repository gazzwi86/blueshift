"""
MCP Environment Variables
=========================

Generate environment variables for MCP servers.
"""

from .types import HarnessCredentials


def get_env_for_mcp_servers(creds: HarnessCredentials) -> dict[str, str]:
    """
    Get environment variables to pass to MCP servers.

    Args:
        creds: Harness credentials

    Returns:
        Dict of environment variables
    """
    env = {}

    # AWS
    if creds.aws_access_key_id:
        env["AWS_ACCESS_KEY_ID"] = creds.aws_access_key_id
    if creds.aws_secret_access_key:
        env["AWS_SECRET_ACCESS_KEY"] = creds.aws_secret_access_key
    if creds.aws_region:
        env["AWS_REGION"] = creds.aws_region
    if creds.aws_profile:
        env["AWS_PROFILE"] = creds.aws_profile

    # Slack
    if creds.slack_bot_token:
        env["SLACK_BOT_TOKEN"] = creds.slack_bot_token
    if creds.slack_app_token:
        env["SLACK_APP_TOKEN"] = creds.slack_app_token

    # GitHub
    if creds.github_token:
        env["GITHUB_TOKEN"] = creds.github_token

    # Context7
    if creds.context7_api_key:
        env["CONTEXT7_API_KEY"] = creds.context7_api_key

    return env
