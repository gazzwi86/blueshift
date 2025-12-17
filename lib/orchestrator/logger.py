"""
Session Logger
==============

Logs full agent session output to file for debugging and analysis.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class SessionLogger:
    """
    Logs agent session output to both console and file.

    Creates timestamped log files in the project's logs/ directory.
    """

    def __init__(self, project_dir: Path, session_id: int = 1):
        self.project_dir = project_dir
        self.session_id = session_id
        self.log_dir = project_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"session_{timestamp}_{session_id:03d}.log"
        self.json_file = self.log_dir / f"session_{timestamp}_{session_id:03d}.jsonl"

        # Open files
        self._log_handle = open(self.log_file, "w", encoding="utf-8")
        self._json_handle = open(self.json_file, "w", encoding="utf-8")

        # Write header
        self._write_header()

    def _write_header(self) -> None:
        """Write session header to log."""
        header = f"""
{'=' * 70}
SESSION LOG
{'=' * 70}
Project: {self.project_dir}
Session: {self.session_id}
Started: {datetime.now().isoformat()}
{'=' * 70}

"""
        self._log_handle.write(header)
        self._log_handle.flush()

        # JSON header
        self._write_json({
            "type": "session_start",
            "project_dir": str(self.project_dir),
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
        })

    def _write_json(self, data: dict) -> None:
        """Write a JSON line to the JSONL file."""
        data["_timestamp"] = datetime.now().isoformat()
        self._json_handle.write(json.dumps(data) + "\n")
        self._json_handle.flush()

    def log(self, text: str, end: str = "\n", flush: bool = True) -> None:
        """Log text to both console and file."""
        print(text, end=end, flush=flush)
        self._log_handle.write(text + end)
        if flush:
            self._log_handle.flush()

    def log_prompt(self, prompt: str) -> None:
        """Log the prompt sent to the agent."""
        self._log_handle.write(f"\n{'=' * 70}\nPROMPT\n{'=' * 70}\n")
        self._log_handle.write(prompt)
        self._log_handle.write(f"\n{'=' * 70}\n\n")
        self._log_handle.flush()

        self._write_json({
            "type": "prompt",
            "content": prompt,
        })

    def log_text(self, text: str) -> None:
        """Log assistant text output."""
        print(text, end="", flush=True)
        self._log_handle.write(text)
        self._log_handle.flush()

        self._write_json({
            "type": "text",
            "content": text,
        })

    def log_tool_use(self, name: str, input_data: Any) -> None:
        """Log a tool use."""
        input_str = str(input_data)
        truncated = len(input_str) > 200
        display_input = input_str[:200] + "..." if truncated else input_str

        print(f"\n[Tool: {name}]", flush=True)
        print(f"   Input: {display_input}", flush=True)

        self._log_handle.write(f"\n[Tool: {name}]\n")
        self._log_handle.write(f"   Input: {input_str}\n")  # Full input in log
        self._log_handle.flush()

        self._write_json({
            "type": "tool_use",
            "name": name,
            "input": input_data if isinstance(input_data, (dict, list, str, int, float, bool, type(None))) else str(input_data),
        })

    def log_tool_result(self, content: str, is_error: bool = False, is_blocked: bool = False) -> None:
        """Log a tool result."""
        if is_blocked:
            print(f"   [BLOCKED] {content}", flush=True)
            self._log_handle.write(f"   [BLOCKED] {content}\n")
        elif is_error:
            error_display = str(content)[:500]
            print(f"   [Error] {error_display}", flush=True)
            self._log_handle.write(f"   [Error] {content}\n")  # Full error in log
        else:
            print("   [Done]", flush=True)
            self._log_handle.write(f"   [Done] Result: {content[:1000]}{'...' if len(str(content)) > 1000 else ''}\n")

        self._log_handle.flush()

        self._write_json({
            "type": "tool_result",
            "content": content[:5000] if isinstance(content, str) else str(content)[:5000],
            "is_error": is_error,
            "is_blocked": is_blocked,
        })

    def log_error(self, error: Exception) -> None:
        """Log an error."""
        error_str = str(error)
        print(f"Error during agent session: {error_str}")
        self._log_handle.write(f"\n[ERROR] {error_str}\n")
        self._log_handle.flush()

        self._write_json({
            "type": "error",
            "error": error_str,
            "error_type": type(error).__name__,
        })

    def log_session_end(self, status: str) -> None:
        """Log session end."""
        footer = f"""
{'=' * 70}
SESSION END
{'=' * 70}
Status: {status}
Ended: {datetime.now().isoformat()}
{'=' * 70}
"""
        self._log_handle.write(footer)
        self._log_handle.flush()

        self._write_json({
            "type": "session_end",
            "status": status,
        })

    def close(self) -> None:
        """Close log files."""
        if self._log_handle:
            self._log_handle.close()
        if self._json_handle:
            self._json_handle.close()

    def __enter__(self) -> "SessionLogger":
        return self

    def __exit__(self, *args) -> None:
        self.close()


def get_latest_log(project_dir: Path) -> Optional[Path]:
    """Get the most recent log file for a project."""
    log_dir = project_dir / "logs"
    if not log_dir.exists():
        return None

    logs = sorted(log_dir.glob("session_*.log"), reverse=True)
    return logs[0] if logs else None
