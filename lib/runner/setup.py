"""
Project Setup
=============

Functions for setting up a new project directory.
"""

import subprocess
import shutil
from pathlib import Path


def initialize_git_repository(project_dir: Path) -> bool:
    """
    Initialize a git repository in the project directory.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if successful, False otherwise
    """
    project_git_dir = project_dir / ".git"

    if project_git_dir.exists():
        return True  # Already initialized

    result = subprocess.run(
        ["git", "init"],
        cwd=project_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Warning: git init failed: {result.stderr}")
        return False

    print(f"Created git repository in {project_dir}")
    return True


def create_gitignore(project_dir: Path) -> None:
    """
    Create a .gitignore file for the project.

    Args:
        project_dir: Path to the project directory
    """
    gitignore = project_dir / ".gitignore"

    if gitignore.exists():
        return

    gitignore.write_text(
        "# Python\n"
        "__pycache__/\n"
        "*.pyc\n"
        ".venv/\n"
        "venv/\n"
        "\n"
        "# Environment\n"
        ".env\n"
        ".env.local\n"
        "\n"
        "# IDE\n"
        ".idea/\n"
        ".vscode/\n"
        "\n"
        "# Logs\n"
        "logs/\n"
        "*.log\n"
        "\n"
        "# Terraform\n"
        ".terraform/\n"
        "*.tfstate*\n"
        "\n"
        "# Node\n"
        "node_modules/\n"
    )
    print("Created .gitignore")


def copy_env_file(project_dir: Path, harness_root: Path = None) -> bool:
    """
    Copy .env file from harness to project directory.

    Args:
        project_dir: Path to the project directory
        harness_root: Path to the harness root (optional)

    Returns:
        True if copied, False otherwise
    """
    if harness_root is None:
        from ..core.paths import get_harness_root
        harness_root = get_harness_root()

    harness_env = harness_root / ".env"
    project_env = project_dir / ".env"

    if harness_env.exists() and not project_env.exists():
        shutil.copy(harness_env, project_env)
        print(f"Copied .env to {project_dir}")
        print("  (The agent can modify this for project-specific needs)")
        return True

    return False


def setup_project_directory(project_dir: Path) -> None:
    """
    Set up a new project directory with all necessary files.

    Args:
        project_dir: Path to the project directory
    """
    # Create directory
    project_dir.mkdir(parents=True, exist_ok=True)

    # Initialize git
    if initialize_git_repository(project_dir):
        create_gitignore(project_dir)

    # Copy .env
    copy_env_file(project_dir)

    print()
