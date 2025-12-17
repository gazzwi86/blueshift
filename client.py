"""
Claude SDK Client Configuration
===============================

Functions for creating and configuring the Claude Agent SDK client.
"""

import json
import os
from pathlib import Path
from typing import Optional

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
from claude_code_sdk.types import HookMatcher

from credentials import Credentials, get_env_for_mcp_servers
from security import bash_security_hook


# Puppeteer MCP tools for browser automation
PUPPETEER_TOOLS = [
    "mcp__puppeteer__puppeteer_navigate",
    "mcp__puppeteer__puppeteer_screenshot",
    "mcp__puppeteer__puppeteer_click",
    "mcp__puppeteer__puppeteer_fill",
    "mcp__puppeteer__puppeteer_select",
    "mcp__puppeteer__puppeteer_hover",
    "mcp__puppeteer__puppeteer_evaluate",
]

# Slack MCP tools
SLACK_TOOLS = [
    "mcp__slack__list_channels",
    "mcp__slack__post_message",
    "mcp__slack__reply_to_thread",
    "mcp__slack__add_reaction",
    "mcp__slack__get_channel_history",
    "mcp__slack__get_thread_replies",
    "mcp__slack__search_messages",
    "mcp__slack__get_users",
    "mcp__slack__get_user_profile",
]

# GitHub MCP tools
GITHUB_TOOLS = [
    "mcp__github__create_or_update_file",
    "mcp__github__search_repositories",
    "mcp__github__create_repository",
    "mcp__github__get_file_contents",
    "mcp__github__push_files",
    "mcp__github__create_issue",
    "mcp__github__create_pull_request",
    "mcp__github__fork_repository",
    "mcp__github__create_branch",
    "mcp__github__list_commits",
    "mcp__github__list_branches",
]

# AWS MCP tools (wildcard patterns for dynamic tool discovery)
AWS_MCP_TOOLS = [
    "mcp__agentcore__*",
    "mcp__aws-terraform__*",
    "mcp__aws-api__*",
    "mcp__aws-docs__*",
    "mcp__aws-knowledge__*",
    "mcp__terraform-registry__*",
    "mcp__context7__*",
]

# Built-in tools available to the agent
BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
    "WebSearch",   # Enabled: Agent can research to resolve ambiguities
    "WebFetch",    # Enabled: Agent can fetch documentation and examples
    # Task/Agent tools are managed by Claude Code itself
]


def build_mcp_servers(creds: Optional[Credentials] = None) -> dict:
    """
    Build MCP server configuration.

    Args:
        creds: Optional credentials object for environment variables

    Returns:
        Dict of MCP server configurations
    """
    env_vars = get_env_for_mcp_servers(creds) if creds else {}

    servers = {
        # Browser automation
        "puppeteer": {
            "command": "npx",
            "args": ["-y", "@anthropic/puppeteer-mcp-server"]
        },

        # Slack (if credentials available)
        "slack": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-slack"],
            "env": {
                "SLACK_BOT_TOKEN": env_vars.get("SLACK_BOT_TOKEN", ""),
                "SLACK_APP_TOKEN": env_vars.get("SLACK_APP_TOKEN", ""),
            }
        },

        # GitHub (if credentials available)
        "github": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-github"],
            "env": {
                "GITHUB_TOKEN": env_vars.get("GITHUB_TOKEN", ""),
            }
        },

        # AWS & AgentCore (uvx-based)
        "agentcore": {
            "command": "uvx",
            "args": ["awslabs.amazon-bedrock-agentcore-mcp-server@latest"]
        },

        "aws-terraform": {
            "command": "uvx",
            "args": ["awslabs.terraform-mcp-server@latest"],
            "env": {
                "AWS_REGION": env_vars.get("AWS_REGION", "ap-southeast-2"),
                "FASTMCP_LOG_LEVEL": "ERROR",
                **{k: v for k, v in env_vars.items() if k.startswith("AWS_")},
            }
        },

        "aws-knowledge": {
            "command": "uvx",
            "args": ["fastmcp", "run", "https://knowledge-mcp.global.api.aws"]
        },

        "aws-api": {
            "command": "uvx",
            "args": ["awslabs.aws-api-mcp-server@latest"],
            "env": {
                "AWS_REGION": env_vars.get("AWS_REGION", "ap-southeast-2"),
                "AWS_API_MCP_PROFILE_NAME": env_vars.get("AWS_PROFILE", ""),
                **{k: v for k, v in env_vars.items() if k.startswith("AWS_")},
            }
        },

        "aws-docs": {
            "command": "uvx",
            "args": ["awslabs.aws-documentation-mcp-server@latest"]
        },

        # Terraform Registry (Docker-based)
        "terraform-registry": {
            "command": "docker",
            "args": ["run", "-i", "--rm", "hashicorp/terraform-mcp-server:0.3.0"]
        },

        # Context7 (HTTP transport)
        # Note: HTTP transport may need special handling in claude_code_sdk
        "context7": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-proxy"],
            "env": {
                "MCP_PROXY_URL": "https://mcp.context7.com/mcp",
                "CONTEXT7_API_KEY": env_vars.get("CONTEXT7_API_KEY", ""),
            }
        },
    }

    return servers


def create_client(
    project_dir: Path,
    model: str,
    creds: Optional[Credentials] = None,
) -> ClaudeSDKClient:
    """
    Create a Claude Agent SDK client with multi-layered security.

    Args:
        project_dir: Directory for the project
        model: Claude model to use
        creds: Optional credentials object

    Returns:
        Configured ClaudeSDKClient

    Security layers (defense in depth):
    1. Sandbox - OS-level bash command isolation prevents filesystem escape
    2. Permissions - File operations restricted to project_dir only
    3. Security hooks - Bash commands validated against an allowlist
       (see security.py for ALLOWED_COMMANDS)
    """
    # Note: ANTHROPIC_API_KEY is optional. If not set, the Claude Code SDK
    # will use the Claude Code subscription token (set via `claude setup-token`).
    # If ANTHROPIC_API_KEY is set, it will be used for direct API access instead.

    # Build MCP server configuration
    mcp_servers = build_mcp_servers(creds)

    # Collect all MCP tool patterns for permissions
    all_mcp_tools = [
        *PUPPETEER_TOOLS,
        *SLACK_TOOLS,
        *GITHUB_TOOLS,
    ]

    # Create comprehensive security settings
    # Note: Using relative paths ("./**") restricts access to project directory
    # since cwd is set to project_dir
    security_settings = {
        "sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True},
        "permissions": {
            "defaultMode": "acceptEdits",  # Auto-approve edits within allowed directories
            "allow": [
                # Allow all file operations within the project directory
                "Read(./**)",
                "Write(./**)",
                "Edit(./**)",
                "Glob(./**)",
                "Grep(./**)",
                # Bash permission granted here, but actual commands are validated
                # by the bash_security_hook (see security.py for allowed commands)
                "Bash(*)",
                # Allow all MCP tools
                *all_mcp_tools,
                # Wildcard patterns for AWS/Terraform MCP tools
                "mcp__agentcore__*",
                "mcp__aws-terraform__*",
                "mcp__aws-api__*",
                "mcp__aws-docs__*",
                "mcp__aws-knowledge__*",
                "mcp__terraform-registry__*",
                "mcp__context7__*",
            ],
        },
    }

    # Ensure project directory exists before creating settings file
    project_dir.mkdir(parents=True, exist_ok=True)

    # Write settings to a file in the project directory
    settings_file = project_dir / ".claude_settings.json"
    with open(settings_file, "w") as f:
        json.dump(security_settings, f, indent=2)

    print(f"Created security settings at {settings_file}")
    print("   - Sandbox enabled (OS-level bash isolation)")
    print(f"   - Filesystem restricted to: {project_dir.resolve()}")
    print("   - Bash commands restricted to allowlist (see security.py)")
    print("   - MCP servers configured:")
    for name in mcp_servers:
        print(f"     - {name}")
    print()

    return ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model=model,
            system_prompt="You are an expert software engineer building production-quality software. Follow best practices, write clean code, and ensure comprehensive testing.",
            allowed_tools=[
                *BUILTIN_TOOLS,
                *all_mcp_tools,
                *AWS_MCP_TOOLS,  # Wildcard patterns for AWS/infrastructure MCP servers
            ],
            mcp_servers=mcp_servers,
            hooks={
                "PreToolUse": [
                    HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
                ],
            },
            max_turns=1000,
            cwd=str(project_dir.resolve()),
            settings=str(settings_file.resolve()),  # Use absolute path
        )
    )
