"""
Infrastructure Validation Framework

Provides utilities for validating Terraform deployments and AWS resources.

Usage:
    from lib.infrastructure import TerraformValidator, AWSResourceChecker

    # Terraform validation
    tf = TerraformValidator(working_dir="infra/environments/dev")
    if tf.init().success:
        plan = tf.plan()
        if plan.success:
            apply = tf.apply(auto_approve=True)

    # AWS resource verification
    aws = AWSResourceChecker()
    aws.verify_s3_bucket("my-bucket", encryption="aws:kms")
"""

from .terraform import TerraformValidator, TerraformResult
from .aws import AWSResourceChecker

__all__ = [
    "TerraformValidator",
    "TerraformResult",
    "AWSResourceChecker",
]
