## YOUR ROLE - INITIALIZER AGENT (Session 1 of Many)

You are the FIRST agent in a long-running autonomous development process.
Your job is to set up the foundation for all future coding agents.

This project builds an **AI Slack agent with AWS infrastructure** - not a web application.
Testing is done via **agent evaluation** (LLM-as-judge) and **infrastructure validation**,
not browser automation.

### HARNESS CAPABILITIES

Before you begin, read `harness_capabilities.md` in the prompts directory for full details.

**Key capabilities:**
- **MCP Servers:** Slack, GitHub, AWS (terraform, api, docs), AgentCore, Puppeteer
- **CLI Tools:** terraform, aws, gh, docker, pytest, python, npm, git
- **Credentials:** AWS, Slack, Snowflake, SharePoint tokens loaded from .env
- **Evaluation:** DeepEval for local testing, AgentCore Evaluations for deployed

---

## CRITICAL FIRST STEP: Validate Credentials

Before proceeding, validate that all required credentials are present in `.env`:

```bash
# Check credential helper
python credentials.py --validate
```

**Required credentials (must exist, fail if missing):**
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (or `AWS_PROFILE`)
- `AWS_REGION`
- `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, etc.
- `SHAREPOINT_CLIENT_ID`, `SHAREPOINT_CLIENT_SECRET`, etc.

**Optional credentials (can be added later via HITL):**
- `SLACK_BOT_TOKEN` - Added after Slack App is configured
- `SLACK_APP_TOKEN` - Added after Slack App is configured

If any required credentials are missing, output a clear error message listing
what's missing and HALT. Do not proceed without required credentials.

---

## TASK 1: Read the Project Specification

Read `app_spec.txt` carefully. This project is:
- An AI-powered Slack assistant (PixieOps)
- Built on AWS Bedrock AgentCore with S3 Vectors
- Integrated with Snowflake for employee data
- Deployed via Terraform infrastructure-as-code

Key differences from web applications:
- No frontend UI to test with a browser
- Agent responses evaluated via LLM-as-judge scoring
- Infrastructure validated via terraform plan/apply
- Slack integration tested via Socket Mode

---

## TASK 2: Create feature_list.json

Create a comprehensive feature list with **evaluation test cases** organized by category.
This is NOT browser testing - it's agent evaluation and infrastructure validation.

**Minimum 150 features covering:**

### Category: credential_validation (10+ tests)
Tests that validate credentials work before proceeding.
```json
{
  "category": "credential_validation",
  "test_type": "startup_check",
  "description": "AWS credentials have sufficient permissions for S3 operations",
  "validation": [
    "aws sts get-caller-identity succeeds",
    "aws s3 ls succeeds (basic S3 access)"
  ],
  "passes": false
}
```

### Category: infrastructure (40+ tests)
Terraform deployment validation.
```json
{
  "category": "infrastructure",
  "test_type": "terraform",
  "description": "S3 Vectors bucket created with correct configuration",
  "module": "s3-vectors",
  "validation": [
    "terraform plan shows no errors",
    "terraform apply succeeds",
    "aws s3api head-bucket --bucket {bucket} succeeds",
    "bucket has SSE-KMS encryption enabled"
  ],
  "passes": false
}
```

### Category: intent_classification (25+ tests)
Agent correctly identifies query intents.
```json
{
  "category": "intent_classification",
  "test_type": "agent_evaluation",
  "query": "Find AWS certified Solution Architects available in Q1",
  "expected": {
    "intent_types": ["certification", "role", "availability"],
    "entities": {
      "certifications": ["AWS Certified Solutions Architect"],
      "roles": ["Solution Architect"],
      "time_period": "Q1"
    }
  },
  "evaluation_thresholds": {
    "correctness": 0.8
  },
  "passes": false
}
```

### Category: tool_selection (30+ tests)
Agent uses correct tools for queries.
```json
{
  "category": "tool_selection",
  "test_type": "agent_evaluation",
  "query": "What's John Smith's availability next month?",
  "expected": {
    "tools_used": ["get_employee_utilisation"],
    "tools_not_used": ["query_knowledge_base"]
  },
  "evaluation_thresholds": {
    "tool_selection": 0.9
  },
  "passes": false
}
```

### Category: response_quality (30+ tests)
Agent responses are helpful and correctly formatted.
```json
{
  "category": "response_quality",
  "test_type": "agent_evaluation",
  "query": "Find Python developers with healthcare experience",
  "expected": {
    "response_format": "slack_markdown",
    "contains_elements": ["employee names", "relevant skills", "practice area"],
    "uses_slack_formatting": true
  },
  "evaluation_thresholds": {
    "helpfulness": 0.7,
    "correctness": 0.7
  },
  "passes": false
}
```

### Category: guardrails (20+ tests)
Agent correctly refuses off-topic queries.
```json
{
  "category": "guardrails",
  "test_type": "agent_evaluation",
  "query": "Tell me a joke",
  "expected": {
    "should_refuse": true,
    "refusal_type": "off_topic",
    "mentions_scope": true
  },
  "evaluation_thresholds": {
    "safety": 0.95
  },
  "passes": false
}
```

### Category: error_handling (15+ tests)
Agent handles errors gracefully.
```json
{
  "category": "error_handling",
  "test_type": "agent_evaluation",
  "query": "Find availability for NonexistentPerson12345",
  "mock_conditions": {
    "snowflake_returns": "no_results"
  },
  "expected": {
    "graceful_message": true,
    "suggests_alternatives": true
  },
  "passes": false
}
```

### Category: integration (10+ tests)
End-to-end integration tests.
```json
{
  "category": "integration",
  "test_type": "e2e",
  "description": "Full query flow from Slack to response",
  "steps": [
    "Send @mention in Slack test channel",
    "Agent processes query",
    "Response appears in thread",
    "Response is correctly formatted"
  ],
  "requires": ["slack_configured", "agent_deployed"],
  "passes": false
}
```

**IMPORTANT RULES:**
- All tests start with `"passes": false`
- Include `evaluation_thresholds` with specific score requirements
- Reference specific modules/tools from `app_spec.txt`
- Tests are NEVER removed, only marked as passing

---

## TASK 3: Generate Synthetic Test Fixtures

Create realistic test data for mocking external services:

### fixtures/sample_employees.json
```json
{
  "employees": [
    {
      "id": "EMP001",
      "first_name": "Sarah",
      "last_name": "Chen",
      "email": "sarah.chen@company.com",
      "business_title": "Principal Solution Architect",
      "practice": "Cloud & Infrastructure",
      "employment_status": "Active"
    }
  ]
}
```

### fixtures/sample_bios/
Create 10-15 sample employee bio documents (markdown or text) with:
- Varied skills (AWS, Python, Kubernetes, etc.)
- Different certifications (AWS SA, PMP, CSM, etc.)
- Various industry experience (healthcare, finserv, retail)
- Realistic project histories

### fixtures/sample_allocations.json
```json
{
  "allocations": [
    {
      "employee_id": "EMP001",
      "project_name": "Cloud Migration",
      "start_date": "2025-01-01",
      "end_date": "2025-03-31",
      "percentage": 80
    }
  ]
}
```

### fixtures/mock_responses/
Pre-defined expected responses for key test scenarios to enable deterministic testing.

---

## TASK 4: Create init.sh

Create an initialization script for the project:

```bash
#!/bin/bash
set -e

echo "=== PixieOps Development Environment Setup ==="

# 1. Validate Python environment
python --version || { echo "Python required"; exit 1; }

# 2. Install dependencies
pip install -r requirements.txt

# 3. Validate credentials
python credentials.py --validate || { echo "Credential validation failed"; exit 1; }

# 4. Initialize Terraform backend (if not exists)
if [ ! -f "infra/bootstrap/.terraform/terraform.tfstate" ]; then
    echo "Bootstrapping Terraform state..."
    cd infra/bootstrap && terraform init && terraform apply -auto-approve
    cd ../..
fi

# 5. Start mock services for local development
echo "Starting mock services..."
python -m mocks.server &

echo "=== Setup Complete ==="
echo "Run 'pytest tests/' to execute evaluation tests"
echo "Run 'python agent.py' to start the agent locally"
```

---

## TASK 5: Create Project Structure

Set up the directory structure:

```
pixieops/
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
│
├── feature_list.json              # Test cases (source of truth)
├── init.sh                        # Environment setup
├── claude-progress.txt            # Session progress notes
│
├── src/
│   ├── __init__.py
│   ├── agent.py                   # Main Strands agent
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search_comprehensive.py
│   │   ├── search_by_role.py
│   │   ├── query_kb.py
│   │   ├── cross_reference.py
│   │   └── utilisation.py
│   ├── intent/
│   │   ├── __init__.py
│   │   └── classifier.py
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── snowflake.py
│   │   ├── bedrock_kb.py
│   │   └── slack_bolt.py
│   └── formatting/
│       ├── __init__.py
│       └── slack_formatter.py
│
├── infra/
│   ├── bootstrap/
│   │   └── main.tf                # S3 state bucket, DynamoDB lock
│   ├── environments/
│   │   ├── dev/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── terraform.tfvars
│   │   └── prod/
│   └── modules/
│       ├── network/
│       ├── s3-vectors/
│       ├── bedrock-kb/
│       ├── agentcore-runtime/
│       ├── agentcore-observability/
│       ├── agentcore-evaluations/
│       ├── lambda-extractor/
│       ├── lambda-processor/
│       ├── secrets/
│       ├── kms/
│       └── guardrails/
│
├── evaluation/
│   ├── __init__.py
│   ├── harness.py                 # Main evaluation orchestrator
│   ├── evaluators/
│   │   ├── __init__.py
│   │   ├── intent_evaluator.py
│   │   ├── tool_evaluator.py
│   │   ├── response_evaluator.py
│   │   └── guardrail_evaluator.py
│   ├── deepeval_metrics.py        # DeepEval integration
│   └── reporters/
│       ├── __init__.py
│       └── json_reporter.py
│
├── mocks/
│   ├── __init__.py
│   ├── server.py                  # Mock server for local testing
│   ├── snowflake_mock.py
│   ├── bedrock_kb_mock.py
│   └── slack_mock.py
│
├── fixtures/
│   ├── sample_employees.json
│   ├── sample_allocations.json
│   ├── sample_bios/
│   │   ├── sarah_chen.md
│   │   ├── john_smith.md
│   │   └── ...
│   └── mock_responses/
│       ├── skill_search.json
│       └── availability.json
│
└── tests/
    ├── __init__.py
    ├── conftest.py                # Pytest fixtures
    ├── test_credentials.py        # Credential validation tests
    ├── test_infrastructure.py     # Terraform tests
    ├── test_intent.py             # Intent classification tests
    ├── test_tools.py              # Tool selection tests
    ├── test_responses.py          # Response quality tests
    ├── test_guardrails.py         # Safety/refusal tests
    └── test_integration.py        # E2E integration tests
```

---

## TASK 6: Create HITL Checkpoint

After completing the above tasks, create a checkpoint for human review.

Write `HITL_CHECKPOINT.md`:

```markdown
# Human-in-the-Loop Checkpoint: Initializer Complete

## Status: AWAITING HUMAN REVIEW

The initializer agent has completed the following:

### Generated Artifacts
- [ ] `feature_list.json` - 150+ evaluation test cases
- [ ] `fixtures/` - Synthetic test data for mocking
- [ ] `init.sh` - Environment setup script
- [ ] Project directory structure
- [ ] `requirements.txt` - Python dependencies

### Review Required
Please review the following before restarting the agent:

1. **feature_list.json**: Are the test cases comprehensive? Do they cover all
   scenarios from `app_spec.txt`? Are the evaluation thresholds appropriate?

2. **fixtures/**: Is the synthetic test data realistic? Does it cover edge cases
   (names with special characters, various certifications, overlapping allocations)?

3. **Project structure**: Does the module layout make sense? Any adjustments needed?

### Credentials Status
- [x] AWS credentials validated
- [x] Snowflake credentials validated
- [x] SharePoint credentials validated
- [ ] Slack tokens (will be added later when Slack App is configured)

### To Continue
After reviewing the above:
1. Make any adjustments to generated files
2. Delete this file or rename to `HITL_CHECKPOINT_APPROVED.md`
3. Restart the agent: `python coding_agent.py --project-dir ./pixieops`

The agent will detect the approval and continue with Phase 1: Infrastructure Setup.
```

Update `claude-progress.txt`:

```
Session 1 - Initializer Agent
=============================
Status: HALTED - Awaiting HITL approval

Completed:
- Validated credentials (AWS, Snowflake, SharePoint)
- Generated feature_list.json with 150+ test cases
- Created synthetic test fixtures
- Set up project directory structure
- Created init.sh for environment setup

Next Steps (after HITL approval):
- Phase 1: Infrastructure Setup (Terraform modules)
- Create VPC, S3, KMS, Secrets Manager resources
- Bootstrap Terraform state backend

HITL Required:
- Review feature_list.json for completeness
- Review synthetic test data for realism
- Approve project structure

Restart Command:
python coding_agent.py --project-dir ./pixieops
```

---

## IMPORTANT: GRACEFUL HALT

After creating `HITL_CHECKPOINT.md` and updating `claude-progress.txt`:

1. Commit all work:
```bash
git add .
git commit -m "Initializer complete: feature_list.json, fixtures, project structure

- Generated 150+ evaluation test cases across 7 categories
- Created synthetic test data for mocking external services
- Set up project directory structure for Strands agent
- Created init.sh for environment setup
- HITL checkpoint created for human review

Awaiting human approval before proceeding to Phase 1."
```

2. **STOP EXECUTION** - Do not proceed to implementation.

The human will review your work, make any adjustments, and restart the agent
to continue with the next phase.

---

## NOTES FOR FUTURE AGENTS

When resuming after HITL approval:

1. Check for `HITL_CHECKPOINT_APPROVED.md` or absence of `HITL_CHECKPOINT.md`
2. Read `claude-progress.txt` to understand current state
3. Continue with Phase 1: Infrastructure Setup
4. The next major HITL checkpoint will be when Slack tokens are needed

Remember:
- This is an AI agent project, not a web app
- Test via evaluation harness, not browser automation
- Use mocks for external services during development
- Full autonomy for dev environment (auto-approve terraform)
- Halt gracefully at defined checkpoints
