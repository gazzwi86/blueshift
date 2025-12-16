"""
Security Framework

Provides command validation and security hooks for autonomous agent execution.
Base classes can be extended with project-specific allowlists.
"""

from .base import (
    BaseSecurity,
    split_command_segments,
    extract_commands,
    validate_pkill_command,
    validate_chmod_command,
    validate_init_script,
    validate_terraform_command,
    validate_aws_command,
    validate_docker_command,
)

__all__ = [
    "BaseSecurity",
    "split_command_segments",
    "extract_commands",
    "validate_pkill_command",
    "validate_chmod_command",
    "validate_init_script",
    "validate_terraform_command",
    "validate_aws_command",
    "validate_docker_command",
]
