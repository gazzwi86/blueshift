"""
Security Allowlist
==================

Defines which bash commands are allowed to be executed by the agent.
This is a security boundary - commands not in this list are blocked.

The allowlist is intentionally restrictive. Add commands carefully.
"""

from typing import Callable

# Commands that are always allowed
ALWAYS_ALLOWED = {
    # Version control
    "git",

    # Package managers
    "npm", "npx", "yarn", "pnpm",
    "pip", "pip3", "uv", "poetry",
    "cargo",

    # Build tools
    "make", "cmake",
    "tsc", "esbuild", "vite", "webpack",

    # Testing
    "pytest", "jest", "vitest", "mocha",
    "playwright",

    # Linting/Formatting
    "ruff", "black", "isort", "flake8",
    "eslint", "prettier",
    "rustfmt", "clippy",

    # Infrastructure
    "terraform", "terragrunt",
    "docker", "docker-compose",
    "kubectl", "helm",
    "aws", "gcloud", "az",
    "agentcore",

    # Development utilities
    "python", "python3", "node",
    "curl", "wget", "jq",
    "ls", "pwd", "cd", "mkdir", "touch",
    "cp", "mv",  # Note: rm is NOT allowed by default
    "tree", "wc",
    "head", "tail", "less", "more",
    "diff", "patch",
    "which", "whereis", "type",
    "env", "printenv", "export",
    "source", ".",
    "chmod",  # Needed for init.sh
    "zip", "unzip", "tar", "gzip",
}

# Commands that are blocked even if they appear in ALWAYS_ALLOWED
ALWAYS_BLOCKED = {
    "rm -rf /",
    "rm -rf /*",
    "rm -rf ~",
    "rm -rf ~/*",
    "sudo rm",
    "> /dev/sda",
    "mkfs",
    "dd if=",
    ":(){:|:&};:",  # Fork bomb
}

# Patterns that indicate dangerous operations
DANGEROUS_PATTERNS = [
    # Destructive file operations
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+\*",
    r">\s*/dev/",

    # Privilege escalation
    r"sudo\s+su",
    r"sudo\s+-i",

    # Secret exposure (reading credential files directly)
    r"cat\s+.*\.env",
    r"cat\s+.*credentials",
    r"cat\s+.*secret",
    r"cat\s+.*/\.aws/",

    # Network attacks
    r"nc\s+-l",  # Netcat listener
    r"nmap\s+",

    # Code injection
    r"eval\s+\$",
    r"`.*`",  # Backtick command substitution in dangerous contexts
]


def get_command_base(command: str) -> str:
    """
    Extract the base command from a full command string.

    Args:
        command: Full command string

    Returns:
        The base command (first word)
    """
    # Handle command prefixes like 'AWS_PROFILE=x command'
    parts = command.strip().split()

    for part in parts:
        # Skip environment variable assignments
        if '=' in part and not part.startswith('-'):
            continue
        # Skip common prefixes
        if part in ('sudo', 'time', 'nice', 'nohup'):
            continue
        return part

    return parts[0] if parts else ""


def is_command_allowed(command: str) -> tuple[bool, str]:
    """
    Check if a command is allowed to be executed.

    Args:
        command: The command to check

    Returns:
        Tuple of (is_allowed, reason)
    """
    import re

    command = command.strip()

    if not command:
        return False, "Empty command"

    # Check for always-blocked patterns
    for blocked in ALWAYS_BLOCKED:
        if blocked in command:
            return False, f"Blocked pattern: {blocked}"

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Dangerous pattern detected"

    # Get the base command
    base_cmd = get_command_base(command)

    if not base_cmd:
        return False, "Could not determine base command"

    # Check if base command is allowed
    if base_cmd in ALWAYS_ALLOWED:
        return True, "Allowed command"

    # Check for common shell built-ins that are safe
    safe_builtins = {'echo', 'printf', 'test', '[', '[[', 'true', 'false', 'exit'}
    if base_cmd in safe_builtins:
        return True, "Safe shell builtin"

    return False, f"Command not in allowlist: {base_cmd}"


# For backward compatibility
ALLOWED_COMMANDS = ALWAYS_ALLOWED


def create_security_hook() -> Callable[[str], tuple[bool, str]]:
    """
    Create a security hook function for the Claude SDK.

    Returns:
        A function that takes a command and returns (allowed, reason)
    """
    def hook(command: str) -> tuple[bool, str]:
        return is_command_allowed(command)
    return hook
