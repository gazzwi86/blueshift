"""
Claude SDK Client Configuration
===============================

Base client creation for Claude Agent SDK.
Projects extend by providing MCP server configs and security hooks.
"""

import json
import os
from pathlib import Path
from typing import Optional, Callable, Any

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
from claude_code_sdk.types import HookMatcher


# Built-in tools
BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
]


def create_base_client(
    project_dir: Path,
    model: str,
    mcp_servers: dict = None,
    allowed_tools: list[str] = None,
    security_hook: Callable = None,
    system_prompt: str = None,
    permissions: list[str] = None,
) -> ClaudeSDKClient:
    """
    Create a Claude Agent SDK client with configurable security.

    Args:
        project_dir: Directory for the project
        model: Claude model to use
        mcp_servers: Dict of MCP server configurations
        allowed_tools: List of allowed MCP tools
        security_hook: Async function for bash command validation
        system_prompt: Custom system prompt
        permissions: Additional permission patterns

    Returns:
        Configured ClaudeSDKClient
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set.\n"
            "Get your API key from: https://console.anthropic.com/"
        )

    mcp_servers = mcp_servers or {}
    allowed_tools = allowed_tools or []

    # Build base permissions
    base_permissions = [
        "Read(./**)",
        "Write(./**)",
        "Edit(./**)",
        "Glob(./**)",
        "Grep(./**)",
        "Bash(*)",
    ]

    if permissions:
        base_permissions.extend(permissions)

    # Add allowed tool permissions
    base_permissions.extend(allowed_tools)

    security_settings = {
        "sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True},
        "permissions": {
            "defaultMode": "acceptEdits",
            "allow": base_permissions,
        },
    }

    # Ensure project directory exists
    project_dir.mkdir(parents=True, exist_ok=True)

    # Write settings file
    settings_file = project_dir / ".claude_settings.json"
    with open(settings_file, "w") as f:
        json.dump(security_settings, f, indent=2)

    # Build hooks
    hooks = {}
    if security_hook:
        hooks["PreToolUse"] = [
            HookMatcher(matcher="Bash", hooks=[security_hook]),
        ]

    return ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model=model,
            system_prompt=system_prompt or "You are an expert developer building production-quality software.",
            allowed_tools=[*BUILTIN_TOOLS, *allowed_tools],
            mcp_servers=mcp_servers,
            hooks=hooks,
            max_turns=1000,
            cwd=str(project_dir.resolve()),
            settings=str(settings_file.resolve()),
        )
    )


class ClientBuilder:
    """
    Builder pattern for creating Claude SDK clients with project-specific configuration.
    """

    def __init__(self, project_dir: Path, model: str):
        self.project_dir = project_dir
        self.model = model
        self.mcp_servers = {}
        self.allowed_tools = []
        self.security_hook = None
        self.system_prompt = None
        self.permissions = []

    def with_mcp_server(self, name: str, config: dict) -> "ClientBuilder":
        """Add an MCP server."""
        self.mcp_servers[name] = config
        return self

    def with_mcp_tools(self, tools: list[str]) -> "ClientBuilder":
        """Add allowed MCP tools."""
        self.allowed_tools.extend(tools)
        return self

    def with_security_hook(self, hook: Callable) -> "ClientBuilder":
        """Set the security hook for bash validation."""
        self.security_hook = hook
        return self

    def with_system_prompt(self, prompt: str) -> "ClientBuilder":
        """Set the system prompt."""
        self.system_prompt = prompt
        return self

    def with_permissions(self, perms: list[str]) -> "ClientBuilder":
        """Add additional permissions."""
        self.permissions.extend(perms)
        return self

    def build(self) -> ClaudeSDKClient:
        """Build the client."""
        return create_base_client(
            project_dir=self.project_dir,
            model=self.model,
            mcp_servers=self.mcp_servers,
            allowed_tools=self.allowed_tools,
            security_hook=self.security_hook,
            system_prompt=self.system_prompt,
            permissions=self.permissions,
        )
