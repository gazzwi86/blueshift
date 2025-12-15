# Ultra Coding Agent

An enhanced autonomous coding agent built on Anthropic's autonomous coding quickstart, with additional capabilities for project planning, architecture, and quality assurance.

## Overview

This is an evolution of Anthropic's autonomous coding agent that implements the improvements recommended in their [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) blog post, plus additional enhancements:

### Core Features (from Anthropic)

- **Two-Agent Pattern**: Initializer + Coding agent for structured development
- **Incremental Development**: One feature at a time with mandatory commits
- **End-to-End Testing**: Browser-based verification via Playwright
- **Progress Tracking**: JSON-based feature lists and git history
- **Security**: Sandboxed execution with command allowlisting

### Ultra Enhancements (Planned)

- **Brief-to-Feature-List**: Accept project briefs and auto-generate feature lists
- **Auto-Test Generation**: Create comprehensive test suites from feature specifications
- **Architect Agent**: Design system architecture before implementation
- **Product Owner Agent**: Sign off on completed features and verify acceptance criteria
- **Enhanced Quality Gates**: Multi-agent code review and validation

## Prerequisites

**Required:** Install the latest versions of both Claude Code and the Claude Agent SDK:

```bash
# Install Claude Code CLI (latest version required)
npm install -g @anthropic-ai/claude-code

# Install Python dependencies
pip install -r requirements.txt
```

Verify your installations:
```bash
claude --version  # Should be latest version
pip show claude-code-sdk  # Check SDK is installed
```

**API Key:** Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Quick Start

```bash
python coding_agent.py --project-dir ./my_project
```

For testing with limited iterations:
```bash
python coding_agent.py --project-dir ./my_project --max-iterations 3
```

## Important Timing Expectations

> **Warning: This demo takes a long time to run!**

- **First session (initialization):** The agent generates a `feature_list.json` with 200 test cases. This takes several minutes and may appear to hang - this is normal. The agent is writing out all the features.

- **Subsequent sessions:** Each coding iteration can take **5-15 minutes** depending on complexity.

- **Full app:** Building all 200 features typically requires **many hours** of total runtime across multiple sessions.

**Tip:** The 200 features parameter in the prompts is designed for comprehensive coverage. If you want faster demos, you can modify `prompts/initializer_prompt.md` to reduce the feature count (e.g., 20-50 features for a quicker demo).

## Roadmap

### Phase 1: Foundation ✅
- [x] Port Anthropic autonomous coding agent
- [x] Setup repository structure
- [ ] Add comprehensive documentation

### Phase 2: Brief-to-Code
- [ ] Implement brief parser (natural language → structured requirements)
- [ ] Auto-generate feature_list.json from briefs
- [ ] Create test generation from features

### Phase 3: Multi-Agent System
- [ ] Architect agent (system design)
- [ ] Product Owner agent (acceptance criteria validation)
- [ ] Code reviewer agent (quality gates)
- [ ] Orchestrator for agent coordination

### Phase 4: Advanced Features
- [ ] Continuous integration testing
- [ ] Progressive refinement of features
- [ ] Performance benchmarking
- [ ] Security scanning integration

## Improvements from Blog Post

This agent implements the key improvements from Anthropic's long-running agent blog:

1. **Two-Agent Pattern**: Separate initialization from incremental coding
2. **Structured Progress**: JSON-based tracking prevents inappropriate modifications
3. **Incremental Work**: Forces one feature at a time
4. **E2E Testing**: Browser automation for real user verification
5. **Startup Protocol**: Always reads context before new work
6. **Verification First**: Tests must pass before new features

## How It Works

### Two-Agent Pattern

1. **Initializer Agent (Session 1):** Reads `app_spec.txt`, creates `feature_list.json` with 200 test cases, sets up project structure, and initializes git.

2. **Coding Agent (Sessions 2+):** Picks up where the previous session left off, implements features one by one, and marks them as passing in `feature_list.json`.

### Session Management

- Each session runs with a fresh context window
- Progress is persisted via `feature_list.json` and git commits
- The agent auto-continues between sessions (3 second delay)
- Press `Ctrl+C` to pause; run the same command to resume

## Security Model

This demo uses a defense-in-depth security approach (see `security.py` and `client.py`):

1. **OS-level Sandbox:** Bash commands run in an isolated environment
2. **Filesystem Restrictions:** File operations restricted to the project directory only
3. **Bash Allowlist:** Only specific commands are permitted:
   - File inspection: `ls`, `cat`, `head`, `tail`, `wc`, `grep`
   - Node.js: `npm`, `node`
   - Version control: `git`
   - Process management: `ps`, `lsof`, `sleep`, `pkill` (dev processes only)

Commands not in the allowlist are blocked by the security hook.

## Project Structure

```
autonomous-coding/
├── coding_agent.py  # Main entry point
├── agent.py                  # Agent session logic
├── client.py                 # Claude SDK client configuration
├── security.py               # Bash command allowlist and validation
├── progress.py               # Progress tracking utilities
├── prompts.py                # Prompt loading utilities
├── prompts/
│   ├── app_spec.txt          # Application specification
│   ├── initializer_prompt.md # First session prompt
│   └── coding_prompt.md      # Continuation session prompt
└── requirements.txt          # Python dependencies
```

## Generated Project Structure

After running, your project directory will contain:

```
my_project/
├── feature_list.json         # Test cases (source of truth)
├── app_spec.txt              # Copied specification
├── init.sh                   # Environment setup script
├── claude-progress.txt       # Session progress notes
├── .claude_settings.json     # Security settings
└── [application files]       # Generated application code
```

## Running the Generated Application

After the agent completes (or pauses), you can run the generated application:

```bash
cd generations/my_project

# Run the setup script created by the agent
./init.sh

# Or manually (typical for Node.js apps):
npm install
npm run dev
```

The application will typically be available at `http://localhost:3000` or similar (check the agent's output or `init.sh` for the exact URL).

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir` | Directory for the project | `./autonomous_demo_project` |
| `--max-iterations` | Max agent iterations | Unlimited |
| `--model` | Claude model to use | `claude-sonnet-4-5-20250929` |

## Customization

### Changing the Application

Edit `prompts/app_spec.txt` to specify a different application to build.

### Adjusting Feature Count

Edit `prompts/initializer_prompt.md` and change the "200 features" requirement to a smaller number for faster demos.

### Modifying Allowed Commands

Edit `security.py` to add or remove commands from `ALLOWED_COMMANDS`.

## Troubleshooting

**"Appears to hang on first run"**
This is normal. The initializer agent is generating 200 detailed test cases, which takes significant time. Watch for `[Tool: ...]` output to confirm the agent is working.

**"Command blocked by security hook"**
The agent tried to run a command not in the allowlist. This is the security system working as intended. If needed, add the command to `ALLOWED_COMMANDS` in `security.py`.

**"API key not set"**
Ensure `ANTHROPIC_API_KEY` is exported in your shell environment.

## Contributing

This is a personal project for extending Anthropic's autonomous coding capabilities. Contributions and suggestions welcome!

## License

Based on Anthropic's autonomous coding quickstart. See LICENSE for details.

## Acknowledgments

- Built on [Anthropic's Claude Agent SDK](https://github.com/anthropics/anthropic-quickstarts)
- Implements patterns from [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
