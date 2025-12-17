# Ultra Coding Agent - Architecture

This document describes the architecture of the autonomous coding agent harness.

Based on patterns from [Anthropic's Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

---

## Two-Agent Pattern

The harness uses a **two-agent architecture**:

### Initializer Agent (Session 1 Only)
- Reads `app_spec.txt` to understand project requirements
- Researches and creates `testing_strategy.md`
- Generates `feature_list.json` with 200+ test cases
- Creates `workflow_phases.md` defining development phases
- Sets up project structure, fixtures, and infrastructure scripts
- Creates HITL checkpoint for human review before coding begins

### Coding Agent (Sessions 2+)
- Reads progress files and git history to orient itself
- Follows `workflow_phases.md` to determine current phase
- Implements features one at a time, following test-driven approach
- Marks tests as passing in `feature_list.json` (the source of truth)
- Commits frequently with descriptive messages
- Checks for stage gates requiring HITL approval

---

## Project Structure

```
ultra-coding-agent/
│
├── lib/                              # REUSABLE LIBRARY (generic)
│   ├── __init__.py                   # Package exports
│   │
│   ├── hitl.py                       # Human-in-the-loop checkpoint system
│   │                                 # - checkpoint(), require_approval()
│   │                                 # - HITLCheckpoint, HITLResponse classes
│   │
│   ├── prompts/                      # Generic prompt templates
│   │   ├── __init__.py               # PromptLoader with combination logic
│   │   ├── initializer_prompt.md     # First session: setup and planning
│   │   └── coding_prompt.md          # Subsequent sessions: implementation
│   │
│   ├── security/                     # Security framework
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseSecurity class, validators
│   │   └── test_security.py          # Security tests
│   │
│   ├── evaluation/                   # Agent evaluation framework
│   │   ├── __init__.py
│   │   ├── harness.py                # EvaluationHarness, DeepEval integration
│   │   └── evaluators/
│   │       ├── __init__.py
│   │       └── base.py               # BaseEvaluator, LLMJudgeEvaluator
│   │
│   ├── infrastructure/               # Infrastructure validation
│   │   ├── __init__.py
│   │   ├── terraform.py              # TerraformValidator
│   │   └── aws.py                    # AWSResourceChecker
│   │
│   ├── credentials/                  # Credential validation
│   │   ├── __init__.py
│   │   └── validator.py              # CredentialValidator
│   │
│   ├── progress/                     # Progress tracking
│   │   ├── __init__.py
│   │   └── tracker.py                # ProgressTracker, count_passing_tests()
│   │
│   └── orchestrator/                 # Session management
│       ├── __init__.py
│       ├── session.py                # run_agent_session()
│       └── logger.py                 # SessionLogger for debugging
│
├── project_context/                  # PROJECT-SPECIFIC CONTEXT
│   ├── app_spec.txt                  # Project specification (required)
│   ├── harness_capabilities.md       # Available tools/credentials (required)
│   ├── workflow_template.md          # Phase templates (required)
│   ├── stage_gates.md                # HITL trigger definitions (required)
│   ├── init_additions.md             # Optional: extra initializer instructions
│   └── coding_additions.md           # Optional: extra coding instructions
│
├── generations/                      # GENERATED PROJECTS (gitignored)
│   └── <project>/                    # Each project has its own git repo
│       ├── .git/                     # Separate from harness git
│       ├── feature_list.json         # Test cases (source of truth)
│       ├── testing_strategy.md       # Testing approach for this project
│       ├── workflow_phases.md        # Phases for this project
│       ├── claude-progress.txt       # Session handoff notes
│       ├── logs/                     # Session logs for debugging
│       └── ...                       # Generated application code
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

---

## Key Artifacts

### feature_list.json (Source of Truth)

The feature list is the **anchor** for the entire project. It contains:
- Test cases with explicit descriptions
- Steps for verification
- `"passes": false` → `"passes": true` as features complete

**Critical rule**: Tests are NEVER removed, only marked as passing.

```json
{
  "category": "core_behavior",
  "test_type": "functional_test",
  "description": "User can search employees by skill",
  "validation": ["Returns matching employees", "Includes skill details"],
  "passes": false
}
```

### testing_strategy.md

Created by the initializer after researching the tech stack:
- Identifies testing layers (unit, integration, e2e)
- Recommends testing frameworks
- Documents CI/CD requirements
- Defines quality gates and thresholds

### workflow_phases.md

Defines concrete phases for the project:
- Current phase indicator
- Categories from feature_list.json to complete
- Exit criteria for each phase
- Stage gate references where HITL required

### claude-progress.txt

Session handoff notes that bridge context windows:
- What was completed in each session
- Current phase and status
- Test counts by category
- What to work on next

---

## Prompt Loading

The `PromptLoader` class combines generic templates with project-specific additions:

```
lib/prompts/initializer_prompt.md     (generic template)
           +
project_context/init_additions.md     (optional project-specific)
           =
Final initializer prompt
```

This allows customization without modifying generic templates.

---

## Session Flow

```
start.py
    │
    ▼
Load credentials (fail-fast if required missing)
    │
    ▼
Create/verify project directory with git init
    │
    ▼
Copy project_context files to project
    │
    ▼
Check for HITL checkpoint file
    │
    ├─ If HITL_CHECKPOINT.md exists → Wait for human decision
    │
    ▼
Create Claude SDK client
    │
    ▼
Choose prompt:
    ├─ First run (no feature_list.json) → Initializer prompt
    └─ Subsequent runs → Coding prompt
    │
    ▼
run_agent_session()
    │
    ▼
Log to project/logs/session_*.log
    │
    ▼
Check for new HITL checkpoint
    │
    ▼
Auto-continue or halt
```

---

## Security Model (Defense in Depth)

1. **OS-level Sandbox**: Bash commands run in isolated environment
2. **Filesystem Restrictions**: Operations restricted to project directory
3. **Command Allowlist**: Only explicitly permitted commands can run
4. **MCP Server Isolation**: Each server runs in its own process

See `security.py` for the project-specific allowlist.

---

## HITL (Human-in-the-Loop) System

Interactive CLI checkpoints where the agent pauses for human decision:

```
======================================================================
  HUMAN-IN-THE-LOOP CHECKPOINT
======================================================================

  Checkpoint: initializer_complete
  Review generated test fixtures and workflow phases

  Options:
    [A] Approve - Continue with execution
    [D] Deny    - Halt execution (provide reason)
    [M] Amend   - Approve with feedback/changes
```

Stage gates in `stage_gates.md` define when HITL is required:
- `post_initialization` - After initializer creates artifacts
- `pre_slack_integration` - Before Slack setup (requires manual app config)
- `pre_production` - Before production deployment

---

## Session Logging

Full session transcripts are saved for debugging:
- `<project>/logs/session_YYYYMMDD_HHMMSS_NNN.log` - Human-readable
- `<project>/logs/session_YYYYMMDD_HHMMSS_NNN.jsonl` - Machine-readable

---

## Extending for New Projects

1. **Edit `project_context/app_spec.txt`** - Define your project requirements
2. **Edit `project_context/stage_gates.md`** - Define HITL triggers
3. **Edit `security.py`** - Add allowed commands for your stack
4. **Edit `credentials.py`** - Add required credentials
5. **Edit `client.py`** - Configure MCP servers
6. **Optional**: Add `init_additions.md` or `coding_additions.md`

---

## References

- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Claude Quickstarts: Autonomous Coding](https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding)
- [Claude Code SDK](https://github.com/anthropics/claude-code)
