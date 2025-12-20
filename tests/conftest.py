"""
Test Fixtures
=============

Shared fixtures for all test modules.
Uses pytest fixtures with mocking for AWS, Terraform, and Claude SDK.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Generator

import pytest


# ============================================================================
# Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_harness_root(tmp_path: Path) -> Path:
    """Create a temporary harness root with project_context."""
    harness_root = tmp_path / "harness"
    harness_root.mkdir()

    # Create project_context
    project_context = harness_root / "project_context"
    project_context.mkdir()

    # Create minimal required files
    (project_context / "app_spec.txt").write_text("<project>\nTest Project\n</project>")
    (project_context / "harness_capabilities.md").write_text("# Capabilities\n")
    (project_context / "stage_gates.md").write_text("# Stage Gates\n")
    (project_context / "workflow_template.md").write_text("# Workflow\n")

    return harness_root


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_feature_list() -> dict:
    """Sample feature_list.json for testing."""
    return {
        "project": "Test Project",
        "generated_by": "test",
        "generated_date": "2025-01-01",
        "total_features": 5,
        "categories": {
            "tech_stack": 2,
            "deployment": 2,
            "evaluation": 1
        },
        "features": [
            {
                "id": "feat_001",
                "category": "tech_stack",
                "title": "Python 3.12 configured",
                "passes": True,
                "dod_checklist": {
                    "code_complete": True,
                    "unit_tests_pass": True
                }
            },
            {
                "id": "feat_002",
                "category": "tech_stack",
                "title": "pytest configured",
                "passes": True,
                "dod_checklist": {
                    "code_complete": True,
                    "unit_tests_pass": True
                }
            },
            {
                "id": "feat_003",
                "category": "deployment",
                "title": "Terraform modules exist",
                "passes": False,
                "dod_checklist": {
                    "code_complete": True,
                    "unit_tests_pass": True,
                    "deployed": False
                }
            },
            {
                "id": "feat_004",
                "category": "deployment",
                "title": "Agent deployed",
                "passes": False,
                "dod_checklist": {
                    "code_complete": False,
                    "deployed": False
                }
            },
            {
                "id": "feat_005",
                "category": "evaluation",
                "title": "Evaluation passes",
                "passes": False,
                "dod_checklist": {
                    "evaluation_threshold_met": False
                }
            }
        ]
    }


@pytest.fixture
def sample_app_spec() -> str:
    """Sample app_spec.txt content."""
    return """
<project_specification>
    <project_name>Test Project</project_name>
    <overview>
        A simple test project for the Blueshift harness.
    </overview>
    <technology_stack>
        <languages>Python 3.12</languages>
        <frameworks>pytest</frameworks>
    </technology_stack>
    <testing_strategy>
        <unit_tests>pytest</unit_tests>
        <coverage_target>80%</coverage_target>
    </testing_strategy>
</project_specification>
"""


@pytest.fixture
def sample_credentials() -> dict:
    """Sample credentials for testing."""
    return {
        "anthropic_api_key": "sk-test-key-12345",
        "aws_profile": "test-profile",
        "aws_region": "us-east-1",
        "github_token": "ghp_test_token",
    }


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_aws_client():
    """Mock boto3 client for AWS operations."""
    with patch('boto3.client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_terraform():
    """Mock terraform subprocess calls."""
    with patch('subprocess.run') as mock:
        mock.return_value = MagicMock(
            returncode=0,
            stdout="No changes. Infrastructure is up-to-date.",
            stderr=""
        )
        yield mock


@pytest.fixture
def mock_agentcore():
    """Mock agentcore CLI calls."""
    with patch('subprocess.run') as mock:
        def side_effect(cmd, **kwargs):
            result = MagicMock()
            if 'status' in cmd:
                result.returncode = 0
                result.stdout = "Agent Status: READY"
            elif 'invoke' in cmd:
                result.returncode = 0
                result.stdout = '{"response": "Hello!"}'
            else:
                result.returncode = 0
                result.stdout = ""
            return result

        mock.side_effect = side_effect
        yield mock


@pytest.fixture
def mock_claude_sdk():
    """Mock Claude Code SDK client."""
    with patch('claude_code_sdk.ClaudeSDKClient') as mock_class:
        client = AsyncMock()
        client.query = AsyncMock()
        client.receive_response = AsyncMock(return_value=iter([]))
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)

        mock_class.return_value = client
        yield client


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    monkeypatch.setenv("AWS_PROFILE", "test-profile")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("MOCK_SERVICES", "true")


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all credential-related environment variables."""
    for key in ["ANTHROPIC_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
                "AWS_PROFILE", "SLACK_BOT_TOKEN", "GITHUB_TOKEN"]:
        monkeypatch.delenv(key, raising=False)


# ============================================================================
# Project Setup Fixtures
# ============================================================================

@pytest.fixture
def project_with_feature_list(temp_project_dir: Path, sample_feature_list: dict) -> Path:
    """Create a project directory with feature_list.json."""
    feature_file = temp_project_dir / "feature_list.json"
    feature_file.write_text(json.dumps(sample_feature_list, indent=2))
    return temp_project_dir


@pytest.fixture
def complete_project(temp_project_dir: Path) -> Path:
    """Create a project with all features passing."""
    feature_list = {
        "total_features": 3,
        "features": [
            {"id": "1", "category": "tech_stack", "passes": True,
             "dod_checklist": {"code_complete": True, "unit_tests_pass": True}},
            {"id": "2", "category": "tech_stack", "passes": True,
             "dod_checklist": {"code_complete": True, "unit_tests_pass": True}},
            {"id": "3", "category": "tech_stack", "passes": True,
             "dod_checklist": {"code_complete": True, "unit_tests_pass": True}},
        ]
    }
    (temp_project_dir / "feature_list.json").write_text(json.dumps(feature_list))
    return temp_project_dir
