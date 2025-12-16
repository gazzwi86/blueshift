"""
Slack Helpers (Optional)
========================

Minimal utility functions for Slack interaction.
The agent can use these OR use MCP tools directly - these are just conveniences.
"""

import os
from typing import Optional

# Try to import slack_sdk, but don't fail if not installed
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_SDK_AVAILABLE = True
except ImportError:
    SLACK_SDK_AVAILABLE = False
    WebClient = None
    SlackApiError = Exception


def get_slack_client() -> Optional["WebClient"]:
    """
    Get an authenticated Slack WebClient.

    Uses SLACK_BOT_TOKEN from environment/.env file.

    Returns:
        WebClient if credentials available, None otherwise
    """
    if not SLACK_SDK_AVAILABLE:
        print("Warning: slack_sdk not installed. Run: pip install slack_sdk")
        return None

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("Warning: SLACK_BOT_TOKEN not set in environment")
        return None

    return WebClient(token=token)


def send_message(channel: str, text: str, thread_ts: Optional[str] = None) -> Optional[dict]:
    """
    Send a message to a Slack channel.

    Args:
        channel: Channel ID or name (e.g., "#general" or "C1234567890")
        text: Message text (supports Slack markdown)
        thread_ts: Optional thread timestamp to reply in thread

    Returns:
        Response dict from Slack API, or None on failure
    """
    client = get_slack_client()
    if not client:
        return None

    try:
        response = client.chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts,
        )
        return response.data
    except SlackApiError as e:
        print(f"Slack API error: {e.response['error']}")
        return None


def get_channel_history(channel: str, limit: int = 10) -> Optional[list]:
    """
    Get recent messages from a channel.

    Args:
        channel: Channel ID
        limit: Number of messages to retrieve

    Returns:
        List of message dicts, or None on failure
    """
    client = get_slack_client()
    if not client:
        return None

    try:
        response = client.conversations_history(
            channel=channel,
            limit=limit,
        )
        return response.data.get("messages", [])
    except SlackApiError as e:
        print(f"Slack API error: {e.response['error']}")
        return None


def add_reaction(channel: str, timestamp: str, emoji: str) -> bool:
    """
    Add a reaction to a message.

    Args:
        channel: Channel ID
        timestamp: Message timestamp
        emoji: Emoji name without colons (e.g., "thumbsup")

    Returns:
        True on success, False on failure
    """
    client = get_slack_client()
    if not client:
        return False

    try:
        client.reactions_add(
            channel=channel,
            timestamp=timestamp,
            name=emoji,
        )
        return True
    except SlackApiError as e:
        print(f"Slack API error: {e.response['error']}")
        return False
