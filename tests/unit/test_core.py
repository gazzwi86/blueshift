"""
Core Module Tests
=================

Unit tests for the core utilities (paths, types).
"""

import pytest
import os
from pathlib import Path
from datetime import datetime

from lib.core.paths import (
    get_harness_root,
    get_project_context_dir,
    get_feature_list_path,
    get_hitl_history_path,
    get_logs_dir,
)
from lib.core.types import (
    SessionStatus,
    ValidationLevel,
    ValidationResult,
    FeatureStatus,
    ProgressSnapshot,
    VerificationResult,
)


class TestPaths:
    """Tests for path management functions."""

    def test_get_harness_root(self):
        """Test getting harness root directory."""
        root = get_harness_root()
        assert root.exists()
        assert (root / "lib").exists()

    def test_get_harness_root_from_env(self, monkeypatch, tmp_path):
        """Test harness root from environment variable."""
        # Clear the lru_cache
        get_harness_root.cache_clear()

        monkeypatch.setenv("BLUESHIFT_ROOT", str(tmp_path))
        root = get_harness_root()
        assert root == tmp_path

        # Clean up
        monkeypatch.delenv("BLUESHIFT_ROOT")
        get_harness_root.cache_clear()

    def test_get_project_context_dir(self):
        """Test getting project_context directory."""
        context_dir = get_project_context_dir()
        assert context_dir.name == "project_context"
        assert context_dir.parent == get_harness_root()

    def test_get_feature_list_path(self):
        """Test feature list path."""
        path = get_feature_list_path()
        assert path.name == "feature_list.json"
        assert path.parent == get_project_context_dir()

    def test_get_hitl_history_path(self):
        """Test HITL history path."""
        path = get_hitl_history_path()
        assert path.name == "hitl_history.json"
        assert path.parent == get_project_context_dir()

    def test_get_logs_dir_creates_directory(self, temp_harness_root, monkeypatch):
        """Test that logs directory is created if it doesn't exist."""
        get_harness_root.cache_clear()
        monkeypatch.setenv("BLUESHIFT_ROOT", str(temp_harness_root))

        logs_dir = get_logs_dir()
        assert logs_dir.exists()
        assert logs_dir.is_dir()

        # Clean up
        monkeypatch.delenv("BLUESHIFT_ROOT")
        get_harness_root.cache_clear()


class TestTypes:
    """Tests for type definitions."""

    def test_session_status_values(self):
        """Test SessionStatus enum values."""
        assert SessionStatus.CONTINUE.value == "continue"
        assert SessionStatus.STOP.value == "stop"
        assert SessionStatus.ERROR.value == "error"
        assert SessionStatus.HITL.value == "hitl"

    def test_validation_level_values(self):
        """Test ValidationLevel enum values."""
        assert ValidationLevel.ERROR.value == "error"
        assert ValidationLevel.WARNING.value == "warning"
        assert ValidationLevel.INFO.value == "info"

    def test_validation_result_str(self):
        """Test ValidationResult string representation."""
        result = ValidationResult(
            passed=True,
            message="All good",
            level=ValidationLevel.INFO
        )
        assert "[INFO] All good" == str(result)

        result = ValidationResult(
            passed=False,
            message="Problem found",
            level=ValidationLevel.ERROR
        )
        assert "[ERROR] Problem found" == str(result)

    def test_validation_result_immutable(self):
        """Test that ValidationResult is immutable."""
        result = ValidationResult(passed=True, message="Test")
        with pytest.raises(AttributeError):
            result.passed = False

    def test_feature_status_immutable(self):
        """Test that FeatureStatus is immutable."""
        status = FeatureStatus(
            id="feat_001",
            title="Test Feature",
            category="tech_stack",
            passes=True
        )
        with pytest.raises(AttributeError):
            status.passes = False

    def test_progress_snapshot(self):
        """Test ProgressSnapshot properties."""
        snapshot = ProgressSnapshot(
            total_features=10,
            passing_features=8,
            categories={"tech_stack": (5, 5), "deployment": (3, 5)}
        )
        assert snapshot.completion_percentage == 80.0
        assert snapshot.is_complete is False

    def test_progress_snapshot_complete(self):
        """Test ProgressSnapshot when complete."""
        snapshot = ProgressSnapshot(
            total_features=10,
            passing_features=10,
            categories={}
        )
        assert snapshot.completion_percentage == 100.0
        assert snapshot.is_complete is True

    def test_progress_snapshot_empty(self):
        """Test ProgressSnapshot with no features."""
        snapshot = ProgressSnapshot(
            total_features=0,
            passing_features=0,
            categories={}
        )
        assert snapshot.completion_percentage == 0.0
        assert snapshot.is_complete is False

    def test_verification_result_to_dict(self):
        """Test VerificationResult serialization."""
        result = VerificationResult(
            passed=True,
            reason="All checks passed",
            exit_code=0
        )
        data = result.to_dict()
        assert data["passed"] is True
        assert data["reason"] == "All checks passed"
        assert data["exit_code"] == 0
        assert "timestamp" in data
