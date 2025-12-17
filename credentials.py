"""
Credential Management
=====================

Load and validate credentials from .env file.
Provides clear error messages for missing credentials.

Two credential scopes:
1. Harness credentials (GENERIC) - for running the autonomous agent harness
2. Runtime credentials (PROJECT-SPECIFIC) - example for PixieOps project

NOTE: The RuntimeCredentials, SnowflakeCredentials, and SharePointCredentials
classes below are PROJECT-SPECIFIC examples. Edit or remove them for your
project's needs. The HarnessCredentials class is generic and reusable.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


@dataclass
class HarnessCredentials:
    """Credentials for running the autonomous agent harness."""
    anthropic_api_key: str = ""
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "ap-southeast-2"
    aws_profile: Optional[str] = None
    slack_bot_token: Optional[str] = None
    slack_app_token: Optional[str] = None
    slack_signing_secret: Optional[str] = None
    github_token: Optional[str] = None
    context7_api_key: Optional[str] = None

    def has_aws_keys(self) -> bool:
        return bool(self.aws_access_key_id and self.aws_secret_access_key)

    def has_aws_profile(self) -> bool:
        return bool(self.aws_profile)

    def has_aws(self) -> bool:
        return self.has_aws_keys() or self.has_aws_profile()

    def has_slack(self) -> bool:
        return bool(self.slack_bot_token and self.slack_app_token)

    def has_github(self) -> bool:
        return bool(self.github_token)


# =============================================================================
# PROJECT-SPECIFIC CREDENTIALS (Example for PixieOps - edit for your project)
# =============================================================================

@dataclass
class SnowflakeCredentials:
    """Snowflake data warehouse credentials. PROJECT-SPECIFIC - edit for your project."""
    account: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    warehouse: Optional[str] = None
    database: Optional[str] = None
    schema: Optional[str] = None

    def is_configured(self) -> bool:
        return all([self.account, self.user, self.password, self.warehouse, self.database])


@dataclass
class SharePointCredentials:
    """SharePoint credentials for bio extraction."""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    site_url: Optional[str] = None

    def is_configured(self) -> bool:
        return all([self.client_id, self.client_secret, self.tenant_id, self.site_url])


@dataclass
class InfrastructureOutputs:
    """
    Infrastructure outputs created by Terraform.

    These are NOT user-provided credentials - they are outputs from
    infrastructure the agent creates. Load from Terraform state or
    a generated config file.
    """
    # Bedrock KB (created by terraform module bedrock-kb)
    bedrock_kb_id: Optional[str] = None
    bedrock_kb_data_source_id: Optional[str] = None

    # Bedrock Guardrails (created by terraform module guardrails)
    bedrock_guardrail_id: Optional[str] = None
    bedrock_guardrail_version: str = "DRAFT"

    # S3 Vectors (created by terraform module s3-vectors)
    s3_vectors_bucket: Optional[str] = None
    s3_vectors_index: str = "bios-index"

    # S3 Raw Docs (created by terraform module storage)
    s3_raw_docs_bucket: Optional[str] = None

    # AgentCore (created by terraform module agentcore-runtime)
    agentcore_agent_id: Optional[str] = None
    agentcore_alias_id: Optional[str] = None

    def is_deployed(self) -> bool:
        """Check if core infrastructure has been deployed."""
        return bool(self.bedrock_kb_id and self.s3_vectors_bucket)


@dataclass
class ModelConfig:
    """Bedrock model IDs - these are constants, not credentials."""
    agent_model_id: str = "anthropic.claude-sonnet-4-5-20250929-v1:0"
    classifier_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    verification_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    embedding_model_id: str = "amazon.titan-embed-text-v2:0"


@dataclass
class RuntimeCredentials:
    """
    Credentials for the PixieOps agent runtime.

    Separates:
    - External service credentials (Snowflake, SharePoint) - must be provided
    - Infrastructure outputs (Bedrock KB, S3) - created by Terraform
    - Model config - constants
    """
    # External services (user must provide)
    snowflake: SnowflakeCredentials = field(default_factory=SnowflakeCredentials)
    sharepoint: SharePointCredentials = field(default_factory=SharePointCredentials)

    # Infrastructure (created by agent via Terraform)
    infra: InfrastructureOutputs = field(default_factory=InfrastructureOutputs)

    # Model IDs (constants)
    models: ModelConfig = field(default_factory=ModelConfig)

    # Environment
    environment: str = "dev"

    def external_services_configured(self) -> bool:
        """Check if external service credentials are provided."""
        return self.snowflake.is_configured() and self.sharepoint.is_configured()

    def is_production_ready(self) -> bool:
        """Check if ready for production (external creds + infra deployed)."""
        return self.external_services_configured() and self.infra.is_deployed()


# Alias for backward compatibility
Credentials = HarnessCredentials


def load_env_file(env_path: Optional[Path] = None) -> None:
    """Load .env file if it exists."""
    if env_path is None:
        env_path = Path(__file__).parent / ".env"

    if env_path.exists():
        if DOTENV_AVAILABLE:
            load_dotenv(env_path)
            print(f"Loaded credentials from {env_path}")
        else:
            # Manual .env parsing as fallback
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip().strip("'\"")
                        if key and value:
                            os.environ[key] = value
            print(f"Loaded credentials from {env_path} (manual parsing)")
    else:
        print(f"No .env file found at {env_path}")
        print("Using environment variables only")


def get_credentials(env_path: Optional[Path] = None) -> HarnessCredentials:
    """
    Load and validate harness credentials.

    Args:
        env_path: Optional path to .env file

    Returns:
        HarnessCredentials object with validated values

    Raises:
        ValueError: If required credentials are missing
    """
    load_env_file(env_path)

    creds = HarnessCredentials()

    # Optional: Anthropic API key (if not set, Claude Code subscription token is used)
    creds.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    # AWS: Either access keys or profile
    creds.aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    creds.aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    creds.aws_region = os.environ.get("AWS_REGION", "ap-southeast-2")
    creds.aws_profile = os.environ.get("AWS_PROFILE")

    # Slack
    creds.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
    creds.slack_app_token = os.environ.get("SLACK_APP_TOKEN")
    creds.slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")

    # GitHub
    creds.github_token = os.environ.get("GITHUB_TOKEN")

    # Context7
    creds.context7_api_key = os.environ.get("CONTEXT7_API_KEY")

    return creds


def get_runtime_credentials(env_path: Optional[Path] = None) -> RuntimeCredentials:
    """
    Load PixieOps agent runtime credentials from .env.

    Only loads external service credentials (Snowflake, SharePoint).
    Infrastructure outputs should be loaded separately from Terraform.

    Args:
        env_path: Optional path to .env file

    Returns:
        RuntimeCredentials object
    """
    load_env_file(env_path)

    runtime = RuntimeCredentials()

    # External service: Snowflake
    runtime.snowflake = SnowflakeCredentials(
        account=os.environ.get("SNOWFLAKE_ACCOUNT"),
        user=os.environ.get("SNOWFLAKE_USER"),
        password=os.environ.get("SNOWFLAKE_PASSWORD"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE"),
        database=os.environ.get("SNOWFLAKE_DATABASE"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA"),
    )

    # External service: SharePoint
    runtime.sharepoint = SharePointCredentials(
        client_id=os.environ.get("SHAREPOINT_CLIENT_ID"),
        client_secret=os.environ.get("SHAREPOINT_CLIENT_SECRET"),
        tenant_id=os.environ.get("SHAREPOINT_TENANT_ID"),
        site_url=os.environ.get("SHAREPOINT_SITE_URL"),
    )

    # Environment
    runtime.environment = os.environ.get("AGENTCORE_ENVIRONMENT", "dev")

    # Infrastructure outputs are NOT loaded from .env
    # They should be loaded from Terraform via load_infrastructure_outputs()

    return runtime


def load_infrastructure_outputs(
    terraform_dir: Optional[Path] = None,
    config_file: Optional[Path] = None,
) -> InfrastructureOutputs:
    """
    Load infrastructure outputs from Terraform state or config file.

    The agent creates infrastructure via Terraform and the outputs
    (KB IDs, bucket names, etc.) are stored in Terraform state.
    This function retrieves them.

    Args:
        terraform_dir: Path to Terraform directory (runs `terraform output -json`)
        config_file: Path to generated config JSON file (alternative to Terraform)

    Returns:
        InfrastructureOutputs object
    """
    import json
    import subprocess

    outputs = InfrastructureOutputs()

    # Option 1: Load from config file (simpler)
    if config_file and config_file.exists():
        with open(config_file) as f:
            config = json.load(f)

        outputs.bedrock_kb_id = config.get("bedrock_kb_id")
        outputs.bedrock_kb_data_source_id = config.get("bedrock_kb_data_source_id")
        outputs.bedrock_guardrail_id = config.get("bedrock_guardrail_id")
        outputs.s3_vectors_bucket = config.get("s3_vectors_bucket")
        outputs.s3_vectors_index = config.get("s3_vectors_index", "bios-index")
        outputs.s3_raw_docs_bucket = config.get("s3_raw_docs_bucket")
        outputs.agentcore_agent_id = config.get("agentcore_agent_id")
        outputs.agentcore_alias_id = config.get("agentcore_alias_id")

        return outputs

    # Option 2: Load from Terraform state
    if terraform_dir and terraform_dir.exists():
        try:
            result = subprocess.run(
                ["terraform", "output", "-json"],
                cwd=terraform_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            tf_outputs = json.loads(result.stdout)

            # Extract values from Terraform output format {"value": ..., "type": ...}
            def get_tf_value(key: str) -> Optional[str]:
                if key in tf_outputs:
                    return tf_outputs[key].get("value")
                return None

            outputs.bedrock_kb_id = get_tf_value("bedrock_kb_id")
            outputs.bedrock_kb_data_source_id = get_tf_value("bedrock_kb_data_source_id")
            outputs.bedrock_guardrail_id = get_tf_value("bedrock_guardrail_id")
            outputs.s3_vectors_bucket = get_tf_value("s3_vectors_bucket")
            outputs.s3_vectors_index = get_tf_value("s3_vectors_index") or "bios-index"
            outputs.s3_raw_docs_bucket = get_tf_value("s3_raw_docs_bucket")
            outputs.agentcore_agent_id = get_tf_value("agentcore_agent_id")
            outputs.agentcore_alias_id = get_tf_value("agentcore_alias_id")

        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            # Terraform not available or no state - infrastructure not yet deployed
            pass

    return outputs


def save_infrastructure_outputs(outputs: InfrastructureOutputs, config_file: Path) -> None:
    """
    Save infrastructure outputs to a config file.

    Use this after Terraform apply to persist outputs for later use.

    Args:
        outputs: InfrastructureOutputs to save
        config_file: Path to save config JSON
    """
    import json

    config = {
        "bedrock_kb_id": outputs.bedrock_kb_id,
        "bedrock_kb_data_source_id": outputs.bedrock_kb_data_source_id,
        "bedrock_guardrail_id": outputs.bedrock_guardrail_id,
        "bedrock_guardrail_version": outputs.bedrock_guardrail_version,
        "s3_vectors_bucket": outputs.s3_vectors_bucket,
        "s3_vectors_index": outputs.s3_vectors_index,
        "s3_raw_docs_bucket": outputs.s3_raw_docs_bucket,
        "agentcore_agent_id": outputs.agentcore_agent_id,
        "agentcore_alias_id": outputs.agentcore_alias_id,
    }

    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Saved infrastructure outputs to {config_file}")


def validate_credentials(creds: HarnessCredentials, require_all: bool = False) -> list[str]:
    """
    Validate harness credentials and return list of warnings.

    Args:
        creds: Credentials object to validate
        require_all: If True, treat missing optional creds as errors

    Returns:
        List of warning/error messages (empty if all OK)
    """
    warnings = []

    if not creds.has_aws():
        msg = "AWS credentials not configured (no access keys or profile)"
        warnings.append(f"{'ERROR' if require_all else 'WARNING'}: {msg}")

    if not creds.has_slack():
        msg = "Slack credentials not configured"
        warnings.append(f"{'ERROR' if require_all else 'WARNING'}: {msg}")

    if not creds.has_github():
        msg = "GitHub token not configured"
        warnings.append(f"{'ERROR' if require_all else 'WARNING'}: {msg}")

    return warnings


def validate_runtime_credentials(runtime: RuntimeCredentials) -> list[str]:
    """
    Validate runtime credentials and return list of warnings.

    Only validates external service credentials (user-provided).
    Infrastructure outputs are validated separately.

    Returns:
        List of warning/error messages
    """
    warnings = []

    if not runtime.snowflake.is_configured():
        warnings.append("WARNING: Snowflake credentials not fully configured")

    if not runtime.sharepoint.is_configured():
        warnings.append("WARNING: SharePoint credentials not configured")

    return warnings


def validate_infrastructure_outputs(infra: InfrastructureOutputs) -> list[str]:
    """
    Validate infrastructure outputs (created by Terraform).

    Returns:
        List of warning/info messages about missing infrastructure
    """
    warnings = []

    if not infra.bedrock_kb_id:
        warnings.append("INFO: Bedrock KB not yet created (run Terraform)")

    if not infra.bedrock_guardrail_id:
        warnings.append("INFO: Bedrock Guardrails not yet created (run Terraform)")

    if not infra.s3_vectors_bucket:
        warnings.append("INFO: S3 Vectors bucket not yet created (run Terraform)")

    if not infra.s3_raw_docs_bucket:
        warnings.append("INFO: S3 Raw Docs bucket not yet created (run Terraform)")

    return warnings


def print_credential_status(creds: HarnessCredentials) -> None:
    """Print status of harness credentials."""
    print("\nHarness Credential Status:")
    print("-" * 50)
    print(f"  Anthropic API Key: {'OK' if creds.anthropic_api_key else 'MISSING'}")

    if creds.has_aws_keys():
        print(f"  AWS (Access Keys): OK (region: {creds.aws_region})")
    elif creds.has_aws_profile():
        print(f"  AWS (Profile): OK (profile: {creds.aws_profile}, region: {creds.aws_region})")
    else:
        print("  AWS: NOT CONFIGURED")

    print(f"  Slack Bot Token:   {'OK' if creds.slack_bot_token else 'NOT SET'}")
    print(f"  Slack App Token:   {'OK' if creds.slack_app_token else 'NOT SET'}")
    print(f"  GitHub Token:      {'OK' if creds.github_token else 'NOT SET'}")
    print(f"  Context7 API Key:  {'OK' if creds.context7_api_key else 'NOT SET'}")
    print("-" * 50)


def print_runtime_credential_status(runtime: RuntimeCredentials) -> None:
    """Print status of runtime credentials (external services only)."""
    print("\nPixieOps External Service Credentials:")
    print("-" * 50)
    print(f"  Environment: {runtime.environment}")
    print(f"  Snowflake:   {'OK' if runtime.snowflake.is_configured() else 'NOT CONFIGURED'}")
    print(f"  SharePoint:  {'OK' if runtime.sharepoint.is_configured() else 'NOT CONFIGURED'}")
    print("-" * 50)
    print(f"  External Services Ready: {'YES' if runtime.external_services_configured() else 'NO'}")
    print("-" * 50)


def print_infrastructure_status(infra: InfrastructureOutputs) -> None:
    """Print status of infrastructure outputs (created by Terraform)."""
    print("\nPixieOps Infrastructure (created by Terraform):")
    print("-" * 50)
    print(f"  Bedrock KB:        {infra.bedrock_kb_id or 'NOT DEPLOYED'}")
    print(f"  Bedrock Guardrails:{infra.bedrock_guardrail_id or 'NOT DEPLOYED'}")
    print(f"  S3 Vectors Bucket: {infra.s3_vectors_bucket or 'NOT DEPLOYED'}")
    print(f"  S3 Raw Docs Bucket:{infra.s3_raw_docs_bucket or 'NOT DEPLOYED'}")
    print(f"  AgentCore Agent:   {infra.agentcore_agent_id or 'NOT DEPLOYED'}")
    print("-" * 50)
    print(f"  Infrastructure Deployed: {'YES' if infra.is_deployed() else 'NO'}")
    print("-" * 50)


def get_env_for_mcp_servers(creds: HarnessCredentials) -> dict[str, str]:
    """
    Get environment variables to pass to MCP servers.

    Returns:
        Dict of environment variables
    """
    env = {}

    # AWS
    if creds.aws_access_key_id:
        env["AWS_ACCESS_KEY_ID"] = creds.aws_access_key_id
    if creds.aws_secret_access_key:
        env["AWS_SECRET_ACCESS_KEY"] = creds.aws_secret_access_key
    if creds.aws_region:
        env["AWS_REGION"] = creds.aws_region
    if creds.aws_profile:
        env["AWS_PROFILE"] = creds.aws_profile

    # Slack
    if creds.slack_bot_token:
        env["SLACK_BOT_TOKEN"] = creds.slack_bot_token
    if creds.slack_app_token:
        env["SLACK_APP_TOKEN"] = creds.slack_app_token

    # GitHub
    if creds.github_token:
        env["GITHUB_TOKEN"] = creds.github_token

    # Context7
    if creds.context7_api_key:
        env["CONTEXT7_API_KEY"] = creds.context7_api_key

    return env


def get_snowflake_connection_params(runtime: RuntimeCredentials) -> dict:
    """
    Get Snowflake connection parameters for snowflake-connector-python.

    Returns:
        Dict of connection parameters
    """
    sf = runtime.snowflake
    return {
        "account": sf.account,
        "user": sf.user,
        "password": sf.password,
        "warehouse": sf.warehouse,
        "database": sf.database,
        "schema": sf.schema,
    }
