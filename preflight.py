#!/usr/bin/env python3
"""
Preflight Check
===============

Run this before start.py to verify the harness is configured correctly.

Usage:
    python preflight.py           # Run all checks
    python preflight.py --quick   # Skip security tests (faster)
"""

import argparse
import sys
from pathlib import Path


class PreflightChecker:
    """Runs preflight checks and reports results."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def ok(self, msg: str) -> None:
        print(f"  [OK] {msg}")
        self.passed += 1

    def fail(self, msg: str) -> None:
        print(f"  [FAIL] {msg}")
        self.failed += 1

    def warn(self, msg: str) -> None:
        print(f"  [WARN] {msg}")
        self.warnings += 1

    def section(self, title: str) -> None:
        print(f"\n{title}")
        print("-" * 50)

    def check_lib_imports(self) -> None:
        """Check that all lib modules can be imported."""
        self.section("Library Imports")

        modules = [
            ("lib.hitl", ["checkpoint", "HITLDecision"]),
            ("lib.prompts", ["get_initializer_prompt", "get_coding_prompt"]),
            ("lib.progress", ["ProgressTracker", "print_progress_summary"]),
            ("lib.security", ["BaseSecurity"]),
            ("lib.credentials", ["CredentialValidator"]),
            ("lib.evaluation", ["EvaluationHarness"]),
            ("lib.infrastructure", ["TerraformValidator", "AWSResourceChecker"]),
            ("lib.orchestrator", ["run_agent_session"]),
        ]

        for module_name, exports in modules:
            try:
                module = __import__(module_name, fromlist=exports)
                for export in exports:
                    if not hasattr(module, export):
                        self.fail(f"{module_name}.{export} not found")
                        continue
                self.ok(f"{module_name}")
            except ImportError as e:
                self.fail(f"{module_name}: {e}")

    def check_project_imports(self) -> None:
        """Check that project-specific modules can be imported."""
        self.section("Project Imports")

        try:
            from security import bash_security_hook, ProjectSecurity
            self.ok("security (ProjectSecurity, bash_security_hook)")
        except ImportError as e:
            self.fail(f"security: {e}")

        try:
            from credentials import get_credentials, Credentials
            self.ok("credentials (get_credentials, Credentials)")
        except ImportError as e:
            self.fail(f"credentials: {e}")

        try:
            from client import create_client, build_mcp_servers
            self.ok("client (create_client, build_mcp_servers)")
        except ImportError as e:
            # claude_code_sdk may not be installed
            if "claude_code_sdk" in str(e):
                self.warn(f"client: claude_code_sdk not installed (required for runtime)")
            else:
                self.fail(f"client: {e}")

    def check_credentials(self) -> None:
        """Check that credentials are configured."""
        self.section("Credentials")

        try:
            from credentials import get_credentials, validate_credentials, print_credential_status

            creds = get_credentials()

            # Required
            if creds.anthropic_api_key:
                # Show partial key for verification
                key_preview = creds.anthropic_api_key[:12] + "..."
                self.ok(f"ANTHROPIC_API_KEY ({key_preview})")
            else:
                self.fail("ANTHROPIC_API_KEY not set")

            # AWS
            if creds.has_aws_profile():
                self.ok(f"AWS (profile: {creds.aws_profile})")
            elif creds.has_aws_keys():
                self.ok(f"AWS (access keys, region: {creds.aws_region})")
            else:
                self.warn("AWS credentials not configured")

            # Optional
            if creds.has_slack():
                self.ok("Slack credentials")
            else:
                self.warn("Slack credentials not configured")

            if creds.has_github():
                self.ok("GitHub token")
            else:
                self.warn("GitHub token not configured")

            if creds.context7_api_key:
                self.ok("Context7 API key")
            else:
                self.warn("Context7 API key not configured")

        except ValueError as e:
            self.fail(str(e))
        except Exception as e:
            self.fail(f"Credential check failed: {e}")

    def check_prompts(self) -> None:
        """Check that prompt files exist."""
        self.section("Prompt Files")

        prompts_dir = Path(__file__).parent / "prompts"
        required_prompts = [
            "initializer_prompt.md",
            "coding_prompt.md",
            "app_spec.txt",
        ]

        for prompt_file in required_prompts:
            path = prompts_dir / prompt_file
            if path.exists():
                size = path.stat().st_size
                self.ok(f"{prompt_file} ({size} bytes)")
            else:
                self.fail(f"{prompt_file} not found")

    def check_security_tests(self) -> None:
        """Run the security test suite."""
        self.section("Security Tests")

        try:
            from lib.security.test_security import main as run_security_tests

            # Capture the result
            import io
            import contextlib

            # Run tests and capture output
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                result = run_security_tests()

            if result == 0:
                self.ok("All security tests passed")
            else:
                self.fail("Some security tests failed (run: python -m lib.security.test_security)")

        except Exception as e:
            self.fail(f"Security tests failed: {e}")

    def check_env_file(self) -> None:
        """Check that .env file exists."""
        self.section("Environment")

        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            self.ok(f".env file found")
        else:
            self.warn(".env file not found (using environment variables only)")

        # Check Python version
        import platform
        py_version = platform.python_version()
        if py_version.startswith("3.12"):
            self.ok(f"Python {py_version}")
        else:
            self.warn(f"Python {py_version} (3.12.x recommended)")

    def check_claude_sdk(self) -> None:
        """Check Claude Code SDK availability."""
        self.section("Claude Code SDK")

        try:
            import claude_code_sdk
            version = getattr(claude_code_sdk, "__version__", "unknown")
            self.ok(f"claude_code_sdk installed (v{version})")
        except ImportError:
            self.fail("claude_code_sdk not installed (required: pip install claude-code-sdk)")

    def run(self, skip_security_tests: bool = False) -> int:
        """Run all preflight checks."""
        print("=" * 50)
        print("  PREFLIGHT CHECK")
        print("=" * 50)

        self.check_env_file()
        self.check_lib_imports()
        self.check_project_imports()
        self.check_credentials()
        self.check_prompts()
        self.check_claude_sdk()

        if not skip_security_tests:
            self.check_security_tests()
        else:
            print("\n[Skipped] Security Tests (--quick mode)")

        # Summary
        print("\n" + "=" * 50)
        print("  SUMMARY")
        print("=" * 50)
        print(f"\n  Passed:   {self.passed}")
        print(f"  Warnings: {self.warnings}")
        print(f"  Failed:   {self.failed}")

        if self.failed == 0:
            print("\n  PREFLIGHT CHECK PASSED")
            if self.warnings > 0:
                print(f"  ({self.warnings} warnings - review above)")
            print("\n  Ready to run: python start.py --project-dir ./your_project")
            return 0
        else:
            print("\n  PREFLIGHT CHECK FAILED")
            print("  Fix the issues above before running start.py")
            return 1


def main():
    parser = argparse.ArgumentParser(
        description="Run preflight checks before starting the agent harness"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Skip security tests for faster checking"
    )
    args = parser.parse_args()

    checker = PreflightChecker()
    sys.exit(checker.run(skip_security_tests=args.quick))


if __name__ == "__main__":
    main()
