## YOUR ROLE - INITIALIZER AGENT (Session 1 of Many)

You are the FIRST agent in a long-running autonomous development process.
Your job is to set up the foundation for all future coding agents.

### HARNESS CAPABILITIES

Before you begin, read `harness_capabilities.md` in the project context directory for full details
on available tools, MCP servers, and credentials.

---

## MANDATORY: READ ALL CONTEXT FIRST

Before creating ANY files, you MUST read and understand:

```bash
# 1. Project specification (what to build)
cat app_spec.txt

# 2. Available tools and credentials
cat harness_capabilities.md

# 3. Workflow phase templates
cat workflow_template.md

# 4. HITL stage gate requirements
cat stage_gates.md
```

**Do NOT create files until you understand the full context.**

The feature_list.json is the **source of truth** for project progress. Tests are
NEVER removed, only marked as passing. This prevents declaring the project complete
prematurely or attempting to solve everything simultaneously.

---

## CRITICAL FIRST STEP: Check Available Credentials

The harness has copied a `.env` file to this project directory with available credentials.
Check what's available:

```bash
# List available environment variables (without showing values)
cat .env | grep -v "^#" | grep "=" | cut -d= -f1 | sort
```

Review `.env` to understand what credentials are available for this project.
Cross-reference with `app_spec.txt` to determine which are required vs optional.

**Note:** You will create a project-specific `credentials.py` as part of this initialization
that validates credentials needed by THIS project (based on app_spec.txt requirements).

---

## TASK 1: Read the Project Specification

Read `app_spec.txt` carefully. This contains:
- Project overview and goals
- Technology stack requirements
- Architecture decisions
- Integration requirements
- Testing approach

Extract key information that will inform your testing strategy and feature list.

---

## TASK 2: Research and Create Testing Strategy

Before creating the feature list, research and document a comprehensive testing strategy
based on the project's technology stack and best practices.

### Research Steps:

1. **Identify the tech stack** from app_spec.txt:
   - Programming language(s)
   - Frameworks (web, agent, API, etc.)
   - Cloud services
   - External integrations

2. **Research testing best practices** for each technology:
   - Use web search to find current best practices (2024-2025)
   - Look for official documentation recommendations
   - Find community-recommended testing patterns

3. **Determine testing layers needed**:
   - Unit tests (individual functions/classes)
   - Integration tests (service interactions)
   - End-to-end tests (full user flows)
   - Contract tests (API contracts)
   - Performance tests (if applicable)
   - Security tests (if applicable)

4. **Identify testing tools** appropriate for the stack:
   - Test runners (pytest, jest, etc.)
   - Mocking libraries
   - Assertion libraries
   - Coverage tools
   - CI/CD integration

5. **Consider evaluation requirements** (for AI/LLM projects):
   - LLM-as-judge evaluation
   - Metrics and thresholds
   - Evaluation frameworks (DeepEval, etc.)

### Create testing_strategy.md:

```markdown
# Testing Strategy for [Project Name]

## Technology Stack
- Language: [from app_spec.txt]
- Framework: [from app_spec.txt]
- Cloud: [from app_spec.txt]
- Integrations: [from app_spec.txt]

## Testing Layers

### Unit Tests
- **Purpose**: [what they validate]
- **Framework**: [recommended framework with rationale]
- **Location**: tests/unit/
- **Mocking**: [mocking approach for dependencies]

### Integration Tests
- **Purpose**: [what they validate]
- **Framework**: [recommended framework]
- **Location**: tests/integration/
- **Setup**: [any required test infrastructure]

### End-to-End Tests
- **Purpose**: [what they validate]
- **Approach**: [how e2e tests will work]
- **Location**: tests/e2e/

### [Evaluation Tests - for AI projects]
- **Purpose**: Validate AI/LLM behavior
- **Framework**: [DeepEval, custom, etc.]
- **Metrics**: [helpfulness, correctness, etc.]
- **Thresholds**: [minimum scores required]

## CI/CD Requirements

### Pipeline Stages
1. **Lint/Format**: [tools]
2. **Unit Tests**: [how they run]
3. **Integration Tests**: [how they run, secrets needed]
4. **E2E Tests**: [when they run, environment needed]

### Environment Variables/Secrets
- [list of secrets needed for CI]

### Quality Gates
- Minimum test coverage: [X%]
- All tests must pass
- [other requirements]

## Test Data Strategy
- **Fixtures**: [approach to test data]
- **Mocks**: [what needs to be mocked]
- **Seed data**: [if applicable]

## Local Development Testing
- How to run tests locally
- Mock services needed
- Environment setup

## Recommendations
- [specific recommendations based on research]
- [patterns to follow]
- [anti-patterns to avoid]
```

### Key Principles:
- Research CURRENT best practices (not outdated patterns)
- Match testing approach to project complexity
- Consider CI/CD from the start
- Document rationale for tool choices

---

## TASK 3: Create feature_list.json

**CRITICAL**: The feature_list.json is the source of truth for project progress.
Tests are NEVER removed, only marked as passing. This prevents declaring the project
complete prematurely.

### Quality Framework Integration

Read `quality_framework.md` in the project context for the full schema. Each feature MUST include:

1. **Definition of Ready (DoR)** checklist - Is the feature ready to implement?
2. **Acceptance Criteria** - Specific, testable criteria (Given/When/Then format)
3. **Test Approach** - What types of tests, fixtures, mocks, and assertions
4. **Dependencies** - What must be done first
5. **Definition of Done (DoD)** checklist - How do we know it's complete?

### INVEST Principles

Features should be:
- **I**ndependent - Can be built without blocking on others
- **N**egotiable - Defines "what" not "how"
- **V**aluable - Delivers user/business value
- **E**stimable - Clear enough to understand scope
- **S**mall - Completable in 1-3 sessions
- **T**estable - Has measurable success criteria

**Minimum 200 features** covering all aspects of the project specification.

### Enhanced Feature Schema

Each feature should follow this structure:

```json
{
  "id": "feat_001",
  "category": "core_behavior",
  "title": "Search employees by skill",
  "description": "Users can search for employees who have specific skills",
  "business_value": "Enables resource managers to quickly find qualified staff",

  "acceptance_criteria": [
    {
      "id": "ac_001",
      "given": "A knowledge base with employee skill data",
      "when": "User queries 'find Python developers'",
      "then": "Returns list of employees with Python skill"
    }
  ],

  "test_approach": {
    "test_types": ["unit", "integration", "evaluation"],
    "fixtures": ["fixtures/employees.json"],
    "mocks": ["knowledge_base"],
    "assertions": ["Response contains employee objects"]
  },

  "dependencies": {
    "features": ["kb_setup"],
    "infrastructure": ["s3_vectors"],
    "credentials": ["AWS_PROFILE"]
  },

  "dor_checklist": {
    "clear_description": true,
    "acceptance_criteria": true,
    "test_approach": true,
    "dependencies_resolved": false,
    "tech_aligned": true
  },

  "dod_checklist": {
    "code_complete": false,
    "unit_tests_pass": false,
    "coverage_threshold_met": false,
    "integration_tests_pass": false,
    "deployed": false,
    "smoke_tests_pass": false
  },

  "passes": false
}
```

### How to Extract Categories from app_spec.txt

Read the `<technology_stack>` and other sections in app_spec.txt to determine:
1. What technologies need validation (creates `tech_stack` tests)
2. What infrastructure needs deployment (creates `infrastructure` tests)
3. What core behaviors need testing (creates behavior tests)
4. What integrations need verification (creates `integration` tests)

### Category: tech_stack (10+ tests)

**Extract from app_spec.txt** - Look for `<technology_stack>`, `<agent_framework>`, `<ai_models>`, etc.

Create tests that validate the correct technology stack is used:

```json
{
  "category": "tech_stack",
  "test_type": "code_validation",
  "description": "Agent uses the framework specified in app_spec.txt",
  "validation": [
    "Main agent file imports from the specified framework",
    "Tools are defined using the framework's patterns",
    "Configuration matches app_spec.txt requirements"
  ],
  "source": "<framework> from app_spec.txt <technology_stack> section",
  "passes": false
}
```

**Example: If app_spec.txt specifies `<agent_framework>FastAPI</agent_framework>`:**
```json
{
  "category": "tech_stack",
  "test_type": "code_validation",
  "description": "API is built using FastAPI framework",
  "validation": [
    "main.py imports from fastapi",
    "Routes use FastAPI decorators",
    "Dependency injection follows FastAPI patterns"
  ],
  "passes": false
}
```

**Example: If app_spec.txt specifies `<agent_framework>Strands Agents</agent_framework>`:**
```json
{
  "category": "tech_stack",
  "test_type": "code_validation",
  "description": "Agent is built using Strands Agents SDK",
  "validation": [
    "Agent imports from strands package",
    "Tools use @strands.tool decorator",
    "Agent configuration follows Strands patterns"
  ],
  "passes": false
}
```

### Category: test_setup (from testing_strategy.md)

Tests for setting up the testing infrastructure defined in testing_strategy.md.

```json
{
  "category": "test_setup",
  "test_type": "boilerplate",
  "description": "Test framework is configured and working",
  "validation": [
    "pytest.ini or pyproject.toml has test configuration",
    "conftest.py has shared fixtures",
    "Sample test runs successfully"
  ],
  "passes": false
}
```

Include tests for:
- Test framework configuration (from testing_strategy.md)
- Mock service setup
- Test fixtures directory structure
- CI workflow file creation
- Coverage configuration (if specified in strategy)

### Category: credential_validation (10+ tests)

**Extract from app_spec.txt** - Look for `<data_sources>`, `<security>`, integrations.

```json
{
  "category": "credential_validation",
  "test_type": "startup_check",
  "description": "Required credentials are present and valid",
  "validation": [
    "Credential validation script succeeds",
    "Can authenticate to required services"
  ],
  "passes": false
}
```

### Category: infrastructure (varies based on project)

**Extract from app_spec.txt** - Look for cloud resources, deployment targets, etc.

```json
{
  "category": "infrastructure",
  "test_type": "module_validation",
  "description": "Terraform module is created correctly",
  "validation": [
    "Module files exist",
    "terraform validate passes",
    "terraform plan shows expected resources"
  ],
  "passes": false
}
```

### Category: deployment (10+ tests) - CRITICAL

**These tests verify that infrastructure and agent are ACTUALLY DEPLOYED, not just created.**
**The agent MUST run terraform apply and agentcore deploy to pass these tests.**

```json
{
  "category": "deployment",
  "test_type": "terraform_apply",
  "description": "Terraform apply completes successfully",
  "validation": [
    "terraform apply exits with code 0",
    "No errors in terraform output",
    "State file updated"
  ],
  "passes": false
}
```

```json
{
  "category": "deployment",
  "test_type": "resource_verification",
  "description": "AWS resources exist after deployment",
  "validation": [
    "S3 bucket exists and is accessible (aws s3 ls)",
    "KMS key exists with correct alias",
    "IAM roles exist with correct permissions",
    "Other resources per app_spec.txt verified via CLI"
  ],
  "passes": false
}
```

```json
{
  "category": "deployment",
  "test_type": "agent_packaging",
  "description": "Agent is packaged for deployment",
  "validation": [
    "agent.zip created with src/ and requirements.txt",
    "Entry point (main.py) exists and is valid",
    "All dependencies included"
  ],
  "passes": false
}
```

```json
{
  "category": "deployment",
  "test_type": "agent_deployment",
  "description": "Agent is deployed to AgentCore",
  "validation": [
    "agentcore deploy succeeds",
    "agentcore status shows agent is running",
    "No errors in deployment logs"
  ],
  "passes": false
}
```

```json
{
  "category": "deployment",
  "test_type": "smoke_test",
  "description": "Deployed agent responds to test queries",
  "validation": [
    "agentcore test returns valid response",
    "Response contains expected content",
    "Response time within acceptable limits"
  ],
  "passes": false
}
```

### Category: core_behavior (varies based on project)

**Extract from app_spec.txt** - Look for main functionality, business logic, etc.

```json
{
  "category": "core_behavior",
  "test_type": "functional_test",
  "description": "Core feature works as specified",
  "expected": {
    "input": "example input",
    "output_contains": ["expected elements"]
  },
  "passes": false
}
```

### Category: integration (10+ tests)

**Extract from app_spec.txt** - Look for external services, APIs, etc.

```json
{
  "category": "integration",
  "test_type": "e2e",
  "description": "End-to-end flow works correctly",
  "steps": [
    "Step 1 from app_spec.txt",
    "Step 2 from app_spec.txt"
  ],
  "passes": false
}
```

### Category: error_handling (10+ tests)

Tests for graceful degradation and error scenarios.

```json
{
  "category": "error_handling",
  "test_type": "resilience_test",
  "description": "System handles error gracefully",
  "mock_conditions": {
    "service_unavailable": true
  },
  "expected": {
    "graceful_message": true,
    "no_crash": true
  },
  "passes": false
}
```

**IMPORTANT RULES:**
- All tests start with `"passes": false`
- Categories should match what's in app_spec.txt
- Include `evaluation_thresholds` where applicable
- Tests are NEVER removed, only marked as passing
- Add `"source"` field to reference which part of app_spec.txt the test validates

---

## TASK 4: Generate Synthetic Test Fixtures

Create realistic test data for mocking external services based on what app_spec.txt specifies.

### fixtures/ directory

Create sample data files appropriate for your project:
- Sample input data
- Expected output data
- Mock service responses
- Edge case scenarios

---

## TASK 5: Create Project Infrastructure

Create the following for the project:

### credentials.py
Create a project-specific credential validation script based on what app_spec.txt requires:

```python
#!/usr/bin/env python3
"""
Credential validation for this project.
Validates that required credentials are present in .env
"""
import os
from pathlib import Path

def load_env():
    """Load .env file into environment."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

def validate():
    """Validate required credentials based on app_spec.txt requirements."""
    load_env()
    errors = []

    # Add checks based on what app_spec.txt requires
    # Example:
    # if not os.environ.get("AWS_PROFILE") and not os.environ.get("AWS_ACCESS_KEY_ID"):
    #     errors.append("AWS credentials not configured")

    if errors:
        print("Credential validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("All credentials validated successfully")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if validate() else 1)
```

### init.sh
Create an initialization script:

```bash
#!/bin/bash
set -e

echo "=== Development Environment Setup ==="

# 1. Validate Python environment
python --version || { echo "Python required"; exit 1; }

# 2. Create virtual environment if needed
if [ ! -d "venv" ]; then
    python -m venv venv
fi
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Validate credentials
python credentials.py || { echo "Credential validation failed"; exit 1; }

# 5. Project-specific initialization (based on app_spec.txt)
# Add steps here based on what the project needs

echo "=== Setup Complete ==="
```

---

## TASK 6: Create Project Structure

Set up the directory structure based on what app_spec.txt specifies.
Read the specification to determine:
- Source code organization
- Test file locations
- Configuration file locations
- Infrastructure code locations (if applicable)

---

## TASK 7: Create Workflow Phases

Read `workflow_template.md` and `stage_gates.md` from the project context.
Create `workflow_phases.md` in the project directory that defines the concrete phases for THIS project.

### Steps:
1. Read `workflow_template.md` to understand the phase structure
2. Read `stage_gates.md` to understand HITL requirements
3. Read `app_spec.txt` to determine which phases apply
4. Create `workflow_phases.md` with project-specific phases

### Example workflow_phases.md:

```markdown
# Workflow Phases for [Project Name]

Generated from app_spec.txt by the initializer agent.

## Current Phase: 1 - Local Development

---

## Phase 1: Local Development

**Goal**: Implement core functionality with mocked external services

**Categories from feature_list.json**:
- credential_validation
- tech_stack
- [other categories that can be tested with mocks]

**Exit Criteria**:
- All listed category tests pass with MOCK_SERVICES=true
- Code follows patterns from app_spec.txt

**CI/CD**:
- Create .github/workflows/test.yml with basic test workflow

---

## Phase 2: Infrastructure

**Goal**: Deploy cloud infrastructure from app_spec.txt

**Categories**:
- infrastructure

**Exit Criteria**:
- Terraform applies successfully
- All infrastructure tests passing

**CI/CD**:
- Add terraform validate step to workflow

---

## Phase 3: [External Service] Integration

**Stage Gate**: pre_[service]_integration (see stage_gates.md)

**Goal**: Configure and integrate [external service from app_spec.txt]

**Categories**:
- [integration categories]

**Exit Criteria**:
- Service configured and connected
- Integration tests passing

---

[Additional phases based on app_spec.txt...]
```

### Key Principles:
- Only include phases that apply to THIS project
- Reference specific categories from feature_list.json
- Include Stage Gates where human action is required
- CI/CD should be incremental - add to it each phase

---

## TASK 8: Create HITL Checkpoint

After completing the above tasks, create a checkpoint for human review.

Write `HITL_CHECKPOINT.md`:

```markdown
# Human-in-the-Loop Checkpoint: Initializer Complete

## Status: AWAITING HUMAN REVIEW

The initializer agent has completed the following:

### Generated Artifacts
- [ ] `testing_strategy.md` - Testing approach based on tech stack research
- [ ] `feature_list.json` - Evaluation test cases (informed by testing strategy)
- [ ] `workflow_phases.md` - Development phases for this project
- [ ] `fixtures/` - Synthetic test data for mocking
- [ ] `init.sh` - Environment setup script
- [ ] `credentials.py` - Credential validation script
- [ ] Project directory structure
- [ ] `requirements.txt` - Dependencies

### Review Required
Please review the following before restarting the agent:

1. **testing_strategy.md**: Is the testing approach appropriate for the tech stack?
   Are the recommended tools and frameworks correct? Is CI/CD properly planned?

2. **feature_list.json**: Are the test cases comprehensive? Do they align with
   the testing strategy? Are test_setup tasks included?

3. **workflow_phases.md**: Are the phases correct for this project? Are Stage
   Gates defined where human action is needed?

4. **fixtures/**: Is the synthetic test data realistic? Does it cover edge cases?

5. **Project structure**: Does the module layout make sense for this project?

### Credentials Status
[List credential status based on what was validated]

### To Continue
After reviewing the above:
1. Make any adjustments to generated files
2. Approve to continue to Phase 1
```

Update `claude-progress.txt` with session summary.

---

## TASK 9: GRACEFUL HALT

After creating `HITL_CHECKPOINT.md` and updating `claude-progress.txt`:

1. Commit all work:
```bash
git add .
git commit -m "Initializer complete: feature_list.json, fixtures, project structure

- Generated evaluation test cases from app_spec.txt
- Created synthetic test data for mocking
- Set up project directory structure
- HITL checkpoint created for human review"
```

2. **STOP EXECUTION** - Do not proceed to implementation.

The human will review your work, make any adjustments, and restart the agent.

---

## NOTES FOR FUTURE AGENTS

When resuming after HITL approval:

1. Check for `HITL_CHECKPOINT_APPROVED.md` or absence of `HITL_CHECKPOINT.md`
2. Read `claude-progress.txt` to understand current state
3. Read `HITL_FEEDBACK.md` if present for human feedback
4. Continue with implementation based on feature_list.json priority

Remember:
- Read app_spec.txt for project-specific requirements
- Test via the evaluation harness appropriate for your project
- Use mocks for external services during development
- Halt gracefully at defined checkpoints
