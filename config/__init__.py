"""
Configuration
=============

Centralized configuration for the Blueshift harness.
"""

from .security_allowlist import ALLOWED_COMMANDS, is_command_allowed

__all__ = [
    "ALLOWED_COMMANDS",
    "is_command_allowed",
]
