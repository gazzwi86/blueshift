"""
Prompt Loading Utilities
========================

Functions for loading prompt templates from the prompts directory.
"""

import shutil
from pathlib import Path


class PromptLoader:
    """
    Loads prompt templates from a configurable directory.
    """

    def __init__(self, prompts_dir: Path = None):
        """
        Args:
            prompts_dir: Directory containing prompt templates.
                        Defaults to prompts/ in the package root.
        """
        if prompts_dir is None:
            # Default to prompts/ relative to this file's parent (lib/)
            prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompts_dir = prompts_dir

    def load(self, name: str) -> str:
        """
        Load a prompt template by name.

        Args:
            name: Prompt name (without extension)

        Returns:
            Prompt content as string
        """
        # Try .md first, then .txt
        md_path = self.prompts_dir / f"{name}.md"
        txt_path = self.prompts_dir / f"{name}.txt"

        if md_path.exists():
            return md_path.read_text()
        elif txt_path.exists():
            return txt_path.read_text()
        else:
            raise FileNotFoundError(f"Prompt not found: {name}")

    def get_initializer_prompt(self) -> str:
        """Load the initializer prompt."""
        return self.load("initializer_prompt")

    def get_coding_prompt(self) -> str:
        """Load the coding agent prompt."""
        return self.load("coding_prompt")

    def get_harness_capabilities(self) -> str:
        """Load the harness capabilities prompt."""
        return self.load("harness_capabilities")

    def get_app_spec(self) -> str:
        """Load the app specification."""
        return self.load("app_spec")

    def copy_spec_to_project(self, project_dir: Path) -> None:
        """
        Copy the app spec file into the project directory.

        Args:
            project_dir: Target project directory
        """
        spec_source = self.prompts_dir / "app_spec.txt"
        spec_dest = project_dir / "app_spec.txt"

        if spec_source.exists() and not spec_dest.exists():
            shutil.copy(spec_source, spec_dest)
            print(f"Copied app_spec.txt to {project_dir}")


# Default loader for backwards compatibility
_default_loader = None


def get_default_loader() -> PromptLoader:
    """Get the default prompt loader."""
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader()
    return _default_loader


def load_prompt(name: str) -> str:
    """Load a prompt template from the default prompts directory."""
    return get_default_loader().load(name)


def get_initializer_prompt() -> str:
    """Load the initializer prompt."""
    return get_default_loader().get_initializer_prompt()


def get_coding_prompt() -> str:
    """Load the coding agent prompt."""
    return get_default_loader().get_coding_prompt()


def copy_spec_to_project(project_dir: Path) -> None:
    """Copy the app spec file into the project directory."""
    get_default_loader().copy_spec_to_project(project_dir)
