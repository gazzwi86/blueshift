"""
AWS Resource Verification

Utilities for verifying AWS resources exist and are configured correctly.
"""

import json
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class ResourceCheckResult:
    """Result of checking an AWS resource."""
    resource_type: str
    resource_id: str
    exists: bool
    configuration_valid: bool
    details: dict
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.exists and self.configuration_valid


class AWSResourceChecker:
    """
    Verifies AWS resources exist and are configured correctly.

    Uses AWS CLI for verification to avoid additional SDK dependencies.
    """

    def __init__(self, region: str = None, profile: str = None):
        self.region = region
        self.profile = profile

    def _run_aws_cli(self, service: str, command: str, *args) -> tuple[bool, dict]:
        """
        Run an AWS CLI command and parse JSON output.

        Returns:
            Tuple of (success, parsed_output or error_dict)
        """
        cmd = ["aws", service, command]
        cmd.extend(args)

        if self.region:
            cmd.extend(["--region", self.region])

        if self.profile:
            cmd.extend(["--profile", self.profile])

        cmd.append("--output")
        cmd.append("json")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                try:
                    return True, json.loads(result.stdout) if result.stdout else {}
                except json.JSONDecodeError:
                    return True, {"raw_output": result.stdout}
            else:
                return False, {"error": result.stderr}

        except subprocess.TimeoutExpired:
            return False, {"error": "Command timed out"}
        except Exception as e:
            return False, {"error": str(e)}

    def verify_s3_bucket(
        self,
        bucket_name: str,
        encryption: str = None,
        versioning: bool = None
    ) -> ResourceCheckResult:
        """
        Verify an S3 bucket exists with expected configuration.

        Args:
            bucket_name: Name of the bucket
            encryption: Expected encryption type (e.g., "aws:kms", "AES256")
            versioning: Expected versioning status
        """
        # Check bucket exists
        success, output = self._run_aws_cli(
            "s3api", "head-bucket", "--bucket", bucket_name
        )

        if not success:
            return ResourceCheckResult(
                resource_type="s3_bucket",
                resource_id=bucket_name,
                exists=False,
                configuration_valid=False,
                details={},
                error=output.get("error", "Bucket not found")
            )

        details = {"bucket_name": bucket_name}
        config_valid = True

        # Check encryption if specified
        if encryption:
            enc_success, enc_output = self._run_aws_cli(
                "s3api", "get-bucket-encryption", "--bucket", bucket_name
            )

            if enc_success:
                rules = enc_output.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
                if rules:
                    actual_encryption = rules[0].get("ApplyServerSideEncryptionByDefault", {}).get("SSEAlgorithm")
                    details["encryption"] = actual_encryption
                    if encryption.lower() not in actual_encryption.lower():
                        config_valid = False
            else:
                details["encryption"] = "none"
                config_valid = False

        # Check versioning if specified
        if versioning is not None:
            ver_success, ver_output = self._run_aws_cli(
                "s3api", "get-bucket-versioning", "--bucket", bucket_name
            )

            if ver_success:
                actual_versioning = ver_output.get("Status") == "Enabled"
                details["versioning"] = actual_versioning
                if versioning != actual_versioning:
                    config_valid = False

        return ResourceCheckResult(
            resource_type="s3_bucket",
            resource_id=bucket_name,
            exists=True,
            configuration_valid=config_valid,
            details=details
        )

    def verify_secret(
        self,
        secret_name: str,
        required_keys: list[str] = None
    ) -> ResourceCheckResult:
        """
        Verify a Secrets Manager secret exists.

        Args:
            secret_name: Name or ARN of the secret
            required_keys: Keys that should exist in the secret value
        """
        success, output = self._run_aws_cli(
            "secretsmanager", "describe-secret", "--secret-id", secret_name
        )

        if not success:
            return ResourceCheckResult(
                resource_type="secrets_manager",
                resource_id=secret_name,
                exists=False,
                configuration_valid=False,
                details={},
                error=output.get("error", "Secret not found")
            )

        details = {
            "name": output.get("Name"),
            "arn": output.get("ARN"),
            "created_date": str(output.get("CreatedDate", "")),
        }

        config_valid = True

        # Check required keys if specified
        if required_keys:
            val_success, val_output = self._run_aws_cli(
                "secretsmanager", "get-secret-value", "--secret-id", secret_name
            )

            if val_success:
                try:
                    secret_value = json.loads(val_output.get("SecretString", "{}"))
                    actual_keys = set(secret_value.keys())
                    required_set = set(required_keys)
                    missing = required_set - actual_keys
                    details["has_required_keys"] = len(missing) == 0
                    if missing:
                        details["missing_keys"] = list(missing)
                        config_valid = False
                except json.JSONDecodeError:
                    details["secret_format"] = "not_json"

        return ResourceCheckResult(
            resource_type="secrets_manager",
            resource_id=secret_name,
            exists=True,
            configuration_valid=config_valid,
            details=details
        )

    def verify_kms_key(self, key_id: str) -> ResourceCheckResult:
        """Verify a KMS key exists and is enabled."""
        success, output = self._run_aws_cli(
            "kms", "describe-key", "--key-id", key_id
        )

        if not success:
            return ResourceCheckResult(
                resource_type="kms_key",
                resource_id=key_id,
                exists=False,
                configuration_valid=False,
                details={},
                error=output.get("error", "Key not found")
            )

        key_metadata = output.get("KeyMetadata", {})
        details = {
            "key_id": key_metadata.get("KeyId"),
            "arn": key_metadata.get("Arn"),
            "state": key_metadata.get("KeyState"),
            "enabled": key_metadata.get("Enabled", False)
        }

        config_valid = key_metadata.get("Enabled", False) and key_metadata.get("KeyState") == "Enabled"

        return ResourceCheckResult(
            resource_type="kms_key",
            resource_id=key_id,
            exists=True,
            configuration_valid=config_valid,
            details=details
        )

    def verify_bedrock_kb(self, kb_id: str) -> ResourceCheckResult:
        """Verify a Bedrock Knowledge Base exists."""
        success, output = self._run_aws_cli(
            "bedrock-agent", "get-knowledge-base", "--knowledge-base-id", kb_id
        )

        if not success:
            return ResourceCheckResult(
                resource_type="bedrock_knowledge_base",
                resource_id=kb_id,
                exists=False,
                configuration_valid=False,
                details={},
                error=output.get("error", "Knowledge Base not found")
            )

        kb = output.get("knowledgeBase", {})
        details = {
            "name": kb.get("name"),
            "status": kb.get("status"),
            "role_arn": kb.get("roleArn"),
        }

        config_valid = kb.get("status") == "ACTIVE"

        return ResourceCheckResult(
            resource_type="bedrock_knowledge_base",
            resource_id=kb_id,
            exists=True,
            configuration_valid=config_valid,
            details=details
        )

    def verify_iam_role(self, role_name: str) -> ResourceCheckResult:
        """Verify an IAM role exists."""
        success, output = self._run_aws_cli(
            "iam", "get-role", "--role-name", role_name
        )

        if not success:
            return ResourceCheckResult(
                resource_type="iam_role",
                resource_id=role_name,
                exists=False,
                configuration_valid=False,
                details={},
                error=output.get("error", "Role not found")
            )

        role = output.get("Role", {})
        details = {
            "name": role.get("RoleName"),
            "arn": role.get("Arn"),
            "path": role.get("Path"),
        }

        return ResourceCheckResult(
            resource_type="iam_role",
            resource_id=role_name,
            exists=True,
            configuration_valid=True,
            details=details
        )

    def verify_lambda(self, function_name: str) -> ResourceCheckResult:
        """Verify a Lambda function exists."""
        success, output = self._run_aws_cli(
            "lambda", "get-function", "--function-name", function_name
        )

        if not success:
            return ResourceCheckResult(
                resource_type="lambda_function",
                resource_id=function_name,
                exists=False,
                configuration_valid=False,
                details={},
                error=output.get("error", "Function not found")
            )

        config = output.get("Configuration", {})
        details = {
            "name": config.get("FunctionName"),
            "runtime": config.get("Runtime"),
            "state": config.get("State"),
            "memory": config.get("MemorySize"),
            "timeout": config.get("Timeout"),
        }

        config_valid = config.get("State") == "Active"

        return ResourceCheckResult(
            resource_type="lambda_function",
            resource_id=function_name,
            exists=True,
            configuration_valid=config_valid,
            details=details
        )

    def verify_all(self, resources: list[dict]) -> dict[str, ResourceCheckResult]:
        """
        Verify multiple resources.

        Args:
            resources: List of {"type": "s3_bucket", "id": "bucket-name", "config": {...}}

        Returns:
            Dict mapping resource_id to ResourceCheckResult
        """
        results = {}

        for resource in resources:
            res_type = resource.get("type")
            res_id = resource.get("id")
            config = resource.get("config", {})

            if res_type == "s3_bucket":
                results[res_id] = self.verify_s3_bucket(res_id, **config)
            elif res_type == "secret":
                results[res_id] = self.verify_secret(res_id, **config)
            elif res_type == "kms_key":
                results[res_id] = self.verify_kms_key(res_id)
            elif res_type == "bedrock_kb":
                results[res_id] = self.verify_bedrock_kb(res_id)
            elif res_type == "iam_role":
                results[res_id] = self.verify_iam_role(res_id)
            elif res_type == "lambda":
                results[res_id] = self.verify_lambda(res_id)

        return results
