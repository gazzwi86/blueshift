"""
Project Security Configuration
==============================

Extends the base security framework with project-specific command allowlist.
Edit ALLOWED_COMMANDS to customize which bash commands the agent can run.
"""

from lib.security.base import BaseSecurity


class ProjectSecurity(BaseSecurity):
    """
    Project-specific security configuration.

    Customize ALLOWED_COMMANDS for your project's needs.
    """

    # Commands allowed for this project
    ALLOWED_COMMANDS = {
        # File inspection
        "ls",
        "cat",
        "head",
        "tail",
        "wc",
        "grep",
        "find",

        # File operations
        "cp",
        "mkdir",
        "touch",
        "chmod",  # Validated: only +x allowed

        # Output/scripting
        "echo",
        "xargs",
        "test",  # Shell test command for conditionals
        "[",     # Alternative test syntax

        # Directory
        "pwd",

        # Node.js development
        "npm",
        "node",
        "npx",

        # Version control
        "git",

        # Process management
        "ps",
        "lsof",
        "sleep",
        "pkill",  # Validated: only dev processes

        # Script execution
        "init.sh",  # Validated: only ./init.sh

        # Infrastructure
        "terraform",  # All operations allowed
        "aws",  # Validated: dangerous operations blocked

        # GitHub
        "gh",

        # Testing
        "pytest",
        "python",
        "python3",

        # Docker
        "docker",  # Validated: no --privileged
        "docker-compose",

        # Package management
        "pip",
        "pip3",
        "uv",
        "uvx",

        # Research and web access
        "curl",    # For API calls and web fetching
        "wget",    # For downloading files

        # AgentCore CLI
        "agentcore",  # Agent deployment and management

        # Zip for packaging
        "zip",
        "unzip",
    }

    # Commands that need additional validation
    COMMANDS_NEEDING_EXTRA_VALIDATION = {
        "pkill",
        "chmod",
        "init.sh",
        "terraform",
        "aws",
        "docker",
        "docker-compose",
    }


# Default instance for import
_security = ProjectSecurity()

# Export the hook for use in client.py
bash_security_hook = _security.create_hook()

# Export validation function for testing
def validate_command(command: str) -> tuple[bool, str]:
    """Validate a bash command against the project allowlist."""
    return _security.validate_command(command)
