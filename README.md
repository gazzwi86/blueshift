# Ultra Coding Agent

A generic, extensible harness for building autonomous AI agents using the Claude Code SDK. Designed for projects that need human-in-the-loop checkpoints, evaluation frameworks, and infrastructure automation.

## Features

- **Two-Agent Pattern**: Initializer agent sets up fixtures and test cases, coding agent implements features
- **Human-in-the-Loop (HITL)**: Interactive CLI checkpoints for approval/denial/amendment
- **Evaluation Framework**: LLM-as-judge evaluation with optional DeepEval integration
- **Infrastructure Support**: Built-in Terraform validation and AWS resource checking
- **Security**: Sandboxed execution with extensible command allowlists
- **MCP Servers**: Pre-configured for Slack, GitHub, AWS, Puppeteer, and more
- **Credential Management**: Fail-fast validation with clear error messages

## Quick Start

### Prerequisites

- Python 3.12+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- [uv](https://github.com/astral-sh/uv) for Python package management (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/ultra-coding-agent.git
cd ultra-coding-agent

# Create virtual environment and install dependencies
uv venv
uv sync

# Copy environment template and configure
cp .env.example .env
# Edit .env with your credentials (see Configuration below)
```

### Authentication

You have two options for authenticating with Claude:

**Option 1: Claude Code Subscription (Recommended)**

Use your existing Claude Code subscription - no additional API costs:

```bash
# Set up a long-lived token for your Claude Code subscription
claude setup-token

# Follow the prompts to authenticate
# The token is stored locally and used automatically
```

**Option 2: Anthropic API Key**

Use direct API access (billed separately):

```bash
# Add to your .env file
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

Get your API key from: https://console.anthropic.com/

### Configuration

Edit `.env` with your credentials:

```bash
# Authentication (optional if using Claude Code subscription token)
# ANTHROPIC_API_KEY=sk-ant-...

# Optional (for MCP servers)
AWS_PROFILE=your-profile
SLACK_BOT_TOKEN=xoxb-...
GITHUB_TOKEN=ghp_...
```

### Running

```bash
# Activate virtual environment
source .venv/bin/activate

# Run preflight checks (recommended)
python preflight.py

# Start the agent
python start.py --project-dir ./my_project
```

## Architecture

```
ultra-coding-agent/
│
├── lib/                              # REUSABLE LIBRARY
│   ├── hitl.py                       # Human-in-the-loop checkpoint system
│   ├── prompts.py                    # Prompt template loader
│   ├── client.py                     # Claude SDK client builder
│   │
│   ├── security/                     # Security framework
│   │   ├── base.py                   # BaseSecurity class
│   │   └── test_security.py          # Security tests
│   │
│   ├── evaluation/                   # Agent evaluation framework
│   │   ├── harness.py                # EvaluationHarness, DeepEval integration
│   │   └── evaluators/base.py        # BaseEvaluator, LLMJudgeEvaluator
│   │
│   ├── infrastructure/               # Infrastructure validation
│   │   ├── terraform.py              # TerraformValidator
│   │   └── aws.py                    # AWSResourceChecker
│   │
│   ├── credentials/                  # Credential validation
│   │   └── validator.py              # CredentialValidator
│   │
│   ├── progress/                     # Progress tracking
│   │   └── tracker.py                # ProgressTracker
│   │
│   └── orchestrator/                 # Session management
│       └── session.py                # run_agent_session()
│
├── prompts/                          # PROMPT TEMPLATES
│   ├── initializer_prompt.md         # First session prompt
│   ├── coding_prompt.md              # Continuation prompt
│   └── app_spec.txt                  # Project specification
│
├── start.py                          # Entry point
├── preflight.py                      # Pre-run verification
├── security.py                       # Project-specific security config
├── credentials.py                    # Project-specific credentials
├── client.py                         # Project-specific MCP config
│
├── .env.example                      # Environment template
└── pyproject.toml                    # Python dependencies
```

### Library vs Project-Specific

| Component | Location | Purpose |
|-----------|----------|---------|
| **Library** | `lib/` | Reusable, project-agnostic modules |
| **Config** | Root | Project-specific configuration |
| **Prompts** | `prompts/` | Customizable prompt templates |

## Extending for Your Project

### 1. Security Configuration

Edit `security.py` to customize allowed bash commands:

```python
from lib.security.base import BaseSecurity

class ProjectSecurity(BaseSecurity):
    ALLOWED_COMMANDS = {
        "ls", "cat", "git",      # Basic
        "npm", "node",            # Node.js
        "terraform", "aws",       # Infrastructure
        # Add your commands here
    }
```

### 2. Credential Requirements

Edit `credentials.py` to define required credentials for your project.

### 3. MCP Server Configuration

Edit `client.py` to configure which MCP servers are available:

```python
mcp_servers = {
    "puppeteer": {...},
    "slack": {...},
    "your_server": {
        "command": "npx",
        "args": ["-y", "@your/mcp-server"]
    }
}
```

### 4. Project Specification

Edit `prompts/app_spec.txt` with your project requirements.

## Human-in-the-Loop (HITL) Checkpoints

The agent can pause for human review at critical points:

```
======================================================================
  HUMAN-IN-THE-LOOP CHECKPOINT
======================================================================

  Checkpoint: initializer_complete
  Review generated test fixtures

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
Check for HITL checkpoint
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
Auto-continue or halt
```

## Testing

### Preflight Check

Run before starting the harness:

```bash
python preflight.py        # Full check (includes security tests)
python preflight.py -q     # Quick check (skip security tests)
```

### Security Tests

```bash
python -m lib.security.test_security
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir` | Directory for the project | `generations/autonomous_demo_project` |
| `--max-iterations` | Max agent iterations | Unlimited |
| `--model` | Claude model to use | `claude-sonnet-4-5-20250929` |

## Security Model

Defense-in-depth approach:

1. **OS-level Sandbox**: Bash commands run in isolated environment
2. **Filesystem Restrictions**: Operations restricted to project directory
3. **Command Allowlist**: Only explicitly permitted commands can run
4. **MCP Server Isolation**: Each server runs in its own process

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built on [Anthropic's Claude Code SDK](https://github.com/anthropics/claude-code)
- Implements patterns from [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
