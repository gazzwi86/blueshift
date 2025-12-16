"""
Base Security Framework
=======================

Core security validation logic for autonomous agent bash command execution.
Uses an allowlist approach - only explicitly permitted commands can run.

This module provides:
1. Command parsing utilities
2. Validation functions for specific commands
3. BaseSecurity class for extension

Projects extend this by subclassing BaseSecurity and defining:
- ALLOWED_COMMANDS: Set of permitted command names
- COMMANDS_NEEDING_EXTRA_VALIDATION: Commands requiring additional checks

Example:
    from lib.security.base import BaseSecurity

    class ProjectSecurity(BaseSecurity):
        ALLOWED_COMMANDS = {"ls", "cat", "npm", "node", ...}
        COMMANDS_NEEDING_EXTRA_VALIDATION = {"pkill", "chmod", ...}

    security = ProjectSecurity()
    hook = security.create_hook()
"""

import os
import re
import shlex
from typing import Callable


def split_command_segments(command_string: str) -> list[str]:
    """
    Split a compound command into individual command segments.

    Handles command chaining (&&, ||, ;) but not pipes (those are single commands).

    Args:
        command_string: The full shell command

    Returns:
        List of individual command segments
    """
    # Split on && and || while preserving the ability to handle each segment
    segments = re.split(r"\s*(?:&&|\|\|)\s*", command_string)

    # Further split on semicolons
    result = []
    for segment in segments:
        sub_segments = re.split(r'(?<!["\'])\s*;\s*(?!["\'])', segment)
        for sub in sub_segments:
            sub = sub.strip()
            if sub:
                result.append(sub)

    return result


def extract_commands(command_string: str) -> list[str]:
    """
    Extract command names from a shell command string.

    Handles pipes, command chaining (&&, ||, ;), and subshells.
    Returns the base command names (without paths).

    Args:
        command_string: The full shell command

    Returns:
        List of command names found in the string
    """
    commands = []

    # Split on semicolons that aren't inside quotes
    segments = re.split(r'(?<!["\'])\s*;\s*(?!["\'])', command_string)

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        try:
            tokens = shlex.split(segment)
        except ValueError:
            # Malformed command - return empty to trigger block (fail-safe)
            return []

        if not tokens:
            continue

        # Track when we expect a command vs arguments
        expect_command = True

        for token in tokens:
            # Shell operators indicate a new command follows
            if token in ("|", "||", "&&", "&"):
                expect_command = True
                continue

            # Skip shell keywords that precede commands
            if token in (
                "if", "then", "else", "elif", "fi",
                "for", "while", "until", "do", "done",
                "case", "esac", "in", "!", "{", "}",
            ):
                continue

            # Skip flags/options
            if token.startswith("-"):
                continue

            # Skip variable assignments (VAR=value)
            if "=" in token and not token.startswith("="):
                continue

            if expect_command:
                # Extract the base command name (handle paths like /usr/bin/python)
                cmd = os.path.basename(token)
                commands.append(cmd)
                expect_command = False

    return commands


def validate_pkill_command(command_string: str) -> tuple[bool, str]:
    """
    Validate pkill commands - only allow killing dev-related processes.

    Returns:
        Tuple of (is_allowed, reason_if_blocked)
    """
    allowed_process_names = {"node", "npm", "npx", "vite", "next"}

    try:
        tokens = shlex.split(command_string)
    except ValueError:
        return False, "Could not parse pkill command"

    if not tokens:
        return False, "Empty pkill command"

    args = [t for t in tokens[1:] if not t.startswith("-")]

    if not args:
        return False, "pkill requires a process name"

    target = args[-1]

    # For -f flag, extract the first word as process name
    if " " in target:
        target = target.split()[0]

    if target in allowed_process_names:
        return True, ""
    return False, f"pkill only allowed for dev processes: {allowed_process_names}"


def validate_chmod_command(command_string: str) -> tuple[bool, str]:
    """
    Validate chmod commands - only allow making files executable with +x.

    Returns:
        Tuple of (is_allowed, reason_if_blocked)
    """
    try:
        tokens = shlex.split(command_string)
    except ValueError:
        return False, "Could not parse chmod command"

    if not tokens or tokens[0] != "chmod":
        return False, "Not a chmod command"

    mode = None
    files = []

    for token in tokens[1:]:
        if token.startswith("-"):
            return False, "chmod flags are not allowed"
        elif mode is None:
            mode = token
        else:
            files.append(token)

    if mode is None:
        return False, "chmod requires a mode"

    if not files:
        return False, "chmod requires at least one file"

    # Only allow +x variants (making files executable)
    if not re.match(r"^[ugoa]*\+x$", mode):
        return False, f"chmod only allowed with +x mode, got: {mode}"

    return True, ""


def validate_init_script(command_string: str) -> tuple[bool, str]:
    """
    Validate init.sh script execution - only allow ./init.sh.

    Returns:
        Tuple of (is_allowed, reason_if_blocked)
    """
    try:
        tokens = shlex.split(command_string)
    except ValueError:
        return False, "Could not parse init script command"

    if not tokens:
        return False, "Empty command"

    script = tokens[0]

    if script == "./init.sh" or script.endswith("/init.sh"):
        return True, ""

    return False, f"Only ./init.sh is allowed, got: {script}"


def validate_terraform_command(command_string: str) -> tuple[bool, str]:
    """
    Validate terraform commands - allow all standard operations.

    Returns:
        Tuple of (is_allowed, reason_if_blocked)
    """
    try:
        tokens = shlex.split(command_string)
    except ValueError:
        return False, "Could not parse terraform command"

    if not tokens or tokens[0] != "terraform":
        return False, "Not a terraform command"

    # All terraform subcommands are allowed
    return True, ""


def validate_aws_command(command_string: str) -> tuple[bool, str]:
    """
    Validate AWS CLI commands - block destructive IAM and account operations.

    Returns:
        Tuple of (is_allowed, reason_if_blocked)
    """
    try:
        tokens = shlex.split(command_string)
    except ValueError:
        return False, "Could not parse aws command"

    if not tokens or tokens[0] != "aws":
        return False, "Not an aws command"

    args = [t for t in tokens[1:] if not t.startswith("-")]

    if len(args) < 2:
        return True, ""  # Allow commands like "aws --version"

    service = args[0]
    operation = args[1]

    # Block dangerous IAM operations
    blocked_iam = {
        "delete-user", "delete-role", "delete-policy",
        "delete-access-key", "delete-account-alias",
        "delete-account-password-policy",
    }
    if service == "iam" and operation in blocked_iam:
        return False, f"aws iam {operation} is blocked for safety"

    # Block dangerous Organizations operations
    blocked_org = {
        "delete-organization", "leave-organization",
        "remove-account-from-organization",
    }
    if service == "organizations" and operation in blocked_org:
        return False, f"aws organizations {operation} is blocked for safety"

    # Block account closure
    if service == "account" and operation == "close-account":
        return False, "aws account close-account is blocked for safety"

    return True, ""


def validate_docker_command(command_string: str) -> tuple[bool, str]:
    """
    Validate Docker commands - block privileged mode and dangerous mounts.

    Returns:
        Tuple of (is_allowed, reason_if_blocked)
    """
    try:
        tokens = shlex.split(command_string)
    except ValueError:
        return False, "Could not parse docker command"

    if not tokens or tokens[0] not in ("docker", "docker-compose"):
        return False, "Not a docker command"

    # Block --privileged flag
    if "--privileged" in tokens:
        return False, "docker --privileged is blocked for security"

    # Block dangerous volume mounts
    dangerous_mounts = ["/", "/etc", "/var", "/root", "/home"]
    for i, token in enumerate(tokens):
        if token in ("-v", "--volume") and i + 1 < len(tokens):
            mount = tokens[i + 1]
            host_path = mount.split(":")[0] if ":" in mount else mount
            for dangerous in dangerous_mounts:
                if host_path == dangerous or host_path.startswith(dangerous + "/"):
                    if "/generations/" in host_path or "/project/" in host_path:
                        continue
                    return False, f"Mounting {host_path} is blocked for security"

    # Block --pid=host for docker
    if tokens[0] == "docker" and "--pid=host" in tokens:
        return False, "docker --pid=host is blocked for security"

    return True, ""


class BaseSecurity:
    """
    Base security class for command validation.

    Subclass this and define ALLOWED_COMMANDS and COMMANDS_NEEDING_EXTRA_VALIDATION
    for your project.
    """

    # Override in subclass
    ALLOWED_COMMANDS: set[str] = set()
    COMMANDS_NEEDING_EXTRA_VALIDATION: set[str] = set()

    # Mapping of command to validation function
    VALIDATORS: dict[str, Callable[[str], tuple[bool, str]]] = {
        "pkill": validate_pkill_command,
        "chmod": validate_chmod_command,
        "init.sh": validate_init_script,
        "terraform": validate_terraform_command,
        "aws": validate_aws_command,
        "docker": validate_docker_command,
        "docker-compose": validate_docker_command,
    }

    def validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate a bash command against the allowlist.

        Args:
            command: The full command string

        Returns:
            Tuple of (is_allowed, reason_if_blocked)
        """
        commands = extract_commands(command)

        if not commands:
            return False, f"Could not parse command for security validation: {command}"

        segments = split_command_segments(command)

        for cmd in commands:
            if cmd not in self.ALLOWED_COMMANDS:
                return False, f"Command '{cmd}' is not in the allowed commands list"

            if cmd in self.COMMANDS_NEEDING_EXTRA_VALIDATION:
                cmd_segment = self._get_command_segment(cmd, segments) or command
                validator = self.VALIDATORS.get(cmd)

                if validator:
                    allowed, reason = validator(cmd_segment)
                    if not allowed:
                        return False, reason

        return True, ""

    def _get_command_segment(self, cmd: str, segments: list[str]) -> str:
        """Find the specific command segment containing the given command."""
        for segment in segments:
            segment_commands = extract_commands(segment)
            if cmd in segment_commands:
                return segment
        return ""

    def create_hook(self) -> Callable:
        """
        Create a pre-tool-use hook for bash command validation.

        Returns:
            Async hook function for use with Claude SDK
        """
        async def bash_security_hook(input_data, tool_use_id=None, context=None):
            if input_data.get("tool_name") != "Bash":
                return {}

            command = input_data.get("tool_input", {}).get("command", "")
            if not command:
                return {}

            allowed, reason = self.validate_command(command)
            if not allowed:
                return {"decision": "block", "reason": reason}

            return {}

        return bash_security_hook
