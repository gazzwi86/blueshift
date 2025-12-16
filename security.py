"""
Security Hooks for Autonomous Coding Agent
==========================================

Pre-tool-use hooks that validate bash commands for security.
Uses an allowlist approach - only explicitly permitted commands can run.
"""

import os
import shlex


# Allowed commands for development tasks
ALLOWED_COMMANDS = {
    # File inspection
    "ls",
    "cat",
    "head",
    "tail",
    "wc",
    "grep",
    # File operations (agent uses SDK tools for most file ops, but cp/mkdir needed occasionally)
    "cp",
    "mkdir",
    "chmod",  # For making scripts executable; validated separately
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
    "pkill",  # For killing dev servers; validated separately
    # Script execution
    "init.sh",  # Init scripts; validated separately
    # Infrastructure (validated separately)
    "terraform",
    "aws",
    # GitHub
    "gh",
    # Testing
    "pytest",
    "python",
    "python3",
    # Docker (validated separately)
    "docker",
    "docker-compose",
    # Package management
    "pip",
    "pip3",
    "uv",
    "uvx",
}

# Commands that need additional validation even when in the allowlist
COMMANDS_NEEDING_EXTRA_VALIDATION = {
    "pkill",
    "chmod",
    "init.sh",
    "terraform",
    "aws",
    "docker",
    "docker-compose",
}


def split_command_segments(command_string: str) -> list[str]:
    """
    Split a compound command into individual command segments.

    Handles command chaining (&&, ||, ;) but not pipes (those are single commands).

    Args:
        command_string: The full shell command

    Returns:
        List of individual command segments
    """
    import re

    # Split on && and || while preserving the ability to handle each segment
    # This regex splits on && or || that aren't inside quotes
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

    # shlex doesn't treat ; as a separator, so we need to pre-process
    import re

    # Split on semicolons that aren't inside quotes (simple heuristic)
    # This handles common cases like "echo hello; ls"
    segments = re.split(r'(?<!["\'])\s*;\s*(?!["\'])', command_string)

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        try:
            tokens = shlex.split(segment)
        except ValueError:
            # Malformed command (unclosed quotes, etc.)
            # Return empty to trigger block (fail-safe)
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
                "if",
                "then",
                "else",
                "elif",
                "fi",
                "for",
                "while",
                "until",
                "do",
                "done",
                "case",
                "esac",
                "in",
                "!",
                "{",
                "}",
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

    Uses shlex to parse the command, avoiding regex bypass vulnerabilities.

    Returns:
        Tuple of (is_allowed, reason_if_blocked)
    """
    # Allowed process names for pkill
    allowed_process_names = {
        "node",
        "npm",
        "npx",
        "vite",
        "next",
    }

    try:
        tokens = shlex.split(command_string)
    except ValueError:
        return False, "Could not parse pkill command"

    if not tokens:
        return False, "Empty pkill command"

    # Separate flags from arguments
    args = []
    for token in tokens[1:]:
        if not token.startswith("-"):
            args.append(token)

    if not args:
        return False, "pkill requires a process name"

    # The target is typically the last non-flag argument
    target = args[-1]

    # For -f flag (full command line match), extract the first word as process name
    # e.g., "pkill -f 'node server.js'" -> target is "node server.js", process is "node"
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

    # Look for the mode argument
    # Valid modes: +x, u+x, a+x, etc. (anything ending with +x for execute permission)
    mode = None
    files = []

    for token in tokens[1:]:
        if token.startswith("-"):
            # Skip flags like -R (we don't allow recursive chmod anyway)
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
    # This matches: +x, u+x, g+x, o+x, a+x, ug+x, etc.
    import re

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

    # The command should be exactly ./init.sh (possibly with arguments)
    script = tokens[0]

    # Allow ./init.sh or paths ending in /init.sh
    if script == "./init.sh" or script.endswith("/init.sh"):
        return True, ""

    return False, f"Only ./init.sh is allowed, got: {script}"


def validate_terraform_command(command_string: str) -> tuple[bool, str]:
    """
    Validate terraform commands - allow all standard operations.

    Terraform destroy is allowed (user confirmed).

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
    # Including: init, plan, apply, destroy, output, state, etc.
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

    # Get the service and operation
    # Format: aws <service> <operation> [options]
    args = [t for t in tokens[1:] if not t.startswith("-")]

    if len(args) < 2:
        # Allow commands like "aws --version" or "aws configure"
        return True, ""

    service = args[0]
    operation = args[1]

    # Block dangerous IAM operations
    blocked_iam_operations = {
        "delete-user",
        "delete-role",
        "delete-policy",
        "delete-access-key",
        "delete-account-alias",
        "delete-account-password-policy",
    }
    if service == "iam" and operation in blocked_iam_operations:
        return False, f"aws iam {operation} is blocked for safety"

    # Block dangerous Organizations operations
    blocked_org_operations = {
        "delete-organization",
        "leave-organization",
        "remove-account-from-organization",
    }
    if service == "organizations" and operation in blocked_org_operations:
        return False, f"aws organizations {operation} is blocked for safety"

    # Block account closure
    if service == "account" and operation == "close-account":
        return False, "aws account close-account is blocked for safety"

    # All other AWS operations are allowed
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
            # Check if mounting a dangerous host path
            host_path = mount.split(":")[0] if ":" in mount else mount
            for dangerous in dangerous_mounts:
                if host_path == dangerous or host_path.startswith(dangerous + "/"):
                    # Allow if it's clearly a project subdirectory
                    if "/generations/" in host_path or "/project/" in host_path:
                        continue
                    return False, f"Mounting {host_path} is blocked for security"

    # Block --pid=host and --network=host for non-compose
    if tokens[0] == "docker":
        if "--pid=host" in tokens:
            return False, "docker --pid=host is blocked for security"

    return True, ""


def get_command_for_validation(cmd: str, segments: list[str]) -> str:
    """
    Find the specific command segment that contains the given command.

    Args:
        cmd: The command name to find
        segments: List of command segments

    Returns:
        The segment containing the command, or empty string if not found
    """
    for segment in segments:
        segment_commands = extract_commands(segment)
        if cmd in segment_commands:
            return segment
    return ""


async def bash_security_hook(input_data, tool_use_id=None, context=None):
    """
    Pre-tool-use hook that validates bash commands using an allowlist.

    Only commands in ALLOWED_COMMANDS are permitted.

    Args:
        input_data: Dict containing tool_name and tool_input
        tool_use_id: Optional tool use ID
        context: Optional context

    Returns:
        Empty dict to allow, or {"decision": "block", "reason": "..."} to block
    """
    if input_data.get("tool_name") != "Bash":
        return {}

    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        return {}

    # Extract all commands from the command string
    commands = extract_commands(command)

    if not commands:
        # Could not parse - fail safe by blocking
        return {
            "decision": "block",
            "reason": f"Could not parse command for security validation: {command}",
        }

    # Split into segments for per-command validation
    segments = split_command_segments(command)

    # Check each command against the allowlist
    for cmd in commands:
        if cmd not in ALLOWED_COMMANDS:
            return {
                "decision": "block",
                "reason": f"Command '{cmd}' is not in the allowed commands list",
            }

        # Additional validation for sensitive commands
        if cmd in COMMANDS_NEEDING_EXTRA_VALIDATION:
            # Find the specific segment containing this command
            cmd_segment = get_command_for_validation(cmd, segments)
            if not cmd_segment:
                cmd_segment = command  # Fallback to full command

            if cmd == "pkill":
                allowed, reason = validate_pkill_command(cmd_segment)
                if not allowed:
                    return {"decision": "block", "reason": reason}
            elif cmd == "chmod":
                allowed, reason = validate_chmod_command(cmd_segment)
                if not allowed:
                    return {"decision": "block", "reason": reason}
            elif cmd == "init.sh":
                allowed, reason = validate_init_script(cmd_segment)
                if not allowed:
                    return {"decision": "block", "reason": reason}
            elif cmd == "terraform":
                allowed, reason = validate_terraform_command(cmd_segment)
                if not allowed:
                    return {"decision": "block", "reason": reason}
            elif cmd == "aws":
                allowed, reason = validate_aws_command(cmd_segment)
                if not allowed:
                    return {"decision": "block", "reason": reason}
            elif cmd in ("docker", "docker-compose"):
                allowed, reason = validate_docker_command(cmd_segment)
                if not allowed:
                    return {"decision": "block", "reason": reason}

    return {}
