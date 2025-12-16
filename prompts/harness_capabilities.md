# Harness Capabilities

This document describes the tools, credentials, and capabilities available to you in this autonomous agent harness.

---

## Architecture Overview

This harness is designed for building **AI agents with cloud infrastructure**, not web applications.

**Key differences from web app development:**
- Testing via **agent evaluation** (LLM-as-judge) not browser automation
- Infrastructure validated via **Terraform** and AWS CLI
- Progress tracked via **evaluation scores** meeting thresholds
- **Human-in-the-loop (HITL)** checkpoints at critical junctures

---

## Credential Scopes

There are **two credential scopes**:

1. **Harness Credentials** - For running the autonomous agent harness itself
2. **Runtime Credentials** - For the deployed agent when running in production

All credentials are loaded from the `.env` file in the project root.

---

## Required Credentials (Validated at Startup)

The harness validates these at startup and **fails fast** if missing:

### AWS
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` - Direct access keys
- OR `AWS_PROFILE` - Named profile for SSO/assumed roles
- `AWS_REGION` - Default region (ap-southeast-2)

### Snowflake
- `SNOWFLAKE_ACCOUNT` - Account identifier
- `SNOWFLAKE_USER` - Service account username
- `SNOWFLAKE_PASSWORD` - Password
- `SNOWFLAKE_WAREHOUSE` - Compute warehouse
- `SNOWFLAKE_DATABASE` - Database name
- `SNOWFLAKE_SCHEMA` - Schema name

### SharePoint
- `SHAREPOINT_CLIENT_ID` - Azure AD app client ID
- `SHAREPOINT_CLIENT_SECRET` - Client secret
- `SHAREPOINT_TENANT_ID` - Azure AD tenant
- `SHAREPOINT_SITE_URL` - SharePoint site URL

---

## Optional Credentials (Added via HITL)

These are added later when the agent reaches the Slack integration phase:

### Slack (Added via HITL checkpoint)
- `SLACK_BOT_TOKEN` - Bot user OAuth token (xoxb-...)
- `SLACK_APP_TOKEN` - App-level token for Socket Mode (xapp-...)

---

## Library Components (lib/)

The harness provides reusable library components:

### lib/hitl.py - Human-in-the-Loop System
```python
from lib.hitl import checkpoint, require_approval

# Interactive checkpoint - waits for human decision
response = checkpoint(
    name="initializer_complete",
    description="Review generated test fixtures",
    artifacts=["feature_list.json", "fixtures/"],
    review_instructions=["Are test cases comprehensive?"]
)

if response.approved:
    if response.has_feedback:
        apply_amendments(response.feedback)
    continue_execution()
else:
    halt_with_reason(response.denial_reason)
```

**HITL Decision Types:**
- `[A] Approve` - Continue execution immediately
- `[D] Deny` - Halt execution with reason
- `[M] Amend` - Continue with feedback for agent to address

### lib/evaluation/ - Agent Evaluation Framework
```python
from lib.evaluation import EvaluationHarness

harness = EvaluationHarness(use_deepeval=True)
result = harness.evaluate(
    query="Find AWS certified architects",
    response=agent_response,
    expected={
        "intent_types": ["certification", "role"],
        "tools_used": ["search_employees_comprehensive"]
    },
    thresholds={"correctness": 0.7, "helpfulness": 0.7}
)

if result.passed:
    mark_test_as_passing()
```

**Evaluation Metrics:**
- `correctness` - Is the response factually correct?
- `helpfulness` - Is it useful and actionable?
- `tool_selection` - Did the agent use the right tools?
- `safety` - Did it refuse off-topic queries?

### lib/infrastructure/ - Terraform & AWS Validation
```python
from lib.infrastructure import TerraformValidator, AWSResourceChecker

# Terraform operations
tf = TerraformValidator(working_dir="infra/environments/dev")
tf.init()
tf.plan()
tf.apply(auto_approve=True)  # Full autonomy for dev

# AWS resource verification
aws = AWSResourceChecker()
result = aws.verify_s3_bucket("my-bucket", encryption="aws:kms")
if result.passed:
    print("Bucket configured correctly")
```

### lib/credentials/ - Credential Validation
```python
from lib.credentials import CredentialValidator

validator = CredentialValidator()
validator.require_aws()
validator.require_snowflake()
validator.require_sharepoint()
validator.require_slack(required=False)  # Optional

result = validator.validate()
if not result.valid:
    result.print_status()
    exit(1)
```

---

## MCP Servers Available

You have access to these MCP servers via the `mcp__<server>__<tool>` convention:

### Browser Automation (Limited use for AI agents)
- **puppeteer** - Only for visual testing if needed
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

## Testing Approach

### Agent Evaluation Tests
```bash
# Run all evaluation tests
pytest tests/test_intent.py tests/test_responses.py -v

# Run with DeepEval metrics
pytest tests/test_responses.py --deepeval -v

# Check specific category
pytest tests/ -k "guardrails" -v
```

### Infrastructure Tests
```bash
# Validate Terraform can plan
cd infra/environments/dev && terraform plan

# Apply with auto-approve (dev only)
terraform apply -auto-approve

# Verify resources
pytest tests/test_infrastructure.py -v
```

### Mock Services
```bash
# Start mock server for local testing
python -m mocks.server &

# Run tests with mocks
MOCK_SERVICES=true pytest tests/ -v
```

---

## HITL Checkpoints

The agent will pause at these points:

### After Initializer
- Review generated feature_list.json
- Review synthetic test fixtures
- Approve project structure

### Before Slack Integration
- Configure Slack App in web console
- Add tokens to .env
- Approve to continue

### Before Production (if applicable)
- Review all passing tests
- Approve production deployment

---

## Environment Autonomy

### Development Environment
- **Full autonomy** - terraform apply -auto-approve
- All dev resources can be created/destroyed
- No HITL required for infrastructure changes

### Production Environment
- **Not in scope** - Agent halts at dev-complete
- Production requires manual deployment

---

## Feature List Format

Tests are defined in `feature_list.json` with evaluation thresholds:

```json
{
  "category": "response_quality",
  "test_type": "agent_evaluation",
  "query": "Find Python developers with healthcare experience",
  "expected": {
    "response_format": "slack_markdown",
    "contains_elements": ["employee names", "skills"],
    "tools_used": ["search_employees_comprehensive"]
  },
  "evaluation_thresholds": {
    "helpfulness": 0.7,
    "correctness": 0.7
  },
  "passes": false
}
```

**Categories:**
1. `credential_validation` - Startup checks
2. `infrastructure` - Terraform/AWS resources
3. `intent_classification` - Query understanding
4. `tool_selection` - Correct tool usage
5. `response_quality` - Response content/format
6. `guardrails` - Safety/refusal behavior
7. `error_handling` - Graceful degradation
8. `integration` - End-to-end flows

---

## What You Are Expected To Do

As an autonomous agent:

1. **Validate credentials at startup** - Fail fast if missing
2. **Generate comprehensive test fixtures** - Synthetic but realistic data
3. **Create Terraform infrastructure** - Modules in `infra/`
4. **Implement agent code** - In `src/` following the spec
5. **Evaluate with scoring thresholds** - Not just pass/fail
6. **Handle HITL checkpoints** - Pause and wait for approval
7. **Track progress** - Update claude-progress.txt and feature_list.json

---

## Security Notes

- All bash commands validated against an allowlist
- Destructive AWS IAM/account operations blocked
- Docker `--privileged` mode blocked
- Terraform destroy allowed (for dev cleanup)
- File operations sandboxed to project directory
- Credentials never logged or committed
