# Blushift

A generic, extensible harness for building autonomous AI agents using the Claude Code SDK. Designed for projects that need human-in-the-loop checkpoints, evaluation frameworks, and infrastructure automation.

Blu-shift (or Blueshift) is a term borrowed from astrophysics. It describes the phenomenon where the light from an object moving toward an observer is shifted toward the blue end of the spectrum.

In the context of your agentic harness, it serves as a powerful metaphor for progress, velocity, and closing the gap. While "Redshift" represents things moving away (entropy, technical debt, project drift), Blu-shift represents a project rapidly approaching completion. It signals that the "Squad" is actively pulling the future state of the product toward the present through continuous, 24/7 iteration.

## Features

- **Two-Agent Pattern**: Initializer agent sets up fixtures and test cases, coding agent implements features
- **Human-in-the-Loop (HITL)**: Interactive CLI checkpoints for approval/denial/amendment
- **Evaluation Framework**: LLM-as-judge evaluation with optional DeepEval integration
- **Infrastructure Support**: Built-in Terraform validation and AWS resource checking
- **Security**: Sandboxed execution with extensible command allowlists
- **MCP Servers**: Pre-configured for Slack, GitHub, AWS, Puppeteer, and more
- **Credential Management**: Fail-fast validation with clear error messages
- **Project Isolation**: Each generated project has its own git repository

## Quick Start

### Prerequisites

- Python 3.12+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- [uv](https://github.com/astral-sh/uv) for Python package management (recommended)

### Installation

```bash
# Clone the repository
git clone git@github.com:gazzwi86/blueshift.git
cd blueshift

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

The harness separates **generic reusable code** from **project-specific configuration**:

```
blueshift/
│
├── lib/                              # REUSABLE LIBRARY (generic)
│   ├── hitl.py                       # Human-in-the-loop checkpoint system
│   │
│   ├── prompts/                      # Generic prompt templates
│   │   ├── __init__.py               # PromptLoader with combination logic
│   │   ├── initializer_prompt.md     # Generic initializer template
│   │   └── coding_prompt.md          # Generic coding template
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
│       ├── session.py                # run_agent_session()
│       └── logger.py                 # SessionLogger for debugging
│
├── project_context/                  # PROJECT-SPECIFIC CONTEXT
│   ├── app_spec.txt                  # Project specification (required)
│   ├── harness_capabilities.md       # Available tools/MCP servers (required)
│   ├── workflow_template.md          # Phase templates (required)
│   ├── stage_gates.md                # HITL trigger definitions (required)
│   ├── init_additions.md             # Optional: extra initializer instructions
│   └── coding_additions.md           # Optional: extra coding instructions
│
├── generations/                      # GENERATED PROJECTS (gitignored)
│   └── my_project/                   # Each project has its own git repo
│       ├── .git/                     # Separate from harness git
│       ├── feature_list.json         # Test cases (source of truth)
│       ├── testing_strategy.md       # Testing approach for this project
│       ├── workflow_phases.md        # Phases for this project
│       ├── claude-progress.txt       # Session handoff notes
│       ├── logs/                     # Session transcripts
│       └── ...
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

### Key Concepts

| Component | Location | Purpose |
|-----------|----------|---------|
| **Generic Prompts** | `lib/prompts/` | Reusable templates with few-shot examples |
| **Project Context** | `project_context/` | Project-specific specification and capabilities |
| **Generated Projects** | `generations/` | Output projects with their own git repos |
| **Project Config** | Root (`security.py`, `credentials.py`, `client.py`) | Project-specific configuration |

### Prompt Loading

The `PromptLoader` combines generic templates with optional project-specific additions:

1. Generic template from `lib/prompts/` (e.g., `initializer_prompt.md`)
2. Optional additions from `project_context/` (e.g., `init_additions.md`)

This allows you to customize behavior without modifying the generic templates.

## Extending for Your Project

### 1. Project Specification

Edit `project_context/app_spec.txt` with your project requirements. The initializer agent will:
- Read this specification
- Extract technology stack requirements
- Generate appropriate test cases in `feature_list.json`

### 2. Optional Prompt Additions

Create optional files in `project_context/` to add project-specific instructions:

**`project_context/init_additions.md`** - Added to initializer prompt:
```markdown
## Project-Specific Requirements

This project MUST use the AWS Strands Agent SDK. Key requirements:
- Import from `strands` package
- Use `@strands.tool` decorators
- Follow Strands patterns from https://strandsagents.com
```

**`project_context/coding_additions.md`** - Added to coding prompt:
```markdown
## Additional Testing Requirements

Always run `npm run lint` before committing code.
```

### 3. Security Configuration

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

### 4. Credential Requirements

Edit `credentials.py` to define required credentials for your project.

### 5. MCP Server Configuration

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

When you choose **Amend**, feedback is written to `HITL_FEEDBACK.md` in the project directory, which the agent reads on the next session.

## Workflow Phases

The harness implements a **phase-driven development workflow**:

### Two-Agent Pattern

1. **Initializer Agent** (Session 1) - Sets up project foundation:
   - Reads `app_spec.txt` and researches tech stack
   - Creates `testing_strategy.md` with testing approach
   - Generates `feature_list.json` with 200+ test cases
   - Creates `workflow_phases.md` defining development phases
   - Stops at HITL checkpoint for human review

2. **Coding Agent** (Sessions 2+) - Implements features:
   - Reads progress files and git history to orient
   - Follows current phase from `workflow_phases.md`
   - Implements one feature at a time
   - Marks tests passing in `feature_list.json`
   - Checks for stage gates requiring HITL

### Key Artifacts

| Artifact | Purpose |
|----------|---------|
| `feature_list.json` | Source of truth - test cases, `passes: false → true` |
| `testing_strategy.md` | Testing approach for this project's tech stack |
| `workflow_phases.md` | Current phase and exit criteria |
| `claude-progress.txt` | Session handoff notes between context windows |

### Stage Gates

Defined in `project_context/stage_gates.md`:
- **post_initialization** - Review artifacts before coding begins
- **pre_slack_integration** - Manual Slack app configuration required
- **pre_production** - Approval before production deployment

## Session Flow

```
start.py
    │
    ▼
Validate credentials (fail-fast)
    │
    ▼
Create project directory with git init
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
    ├─ Generic template from lib/prompts/
    └─ + Optional additions from project_context/
    │
    ▼
run_agent_session()
    │
    ▼
Auto-continue or halt
```

## Git Isolation

**Important**: Each generated project has its own git repository, separate from the harness.

- The harness repository is at `blueshift/.git`
- Generated projects have their own repos at `generations/<project>/.git`
- Agent commits go to the project's git, not the harness
- `generations/` is gitignored in the harness

This ensures:
- Clean separation between harness and generated code
- You can push generated projects to their own remotes
- Harness updates don't affect generated projects

## Testing

### Preflight Check

Run before starting the harness:

```bash
python preflight.py        # Full check (includes security tests)
python preflight.py -q     # Quick check (skip security tests)
```

### Spec Validation

Validate app_spec.txt independently:

```bash
python validate_spec.py                           # Default: project_context/app_spec.txt
python validate_spec.py path/to/app_spec.txt      # Custom path
```

### Post-Initialization Validation

After Session 1 completes (at HITL checkpoint), validate the generated artifacts:

```bash
python post_init_validation.py generations/pixieops_v2
```

This checks:
- feature_list.json has valid schema
- Required categories present (including **deployment**)
- Minimum feature count (200+)
- DoR/DoD checklists present
- testing_strategy.md and workflow_phases.md exist
- Deployment phases included in workflow

**Run this before approving the HITL checkpoint!**

### Feature List Schema Validation

Validate feature_list.json against the enhanced schema:

```bash
python -m lib.validation.feature_schema generations/pixieops_v2/feature_list.json
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

## Session Logging

Full session transcripts are saved to `<project>/logs/` for debugging:

- `session_YYYYMMDD_HHMMSS_NNN.log` - Human-readable transcript
- `session_YYYYMMDD_HHMMSS_NNN.jsonl` - Machine-readable for analysis

Each log contains:
- Full prompt sent to the agent
- All tool calls and their inputs
- Tool results (including blocked commands)
- Text output from the agent
- Errors and session status

Use these logs to debug agent behavior, identify blocked commands, or analyze tool usage patterns.

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
