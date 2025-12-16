# Harness Capabilities

This document describes the tools, credentials, and capabilities available to you in this autonomous agent harness.

---

## Credential Scopes

There are **two credential scopes**:

1. **Harness Credentials** - For running the autonomous agent harness itself
2. **Runtime Credentials** - For the PixieOps agent when deployed to AgentCore

All credentials are loaded from the `.env` file in the project root.

---

## Harness Credentials

These are for the harness that orchestrates your work.

### AWS
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` - Direct access keys
- OR `AWS_PROFILE` - Named profile for SSO/assumed roles
- `AWS_REGION` - Default region (ap-southeast-2)
- **Load with:** Environment variables are already set, or use `from credentials import get_credentials`

### Slack
- `SLACK_BOT_TOKEN` - Bot user OAuth token (xoxb-...)
- `SLACK_APP_TOKEN` - App-level token for Socket Mode (xapp-...)
- **Load with:** Already available to Slack MCP server

### GitHub
- `GITHUB_TOKEN` - Personal access token (ghp_...)
- **Load with:** Already available to GitHub MCP server

### Anthropic
- `ANTHROPIC_API_KEY` - Already configured for this agent

---

## External Service Credentials (User Provided)

These connect to services that exist **outside AWS** and must be provided in `.env`.

### Snowflake Data Warehouse
Source of truth for employee roles, practices, allocations, absences.
```
SNOWFLAKE_ACCOUNT=your-account.ap-southeast-2.aws
SNOWFLAKE_USER=pixieops_service
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_WAREHOUSE=PIXIEOPS_WH
SNOWFLAKE_DATABASE=WORKFORCE
SNOWFLAKE_SCHEMA=PUBLIC
```
**Production:** Store in `pixieops/snowflake-credentials` (Secrets Manager)

### SharePoint (Bio Source)
Employee bio documents to be extracted.
```
SHAREPOINT_CLIENT_ID=...
SHAREPOINT_CLIENT_SECRET=...
SHAREPOINT_TENANT_ID=...
SHAREPOINT_SITE_URL=https://yourorg.sharepoint.com/sites/EmployeeBios
```
**Production:** Store in `pixieops/sharepoint-credentials` (Secrets Manager)

---

## Infrastructure Outputs (Created by Terraform)

These are **NOT** user-provided credentials. The agent creates this infrastructure via Terraform and the IDs are outputs.

| Resource | Created By | Output Variable |
|----------|-----------|-----------------|
| Bedrock Knowledge Base | `modules/bedrock-kb` | `bedrock_kb_id` |
| Bedrock Guardrails | `modules/guardrails` | `bedrock_guardrail_id` |
| S3 Vectors Bucket | `modules/s3-vectors` | `s3_vectors_bucket` |
| S3 Raw Docs Bucket | `modules/storage` | `s3_raw_docs_bucket` |
| AgentCore Runtime | `modules/agentcore-runtime` | `agentcore_agent_id` |

### Loading Infrastructure Outputs
```python
from credentials import load_infrastructure_outputs, print_infrastructure_status
from pathlib import Path

# Option 1: From Terraform state
infra = load_infrastructure_outputs(terraform_dir=Path("infra/environments/dev"))

# Option 2: From saved config file (after terraform apply)
infra = load_infrastructure_outputs(config_file=Path("generated_config.json"))

print_infrastructure_status(infra)

# Access values
infra.bedrock_kb_id
infra.s3_vectors_bucket

# Check deployment status
if infra.is_deployed():
    print("Infrastructure ready!")
```

### Saving Infrastructure Outputs
After `terraform apply`, save outputs for later use:
```python
from credentials import save_infrastructure_outputs

save_infrastructure_outputs(infra, Path("generated_config.json"))
```

---

## Model Configuration (Constants)

These are model IDs - not credentials. They're hardcoded in `credentials.py`:
```python
runtime.models.agent_model_id        # Claude Sonnet 4.5
runtime.models.classifier_model_id   # Claude Haiku 3.0
runtime.models.verification_model_id # Claude 3.5 Sonnet
runtime.models.embedding_model_id    # Titan Text V2
```

---

## Loading Credentials
```python
from credentials import (
    get_runtime_credentials,
    load_infrastructure_outputs,
    print_runtime_credential_status,
    print_infrastructure_status,
)
from pathlib import Path

# Load external service credentials from .env
runtime = get_runtime_credentials()
print_runtime_credential_status(runtime)

# Load infrastructure outputs from Terraform
runtime.infra = load_infrastructure_outputs(
    terraform_dir=Path("infra/environments/dev")
)
print_infrastructure_status(runtime.infra)

# Check overall readiness
if runtime.is_production_ready():
    print("All systems go!")
```

---

## MCP Servers Available

You have access to these MCP servers. Use their tools via the `mcp__<server>__<tool>` naming convention.

### Browser Automation
- **puppeteer** - Browser automation for testing
  - Navigate, click, fill, screenshot, evaluate

### Communication
- **slack** - Slack workspace interaction
  - Post messages, read channels, add reactions, search
- **github** - GitHub repository operations
  - Create repos, push files, create PRs, manage issues

### AWS & Infrastructure
- **agentcore** - Amazon Bedrock AgentCore operations
- **aws-terraform** - Terraform operations via AWS
- **aws-api** - Direct AWS API access
- **aws-docs** - Search AWS documentation
- **aws-knowledge** - AWS knowledge base queries
- **terraform-registry** - Terraform registry lookups

### Knowledge
- **context7** - Context7 knowledge base

---

## CLI Commands Allowed

The security allowlist permits these commands:

### Infrastructure
```bash
terraform init|plan|apply|destroy|output|state|...
aws <service> <operation> ...  # Most operations allowed
gh repo|pr|issue|...           # GitHub CLI
```

### Development
```bash
npm install|run|...
node script.js
npx <package>
python|python3 script.py
pytest tests/
pip|pip3 install ...
uv|uvx ...
```

### Docker
```bash
docker build|run|stop|...     # (no --privileged)
docker-compose up|down|...
```

### Utilities
```bash
git status|add|commit|push|...
ls|cat|head|tail|grep|wc|...
cp|mkdir|chmod +x|...
ps|lsof|sleep|pkill <dev-process>
```

---

## Optional Python Helpers

These helpers are available but you can also use MCP tools directly.

### credentials.py
```python
# Harness credentials
from credentials import get_credentials, print_credential_status

creds = get_credentials()
print_credential_status(creds)

creds.aws_access_key_id
creds.slack_bot_token
creds.github_token

# Runtime credentials
from credentials import get_runtime_credentials, print_runtime_credential_status

runtime = get_runtime_credentials()
print_runtime_credential_status(runtime)

runtime.snowflake.account
runtime.bedrock.kb_id
```

### slack_helpers.py
```python
from slack_helpers import send_message, get_channel_history

# Send a message
send_message("#general", "Deployment complete!")

# Get recent messages
messages = get_channel_history("C1234567890", limit=10)
```

---

## What You Are Expected To Do

As an autonomous agent running for up to 24 hours:

1. **Create your own testing framework** - Design tests that fit your project
2. **Create your own Terraform infrastructure** - Build infra in `infra/` as needed
3. **Build your own Slack interaction patterns** - Use MCP or helpers as you prefer
4. **Manage your own deployment verification** - Test deployments end-to-end
5. **Port from ECS to AgentCore** - Using the PixieOps spec as guidance
6. **Configure AWS Secrets Manager** - Store runtime credentials securely

The harness provides capabilities; you decide how to use them.

---

## AWS Secrets Manager Paths (Production)

In production, credentials should be stored in AWS Secrets Manager:

| Secret Path | Contents |
|-------------|----------|
| `pixieops/slack-tokens` | SLACK_BOT_TOKEN, SLACK_APP_TOKEN |
| `pixieops/snowflake-credentials` | account, user, password, warehouse, database, schema |
| `pixieops/sharepoint-credentials` | client_id, client_secret, tenant_id, site_url |

---

## Security Notes

- All bash commands are validated against an allowlist
- Destructive AWS IAM/account operations are blocked
- Docker `--privileged` mode is blocked
- Terraform destroy is allowed (for infrastructure management)
- File operations are sandboxed to the project directory
- In production, use AWS Secrets Manager instead of .env files
