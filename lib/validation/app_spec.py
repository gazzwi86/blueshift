"""
App Specification Validator
===========================

Validates that app_spec.txt contains all required sections with sufficient detail.
This ensures all research is done upfront, eliminating the need for runtime web searches.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SectionRequirement:
    """Defines requirements for a section in app_spec.txt."""
    name: str
    tag: str
    description: str
    min_chars: int = 100
    required_subsections: list[str] = field(default_factory=list)
    required_keywords: list[str] = field(default_factory=list)


@dataclass
class SectionValidation:
    """Result of validating a single section."""
    name: str
    found: bool
    char_count: int = 0
    missing_subsections: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.found and not self.error and not self.missing_subsections and not self.missing_keywords


@dataclass
class ValidationResult:
    """Overall validation result."""
    valid: bool
    sections: list[SectionValidation]
    errors: list[str]
    warnings: list[str]

    def summary(self) -> str:
        """Return a human-readable summary."""
        lines = []
        for section in self.sections:
            status = "[OK]" if section.passed else "[FAIL]"
            lines.append(f"  {status} {section.name} ({section.char_count} chars)")
            if section.missing_subsections:
                lines.append(f"        Missing subsections: {', '.join(section.missing_subsections)}")
            if section.missing_keywords:
                lines.append(f"        Missing keywords: {', '.join(section.missing_keywords)}")
            if section.error:
                lines.append(f"        Error: {section.error}")
        return "\n".join(lines)


# Required sections for a complete app_spec.txt
REQUIRED_SECTIONS = [
    SectionRequirement(
        name="Overview",
        tag="overview",
        description="High-level project description",
        min_chars=100,
    ),
    SectionRequirement(
        name="Technology Stack",
        tag="technology_stack",
        description="Technology decisions and frameworks",
        min_chars=200,
        required_keywords=["framework", "model"],
    ),
    SectionRequirement(
        name="Testing Strategy",
        tag="testing_strategy",
        description="How testing will be performed",
        min_chars=150,
        required_subsections=["unit_testing", "integration_testing"],
        required_keywords=["framework", "coverage", "mock"],
    ),
    SectionRequirement(
        name="Evaluation Test Cases",
        tag="evaluation_test_cases",
        description="Concrete test scenarios",
        min_chars=200,
    ),
    SectionRequirement(
        name="Data Schema",
        tag="data_schema",
        description="Data structures and storage",
        min_chars=100,
    ),
    SectionRequirement(
        name="Agent Tools",
        tag="agent_tools",
        description="Tool definitions with inputs/outputs",
        min_chars=100,
    ),
    SectionRequirement(
        name="Implementation Phases",
        tag="implementation_phases",
        description="Phased development approach",
        min_chars=100,
    ),
    SectionRequirement(
        name="Success Criteria",
        tag="success_criteria",
        description="Measurable success metrics",
        min_chars=100,
    ),
    SectionRequirement(
        name="Architecture Decisions",
        tag="architecture_decisions",
        description="Pre-researched technical decisions (ADRs)",
        min_chars=100,
    ),
]

# Optional but recommended sections
OPTIONAL_SECTIONS = [
    SectionRequirement(
        name="Users/Personas",
        tag="users_personas",
        description="Target user personas",
        min_chars=50,
    ),
    SectionRequirement(
        name="Error Handling",
        tag="error_handling",
        description="Error handling strategies",
        min_chars=100,
    ),
    SectionRequirement(
        name="Infrastructure",
        tag="infrastructure",
        description="Infrastructure requirements",
        min_chars=100,
    ),
]


class AppSpecValidator:
    """Validates app_spec.txt for completeness and sufficient detail."""

    def __init__(self, app_spec_path: Path):
        self.path = app_spec_path
        self.content = ""

    def load(self) -> bool:
        """Load the app_spec.txt file."""
        if not self.path.exists():
            return False
        self.content = self.path.read_text()
        return True

    def _extract_section(self, tag: str) -> Optional[str]:
        """Extract content between XML tags."""
        pattern = rf"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, self.content, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _check_subsections(self, content: str, subsections: list[str]) -> list[str]:
        """Check for required subsections, return missing ones."""
        missing = []
        for sub in subsections:
            pattern = rf"<{sub}>"
            if not re.search(pattern, content, re.IGNORECASE):
                missing.append(sub)
        return missing

    def _check_keywords(self, content: str, keywords: list[str]) -> list[str]:
        """Check for required keywords, return missing ones."""
        missing = []
        content_lower = content.lower()
        for kw in keywords:
            if kw.lower() not in content_lower:
                missing.append(kw)
        return missing

    def validate_section(self, requirement: SectionRequirement) -> SectionValidation:
        """Validate a single section against its requirements."""
        content = self._extract_section(requirement.tag)

        if content is None:
            return SectionValidation(
                name=requirement.name,
                found=False,
                error=f"Section <{requirement.tag}> not found"
            )

        char_count = len(content)
        validation = SectionValidation(
            name=requirement.name,
            found=True,
            char_count=char_count,
        )

        # Check minimum length
        if char_count < requirement.min_chars:
            validation.error = f"Insufficient detail ({char_count} chars, need {requirement.min_chars})"

        # Check subsections
        if requirement.required_subsections:
            validation.missing_subsections = self._check_subsections(
                content, requirement.required_subsections
            )

        # Check keywords
        if requirement.required_keywords:
            validation.missing_keywords = self._check_keywords(
                content, requirement.required_keywords
            )

        return validation

    def validate(self) -> ValidationResult:
        """Validate the entire app_spec.txt."""
        errors = []
        warnings = []
        sections = []

        if not self.load():
            return ValidationResult(
                valid=False,
                sections=[],
                errors=[f"app_spec.txt not found at {self.path}"],
                warnings=[],
            )

        # Validate required sections
        for req in REQUIRED_SECTIONS:
            result = self.validate_section(req)
            sections.append(result)
            if not result.passed:
                errors.append(f"{req.name}: {result.error or 'validation failed'}")

        # Check optional sections (warnings only)
        for opt in OPTIONAL_SECTIONS:
            result = self.validate_section(opt)
            if not result.found:
                warnings.append(f"Optional section <{opt.tag}> not found")

        return ValidationResult(
            valid=len(errors) == 0,
            sections=sections,
            errors=errors,
            warnings=warnings,
        )


def validate_app_spec(project_context_dir: Path) -> ValidationResult:
    """
    Convenience function to validate app_spec.txt in a project context directory.

    Args:
        project_context_dir: Path to the project_context/ directory

    Returns:
        ValidationResult with validation status and details
    """
    app_spec_path = project_context_dir / "app_spec.txt"
    validator = AppSpecValidator(app_spec_path)
    return validator.validate()
