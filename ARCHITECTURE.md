# Ultra Coding Agent - Architecture

## Project Structure (Implemented)

```
ultra-coding-agent/
│
├── lib/                              # REUSABLE LIBRARY
│   ├── __init__.py
│   │
│   ├── hitl.py                       # Human-in-the-loop checkpoint system
│   │                                 # - Interactive CLI (approve/deny/amend)
│   │                                 # - HITLCheckpoint, HITLManager classes
│   │
│   ├── client.py                     # Claude SDK client builder
│   │                                 # - create_base_client()
│   │                                 # - ClientBuilder pattern
│   │
│   ├── prompts.py                    # Prompt template loader
│   │                                 # - PromptLoader class
│   │                                 # - get_initializer_prompt(), get_coding_prompt()
│   │
│   ├── security/                     # Security framework
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseSecurity class, validation functions
│   │   └── test_security.py          # Security tests
│   │
│   ├── evaluation/                   # Agent evaluation framework
│   │   ├── __init__.py
│   │   ├── harness.py                # EvaluationHarness, DeepEval integration
│   │   └── evaluators/
│   │       ├── __init__.py
│   │       └── base.py               # BaseEvaluator, LLMJudgeEvaluator
│   │
│   ├── infrastructure/               # Infrastructure testing
│   │   ├── __init__.py
│   │   ├── terraform.py              # TerraformValidator, TerraformTestRunner
│   │   └── aws.py                    # AWSResourceChecker
│   │
│   ├── credentials/                  # Credential validation
│   │   ├── __init__.py
│   │   └── validator.py              # CredentialValidator, ValidationResult
│   │
│   ├── progress/                     # Progress tracking
│   │   ├── __init__.py
│   │   └── tracker.py                # ProgressTracker, count_passing_tests()
│   │
│   └── orchestrator/                 # Session management
│       ├── __init__.py
│       └── session.py                # run_agent_session(), AgentSession
│
├── prompts/                          # PROMPT TEMPLATES
│   ├── initializer_prompt.md         # First session: setup, fixtures, feature_list
│   ├── coding_prompt.md              # Continuation: implement features
│   ├── harness_capabilities.md       # Available tools documentation
│   └── app_spec.txt                  # Project specification (edit for your project)
│
├── start.py                          # ENTRY POINT
│                                     # - CLI argument parsing
│                                     # - Main agent loop
│                                     # - HITL checkpoint handling
│
├── preflight.py                      # PRE-RUN VERIFICATION
│                                     # - Check all imports work
│                                     # - Validate credentials
│                                     # - Run security tests
│                                     # - Verify prompt files exist
│
├── security.py                       # PROJECT-SPECIFIC SECURITY
│                                     # - Extends lib/security/base.py
│                                     # - ALLOWED_COMMANDS set
│                                     # - bash_security_hook export
│
├── credentials.py                    # PROJECT-SPECIFIC CREDENTIALS
│                                     # - get_credentials()
│                                     # - validate_credentials()
│                                     # - print_credential_status()
│
├── client.py                         # PROJECT-SPECIFIC CLIENT
│                                     # - create_client() with MCP servers
│                                     # - MCP tool definitions
│
├── slack_helpers.py                  # PROJECT-SPECIFIC HELPER
│
├── .env.example                      # Environment template (safe to commit)
├── .gitignore                        # Git ignore patterns
├── pyproject.toml                    # Python project config
├── LICENSE                           # MIT License
├── CONTRIBUTING.md                   # Contribution guidelines
└── README.md                         # This documentation
```

## Library vs Project-Specific

### Library (lib/) - Reusable

These modules are project-agnostic and can be used across different agent projects:

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `lib/hitl.py` | Interactive checkpoints | `checkpoint()`, `require_approval()`, `HITLCheckpoint` |
| `lib/client.py` | SDK client builder | `create_base_client()`, `ClientBuilder` |
| `lib/prompts.py` | Prompt loading | `PromptLoader`, `get_initializer_prompt()` |
| `lib/security/base.py` | Security framework | `BaseSecurity`, validation functions |
| `lib/evaluation/` | Agent evaluation | `EvaluationHarness`, `BaseEvaluator` |
| `lib/infrastructure/` | Terraform/AWS | `TerraformValidator`, `AWSResourceChecker` |
| `lib/credentials/` | Credential validation | `CredentialValidator` |
| `lib/progress/` | Progress tracking | `ProgressTracker` |
| `lib/orchestrator/` | Session management | `run_agent_session()` |

### Project-Specific (root) - Configured

These files configure the library for the specific project:

| File | Purpose | Extends |
|------|---------|---------|
| `start.py` | Entry point | Uses lib/orchestrator |
| `security.py` | Command allowlist | Extends lib/security/base.BaseSecurity |
| `credentials.py` | Required credentials | Uses lib/credentials/validator |
| `client.py` | MCP server config | Uses lib/client |
| `prompts/app_spec.txt` | Project spec | N/A |

## Extending for New Projects

### 1. Security Configuration

Edit `security.py` to customize allowed commands:

```python
from lib.security.base import BaseSecurity

class ProjectSecurity(BaseSecurity):
    ALLOWED_COMMANDS = {
        "ls", "cat", "git",  # Basic
        "npm", "node",        # Node.js
        "terraform", "aws",   # Infrastructure
        # Add project-specific commands
    }
```

### 2. Credential Requirements

Edit `credentials.py` to define required credentials:

```python
from lib.credentials import CredentialValidator

def get_credentials():
    validator = CredentialValidator()
    validator.require_aws()
    validator.require("CUSTOM_API_KEY", required=True)
    return validator.validate()
```

### 3. MCP Server Configuration

Edit `client.py` to configure MCP servers:

```python
mcp_servers = {
    "puppeteer": {...},
    "slack": {...},
    "custom_server": {
        "command": "npx",
        "args": ["-y", "@your/mcp-server"]
    }
}
```

### 4. Project Specification

Edit `prompts/app_spec.txt` with your project requirements.

## HITL System

Interactive CLI checkpoints:

```
======================================================================
  HUMAN-IN-THE-LOOP CHECKPOINT
======================================================================

  Checkpoint: initializer_complete
  Review generated test fixtures

  Generated Artifacts:
    - feature_list.json - 150+ evaluation test cases
    - fixtures/ - Synthetic test data

  Please Review:
    1. Are test cases comprehensive?
    2. Is the synthetic data realistic?

======================================================================

  Options:
    [A] Approve - Continue with execution
    [D] Deny    - Halt execution (provide reason)
    [M] Amend   - Approve with feedback/changes

  Your decision (A/D/M):
```

## Session Flow

```
start.py
    │
    ▼
Validate credentials (fail-fast)
    │
    ▼
Check for HITL_CHECKPOINT.md
    │
    ├─ If exists: Display checkpoint, wait for decision
    │
    ▼
Create Claude SDK client
    │
    ▼
Choose prompt (initializer or coding)
    │
    ▼
run_agent_session()
    │
    ▼
Process response, check for HITL
    │
    ▼
Auto-continue or halt
```

## Testing

### Preflight Check (Recommended)

Run before starting the harness to verify configuration:

```bash
python preflight.py        # Full check (includes security tests)
python preflight.py -q     # Quick check (skip security tests)
```

### Individual Tests

```bash
# Security tests only
python -m lib.security.test_security

# Verify imports only
python -c "from lib.hitl import checkpoint; from lib.evaluation import EvaluationHarness; print('OK')"

# Check credentials
python -c "from credentials import get_credentials; c = get_credentials(); print('OK')"
```
