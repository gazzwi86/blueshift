"""
Path Management
===============

Centralized path management for the Blueshift harness.
All file path logic should go through these functions.
"""

import os
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=1)
def get_harness_root() -> Path:
    """
    Get the root directory of the Blueshift harness.

    This can be overridden by setting the BLUESHIFT_ROOT environment variable.

    Returns:
        Path to the harness root directory
    """
    if env_root := os.environ.get("BLUESHIFT_ROOT"):
        return Path(env_root).resolve()

    # Default: parent of lib/ directory
    return Path(__file__).parent.parent.parent.resolve()


def get_project_context_dir() -> Path:
    """
    Get the project_context directory path.

    This is where project-specific configuration files live:
    - app_spec.txt
    - feature_list.json
    - harness_capabilities.md
    - stage_gates.md
    - workflow_template.md
    - hitl_history.json
    - logs/

    Returns:
        Path to the project_context directory
    """
    return get_harness_root() / "project_context"


def get_feature_list_path() -> Path:
    """
    Get the path to feature_list.json.

    The feature list is stored in project_context/ (not in generations/).

    Returns:
        Path to feature_list.json
    """
    return get_project_context_dir() / "feature_list.json"


def get_hitl_history_path() -> Path:
    """
    Get the path to hitl_history.json.

    HITL history is stored in project_context/ (not in generations/).

    Returns:
        Path to hitl_history.json
    """
    return get_project_context_dir() / "hitl_history.json"


def get_logs_dir() -> Path:
    """
    Get the path to the logs directory.

    Logs are stored in project_context/logs/ (not in generations/).

    Returns:
        Path to logs directory
    """
    logs_dir = get_project_context_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_examples_dir() -> Path:
    """
    Get the path to the examples directory.

    Contains sample app_spec.txt files for different project types.

    Returns:
        Path to examples directory
    """
    return get_harness_root() / "examples"


def get_generations_dir() -> Path:
    """
    Get the path to the generations directory.

    This is where generated projects are stored.

    Returns:
        Path to generations directory
    """
    return get_harness_root() / "generations"


def get_active_project_dir(project_name: str = None) -> Path:
    """
    Get the path to the active project directory.

    Args:
        project_name: Name of the project (optional, uses first dir in generations/)

    Returns:
        Path to the active project directory
    """
    generations = get_generations_dir()

    if project_name:
        return generations / project_name

    # Find first directory in generations/
    if generations.exists():
        for item in generations.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                return item

    return generations / "project"


def ensure_project_context_files() -> dict[str, bool]:
    """
    Ensure all required project_context files exist.

    Returns:
        Dict mapping filename to whether it exists
    """
    context_dir = get_project_context_dir()
    required_files = [
        "app_spec.txt",
        "harness_capabilities.md",
        "stage_gates.md",
        "workflow_template.md",
        "quality_framework.md",
    ]

    return {
        filename: (context_dir / filename).exists()
        for filename in required_files
    }
