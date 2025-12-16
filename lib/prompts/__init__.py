"""
Prompt Loading Utilities
========================

Loads and combines:
- Generic prompt templates from lib/prompts/
- Project-specific context from project_context/
- Optional project-specific additions

Structure:
    lib/prompts/
        initializer_prompt.md    # Generic initializer template
        coding_prompt.md         # Generic coding template

    project_context/
        app_spec.txt             # Project specification (required)
        harness_capabilities.md  # Harness capabilities (required)
        init_additions.md        # Optional additions to initializer prompt
        coding_additions.md      # Optional additions to coding prompt
"""

import shutil
from pathlib import Path
from typing import Optional


class PromptLoader:
    """
    Loads and combines prompt templates.

    Generic templates are in lib/prompts/.
    Project-specific context is in project_context/.
    """

    def __init__(
        self,
        generic_prompts_dir: Optional[Path] = None,
        project_context_dir: Optional[Path] = None,
    ):
        """
        Args:
            generic_prompts_dir: Directory containing generic prompt templates.
                                Defaults to lib/prompts/.
            project_context_dir: Directory containing project-specific context.
                                Defaults to project_context/.
        """
        if generic_prompts_dir is None:
            # lib/prompts/ is the same directory as this file
            generic_prompts_dir = Path(__file__).parent
        if project_context_dir is None:
            # project_context/ is at the repo root
            project_context_dir = Path(__file__).parent.parent.parent / "project_context"

        self.generic_prompts_dir = generic_prompts_dir
        self.project_context_dir = project_context_dir

    def _load_file(self, directory: Path, name: str, extensions: list[str] = None) -> Optional[str]:
        """
        Load a file from a directory, trying multiple extensions.

        Returns None if file doesn't exist.
        """
        if extensions is None:
            extensions = [".md", ".txt"]

        for ext in extensions:
            path = directory / f"{name}{ext}"
            if path.exists():
                return path.read_text()

        return None

    def _load_required(self, directory: Path, name: str) -> str:
        """Load a required file, raising if not found."""
        content = self._load_file(directory, name)
        if content is None:
            raise FileNotFoundError(
                f"Required file not found: {name} in {directory}"
            )
        return content

    def get_initializer_prompt(self) -> str:
        """
        Load the complete initializer prompt.

        Combines:
        1. Generic initializer template (lib/prompts/initializer_prompt.md)
        2. Optional project additions (project_context/init_additions.md)
        """
        # Load generic template
        generic = self._load_required(self.generic_prompts_dir, "initializer_prompt")

        # Load optional project-specific additions
        additions = self._load_file(self.project_context_dir, "init_additions")

        if additions:
            return f"{generic}\n\n---\n\n## PROJECT-SPECIFIC ADDITIONS\n\n{additions}"
        return generic

    def get_coding_prompt(self) -> str:
        """
        Load the complete coding prompt.

        Combines:
        1. Generic coding template (lib/prompts/coding_prompt.md)
        2. Optional project additions (project_context/coding_additions.md)
        """
        # Load generic template
        generic = self._load_required(self.generic_prompts_dir, "coding_prompt")

        # Load optional project-specific additions
        additions = self._load_file(self.project_context_dir, "coding_additions")

        if additions:
            return f"{generic}\n\n---\n\n## PROJECT-SPECIFIC ADDITIONS\n\n{additions}"
        return generic

    def get_harness_capabilities(self) -> str:
        """Load the harness capabilities from project context."""
        return self._load_required(self.project_context_dir, "harness_capabilities")

    def get_app_spec(self) -> str:
        """Load the app specification from project context."""
        return self._load_required(self.project_context_dir, "app_spec")

    def copy_context_to_project(self, project_dir: Path) -> None:
        """
        Copy project context files into the project directory.

        Copies:
        - app_spec.txt
        - harness_capabilities.md
        - workflow_template.md
        - stage_gates.md

        Args:
            project_dir: Target project directory
        """
        files_to_copy = [
            "app_spec.txt",
            "harness_capabilities.md",
            "workflow_template.md",
            "stage_gates.md",
        ]

        for filename in files_to_copy:
            source = self.project_context_dir / filename
            dest = project_dir / filename

            if source.exists() and not dest.exists():
                shutil.copy(source, dest)
                print(f"Copied {filename} to {project_dir}")

    def has_project_additions(self) -> dict[str, bool]:
        """Check which optional project additions exist."""
        return {
            "init_additions": (self.project_context_dir / "init_additions.md").exists(),
            "coding_additions": (self.project_context_dir / "coding_additions.md").exists(),
        }


# Default loader for backwards compatibility
_default_loader = None


def get_default_loader() -> PromptLoader:
    """Get the default prompt loader."""
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader()
    return _default_loader


def get_initializer_prompt() -> str:
    """Load the initializer prompt."""
    return get_default_loader().get_initializer_prompt()


def get_coding_prompt() -> str:
    """Load the coding agent prompt."""
    return get_default_loader().get_coding_prompt()


def copy_spec_to_project(project_dir: Path) -> None:
    """Copy project context files into the project directory."""
    get_default_loader().copy_context_to_project(project_dir)
