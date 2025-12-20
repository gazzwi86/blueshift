"""
HITL Tests
==========

Unit tests for the Human-in-the-Loop system.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from lib.hitl.types import HITLDecision, HITLResponse
from lib.hitl.checkpoint import HITLCheckpoint
from lib.hitl.manager import HITLManager, reset_manager


class TestHITLTypes:
    """Tests for HITL type definitions."""

    def test_hitl_response_approve(self):
        """Test HITLResponse with approve decision."""
        response = HITLResponse(decision=HITLDecision.APPROVE)
        assert response.approved is True
        assert response.has_feedback is False

    def test_hitl_response_deny(self):
        """Test HITLResponse with deny decision."""
        response = HITLResponse(
            decision=HITLDecision.DENY,
            denial_reason="Not ready"
        )
        assert response.approved is False
        assert response.denial_reason == "Not ready"

    def test_hitl_response_amend(self):
        """Test HITLResponse with amend decision."""
        response = HITLResponse(
            decision=HITLDecision.AMEND,
            feedback="Please fix X"
        )
        assert response.approved is True
        assert response.has_feedback is True
        assert response.feedback == "Please fix X"

    def test_hitl_response_to_dict(self):
        """Test serialization of HITLResponse."""
        response = HITLResponse(
            decision=HITLDecision.APPROVE,
            feedback="Good job"
        )
        data = response.to_dict()
        assert data["decision"] == "approve"
        assert data["feedback"] == "Good job"
        assert "timestamp" in data

    def test_hitl_response_from_dict(self):
        """Test deserialization of HITLResponse."""
        data = {
            "decision": "deny",
            "denial_reason": "Not ready",
            "timestamp": "2025-01-01T00:00:00"
        }
        response = HITLResponse.from_dict(data)
        assert response.decision == HITLDecision.DENY
        assert response.denial_reason == "Not ready"


class TestHITLCheckpoint:
    """Tests for HITLCheckpoint class."""

    @patch('builtins.input', return_value='A')
    def test_prompt_decision_approve(self, mock_input):
        """Test approving a checkpoint via CLI."""
        checkpoint = HITLCheckpoint(
            name="test",
            description="Test checkpoint"
        )
        response = checkpoint.prompt_decision()
        assert response.decision == HITLDecision.APPROVE

    @patch('builtins.input', side_effect=['D', 'Not ready'])
    def test_prompt_decision_deny(self, mock_input):
        """Test denying a checkpoint via CLI."""
        checkpoint = HITLCheckpoint(
            name="test",
            description="Test checkpoint"
        )
        response = checkpoint.prompt_decision()
        assert response.decision == HITLDecision.DENY
        assert response.denial_reason == "Not ready"

    @patch('builtins.input', side_effect=['M', 'Fix this', ''])
    def test_prompt_decision_amend(self, mock_input):
        """Test amending a checkpoint via CLI."""
        checkpoint = HITLCheckpoint(
            name="test",
            description="Test checkpoint"
        )
        response = checkpoint.prompt_decision()
        assert response.decision == HITLDecision.AMEND
        assert response.feedback == "Fix this"

    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_prompt_decision_interrupt(self, mock_input):
        """Test handling Ctrl+C interrupt."""
        checkpoint = HITLCheckpoint(
            name="test",
            description="Test checkpoint"
        )
        response = checkpoint.prompt_decision()
        assert response.decision == HITLDecision.DENY
        assert "Interrupted" in response.denial_reason


class TestHITLManager:
    """Tests for HITLManager class."""

    def setup_method(self):
        """Reset global manager before each test."""
        reset_manager()

    def test_manager_history_persistence(self, temp_project_dir):
        """Test that checkpoint history is persisted."""
        history_file = temp_project_dir / "hitl_history.json"
        manager = HITLManager(history_file=history_file)

        with patch.object(HITLCheckpoint, 'prompt_decision') as mock:
            mock.return_value = HITLResponse(decision=HITLDecision.APPROVE)
            manager.checkpoint(
                name="test_checkpoint",
                description="Test"
            )

        # Check history was saved
        assert history_file.exists()
        data = json.loads(history_file.read_text())
        assert len(data) == 1
        assert data[0]["name"] == "test_checkpoint"

    def test_manager_load_existing_history(self, temp_project_dir):
        """Test loading existing checkpoint history."""
        history_file = temp_project_dir / "hitl_history.json"
        history_file.write_text(json.dumps([
            {"name": "old_checkpoint", "description": "Old"}
        ]))

        manager = HITLManager(history_file=history_file)
        assert len(manager.get_history()) == 1
        assert manager.get_history()[0]["name"] == "old_checkpoint"

    def test_was_checkpoint_approved(self, temp_project_dir):
        """Test checking if a checkpoint was previously approved."""
        history_file = temp_project_dir / "hitl_history.json"
        manager = HITLManager(history_file=history_file)

        with patch.object(HITLCheckpoint, 'prompt_decision') as mock:
            mock.return_value = HITLResponse(decision=HITLDecision.APPROVE)
            manager.checkpoint("approved_cp", "Test")

            mock.return_value = HITLResponse(decision=HITLDecision.DENY)
            manager.checkpoint("denied_cp", "Test")

        assert manager.was_checkpoint_approved("approved_cp") is True
        assert manager.was_checkpoint_approved("denied_cp") is False
        assert manager.was_checkpoint_approved("nonexistent") is None

    def test_clear_history(self, temp_project_dir):
        """Test clearing checkpoint history."""
        history_file = temp_project_dir / "hitl_history.json"
        history_file.write_text(json.dumps([
            {"name": "test", "description": "Test"}
        ]))

        manager = HITLManager(history_file=history_file)
        assert len(manager.get_history()) == 1

        manager.clear_history()
        assert len(manager.get_history()) == 0
        assert json.loads(history_file.read_text()) == []
