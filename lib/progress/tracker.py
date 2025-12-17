"""
Progress Tracking Utilities
===========================

Functions for tracking and displaying progress of the autonomous coding agent.
"""

import json
from pathlib import Path
from typing import Optional


def count_passing_tests(project_dir: Path) -> tuple[int, int]:
    """
    Count passing and total tests in feature_list.json.

    Args:
        project_dir: Directory containing feature_list.json

    Returns:
        (passing_count, total_count)
    """
    tests_file = project_dir / "feature_list.json"

    if not tests_file.exists():
        return 0, 0

    try:
        with open(tests_file, "r") as f:
            data = json.load(f)

        # Handle both formats: list of tests or object with "tests" key
        if isinstance(data, list):
            tests = data
        elif isinstance(data, dict) and "tests" in data:
            tests = data["tests"]
        else:
            return 0, 0

        total = len(tests)
        passing = sum(1 for test in tests if isinstance(test, dict) and test.get("passes", False))

        return passing, total
    except (json.JSONDecodeError, IOError):
        return 0, 0


def count_by_category(project_dir: Path) -> dict[str, tuple[int, int]]:
    """
    Count passing/total tests by category.

    Args:
        project_dir: Directory containing feature_list.json

    Returns:
        Dict mapping category -> (passing, total)
    """
    tests_file = project_dir / "feature_list.json"

    if not tests_file.exists():
        return {}

    try:
        with open(tests_file, "r") as f:
            data = json.load(f)

        # Handle both formats: list of tests or object with "tests" key
        if isinstance(data, list):
            tests = data
        elif isinstance(data, dict) and "tests" in data:
            tests = data["tests"]
        else:
            return {}

        categories = {}
        for test in tests:
            if not isinstance(test, dict):
                continue
            cat = test.get("category", "unknown")
            if cat not in categories:
                categories[cat] = [0, 0]
            categories[cat][1] += 1
            if test.get("passes", False):
                categories[cat][0] += 1

        return {k: tuple(v) for k, v in categories.items()}
    except (json.JSONDecodeError, IOError):
        return {}


def print_session_header(session_num: int, is_initializer: bool) -> None:
    """Print a formatted header for the session."""
    session_type = "INITIALIZER" if is_initializer else "CODING AGENT"

    print("\n" + "=" * 70)
    print(f"  SESSION {session_num}: {session_type}")
    print("=" * 70)
    print()


def print_progress_summary(project_dir: Path) -> None:
    """Print a summary of current progress."""
    passing, total = count_passing_tests(project_dir)

    if total > 0:
        percentage = (passing / total) * 100
        print(f"\nProgress: {passing}/{total} tests passing ({percentage:.1f}%)")

        # Show breakdown by category
        categories = count_by_category(project_dir)
        if categories:
            print("\nBy category:")
            for cat, (cat_passing, cat_total) in sorted(categories.items()):
                pct = (cat_passing / cat_total * 100) if cat_total else 0
                print(f"  {cat}: {cat_passing}/{cat_total} ({pct:.0f}%)")
    else:
        print("\nProgress: feature_list.json not yet created")


class ProgressTracker:
    """
    Tracks and persists agent progress across sessions.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.progress_file = project_dir / "claude-progress.txt"

    def get_session_count(self) -> int:
        """Get the current session count from progress file."""
        if not self.progress_file.exists():
            return 0

        try:
            content = self.progress_file.read_text()
            # Look for "Session X" pattern
            import re
            matches = re.findall(r"Session (\d+)", content)
            if matches:
                return max(int(m) for m in matches)
        except Exception:
            pass

        return 0

    def get_passing_tests(self) -> tuple[int, int]:
        """Get (passing, total) test counts."""
        return count_passing_tests(self.project_dir)

    def get_by_category(self) -> dict[str, tuple[int, int]]:
        """Get test counts by category."""
        return count_by_category(self.project_dir)

    def is_first_run(self) -> bool:
        """Check if this is the first run (no feature_list.json)."""
        return not (self.project_dir / "feature_list.json").exists()

    def update_progress(self, session_num: int, status: str, notes: str = "") -> None:
        """
        Update the progress file.

        Args:
            session_num: Current session number
            status: Status (IN_PROGRESS, HALTED, COMPLETED)
            notes: Additional notes
        """
        passing, total = self.get_passing_tests()

        content = f"""Session {session_num}
{'=' * 40}
Status: {status}

Progress: {passing}/{total} tests passing

{notes}
"""

        # Append to existing or create new
        mode = "a" if self.progress_file.exists() else "w"
        with open(self.progress_file, mode) as f:
            f.write("\n" + content)

    def mark_hitl_checkpoint(self, checkpoint_name: str, description: str) -> None:
        """Mark that a HITL checkpoint was reached."""
        self.update_progress(
            self.get_session_count(),
            "HALTED - Awaiting HITL approval",
            f"Checkpoint: {checkpoint_name}\n{description}"
        )
