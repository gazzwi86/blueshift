"""
Agent Runner
=============

Core runner logic for the autonomous agent loop.
Extracted from start.py for better modularity.
"""

from .autonomous import run_autonomous_agent
from .setup import setup_project_directory, initialize_git_repository

__all__ = [
    "run_autonomous_agent",
    "setup_project_directory",
    "initialize_git_repository",
]
