"""
Terraform Validation

Utilities for running and validating Terraform operations.
"""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TerraformResult:
    """Result of a Terraform operation."""
    success: bool
    command: str
    stdout: str
    stderr: str
    return_code: int
    outputs: dict = field(default_factory=dict)

    @property
    def error_message(self) -> Optional[str]:
        """Get error message if operation failed."""
        if self.success:
            return None
        return self.stderr or f"Command failed with return code {self.return_code}"


class TerraformValidator:
    """
    Validates Terraform deployments.

    Provides methods for init, plan, apply, and output operations
    with result validation.
    """

    def __init__(
        self,
        working_dir: str | Path,
        auto_approve: bool = False,
        var_file: str = None
    ):
        self.working_dir = Path(working_dir)
        self.auto_approve = auto_approve
        self.var_file = var_file
        self._initialized = False

    def _run_command(self, args: list[str], timeout: int = 600) -> TerraformResult:
        """Run a terraform command and capture output."""
        cmd = ["terraform"] + args

        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return TerraformResult(
                success=result.returncode == 0,
                command=" ".join(cmd),
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            return TerraformResult(
                success=False,
                command=" ".join(cmd),
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                return_code=-1
            )
        except Exception as e:
            return TerraformResult(
                success=False,
                command=" ".join(cmd),
                stdout="",
                stderr=str(e),
                return_code=-1
            )

    def init(self, upgrade: bool = False) -> TerraformResult:
        """
        Initialize Terraform working directory.

        Args:
            upgrade: If True, upgrade modules and providers
        """
        args = ["init"]
        if upgrade:
            args.append("-upgrade")

        result = self._run_command(args)
        if result.success:
            self._initialized = True

        return result

    def validate(self) -> TerraformResult:
        """Validate Terraform configuration."""
        return self._run_command(["validate"])

    def plan(
        self,
        target: str = None,
        out: str = None,
        detailed_exitcode: bool = True
    ) -> TerraformResult:
        """
        Run terraform plan.

        Args:
            target: Optional target module/resource
            out: Optional output file for plan
            detailed_exitcode: If True, use detailed exit codes (0=no changes, 1=error, 2=changes)
        """
        args = ["plan"]

        if target:
            args.extend(["-target", target])

        if out:
            args.extend(["-out", out])

        if detailed_exitcode:
            args.append("-detailed-exitcode")

        if self.var_file:
            args.extend(["-var-file", self.var_file])

        result = self._run_command(args)

        # With detailed-exitcode: 0=no changes, 1=error, 2=changes pending
        if detailed_exitcode:
            if result.return_code == 0:
                result.success = True
            elif result.return_code == 2:
                result.success = True  # Changes pending is still success
            else:
                result.success = False

        return result

    def apply(
        self,
        auto_approve: bool = None,
        target: str = None,
        plan_file: str = None
    ) -> TerraformResult:
        """
        Run terraform apply.

        Args:
            auto_approve: Override instance auto_approve setting
            target: Optional target module/resource
            plan_file: Optional plan file to apply
        """
        args = ["apply"]

        should_auto_approve = auto_approve if auto_approve is not None else self.auto_approve
        if should_auto_approve:
            args.append("-auto-approve")

        if target:
            args.extend(["-target", target])

        if plan_file:
            args.append(plan_file)

        if self.var_file and not plan_file:
            args.extend(["-var-file", self.var_file])

        return self._run_command(args, timeout=1800)  # 30 min timeout for apply

    def destroy(
        self,
        auto_approve: bool = None,
        target: str = None
    ) -> TerraformResult:
        """
        Run terraform destroy.

        Args:
            auto_approve: Override instance auto_approve setting
            target: Optional target module/resource
        """
        args = ["destroy"]

        should_auto_approve = auto_approve if auto_approve is not None else self.auto_approve
        if should_auto_approve:
            args.append("-auto-approve")

        if target:
            args.extend(["-target", target])

        if self.var_file:
            args.extend(["-var-file", self.var_file])

        return self._run_command(args, timeout=1800)

    def output(self, name: str = None, json_format: bool = True) -> TerraformResult:
        """
        Get terraform outputs.

        Args:
            name: Optional specific output name
            json_format: If True, output as JSON
        """
        args = ["output"]

        if json_format:
            args.append("-json")

        if name:
            args.append(name)

        result = self._run_command(args)

        if result.success and json_format:
            try:
                result.outputs = json.loads(result.stdout)
            except json.JSONDecodeError:
                result.outputs = {}

        return result

    def get_output_value(self, name: str) -> Optional[str]:
        """Get a specific output value."""
        result = self.output(name)
        if result.success and result.outputs:
            if isinstance(result.outputs, dict) and "value" in result.outputs:
                return result.outputs["value"]
            return str(result.outputs)
        return None

    def state_list(self) -> TerraformResult:
        """List resources in terraform state."""
        return self._run_command(["state", "list"])

    def format_check(self) -> TerraformResult:
        """Check if Terraform files are formatted."""
        return self._run_command(["fmt", "-check", "-recursive"])


class TerraformTestRunner:
    """
    Runs infrastructure tests using Terraform.

    Validates that modules can be planned/applied and resources
    are created with correct configuration.
    """

    def __init__(self, environments_dir: Path):
        self.environments_dir = environments_dir

    def test_module(
        self,
        module_name: str,
        environment: str = "dev",
        validate_only: bool = False
    ) -> TerraformResult:
        """
        Test a specific Terraform module.

        Args:
            module_name: Name of the module to test
            environment: Environment to test in
            validate_only: If True, only run plan (no apply)
        """
        env_dir = self.environments_dir / environment

        tf = TerraformValidator(
            working_dir=env_dir,
            auto_approve=True
        )

        # Init
        result = tf.init()
        if not result.success:
            return result

        # Plan with target
        result = tf.plan(target=f"module.{module_name}")
        if not result.success or validate_only:
            return result

        # Apply with target
        return tf.apply(target=f"module.{module_name}")

    def validate_all_modules(self, environment: str = "dev") -> dict[str, TerraformResult]:
        """Validate all modules can be planned."""
        env_dir = self.environments_dir / environment

        tf = TerraformValidator(working_dir=env_dir)

        # Init first
        init_result = tf.init()
        if not init_result.success:
            return {"init": init_result}

        # Validate syntax
        validate_result = tf.validate()
        if not validate_result.success:
            return {"validate": validate_result}

        # Plan entire configuration
        plan_result = tf.plan()

        return {
            "init": init_result,
            "validate": validate_result,
            "plan": plan_result
        }
