# Ultra Coding Agent - Collaboration Plan

### 2. Brief-to-Feature-List Generation (In Progress)

**Goal:** Enable the agent to accept a natural language project brief and auto-generate the `feature_list.json`.

**Approach:**
1. Create a `brief_parser.py` module that:
   - Takes natural language input
   - Uses Claude to analyze the brief
   - Extracts user stories and requirements
   - Generates structured feature list in the expected JSON format

2. Modify `prompts/initializer_prompt.md` to:
   - Accept brief content as input
   - Generate comprehensive feature breakdown
   - Output to `feature_list.json`

3. Update `coding_agent.py` to:
   - Add `--brief` parameter
   - Call brief parser before initializer
   - Pass parsed requirements to initializer agent

**Expected Flow:**
```
User Brief (natural language)
    ↓
Brief Parser (Claude analysis)
    ↓
Structured Requirements
    ↓
Initializer Agent
    ↓
feature_list.json (200+ test cases)
```

### 3. Auto-Test Generation

**Goal:** Generate comprehensive E2E tests from the feature list.

**Approach:**
1. Create `test_generator.py` that:
   - Reads `feature_list.json`
   - Generates Playwright test files for each feature category
   - Creates test utilities and helpers
   - Outputs to `tests/` directory

2. Integrate with initializer:
   - After feature list generation
   - Before first coding session
   - Set up test infrastructure

### 4. Multi-Agent System

**Goal:** Add specialist agents for different phases of development.

**Agents to Create:**

#### Architect Agent
- **Input:** Project brief + requirements
- **Output:** System design document, tech stack recommendations, file structure
- **Runs:** Before initializer
- **Creates:** 
  - `architecture.md`
  - `tech_stack.json`
  - `file_structure.json`

#### Product Owner Agent
- **Input:** Implemented feature + feature spec
- **Output:** Acceptance decision (pass/fail/needs-work)
- **Runs:** After each feature completion
- **Validates:**
  - Functionality matches requirements
  - E2E tests actually verify the feature
  - Visual design meets expectations

#### Code Reviewer Agent
- **Input:** Git diff from feature branch
- **Output:** Review comments, approval/rejection
- **Runs:** Before marking feature as complete
- **Checks:**
  - Code quality and style
  - Security issues
  - Performance concerns
  - Test coverage

#### Orchestrator
- **Input:** Project state, agent outputs
- **Output:** Next agent to run, commands to execute
- **Runs:** Between all agents
- **Coordinates:**
  - Agent sequencing
  - Data flow between agents
  - Error handling and retries

**Execution Flow:**
```
User Brief
    ↓
Architect Agent → architecture.md, tech_stack.json
    ↓
Brief Parser → structured requirements
    ↓
Initializer Agent → feature_list.json, project setup
    ↓
[Loop for each feature]
    Coding Agent → implements feature
        ↓
    Code Reviewer → reviews changes
        ↓
    Product Owner → acceptance testing
        ↓
    [If approved: mark complete, continue]
    [If rejected: provide feedback, retry]
```

### 5. Blog Post Improvements Integration

**Improvements Already Implemented:**
- ✅ Two-agent pattern (initializer + coder)
- ✅ JSON-based progress tracking
- ✅ Incremental work (one feature at a time)
- ✅ Git commits for persistence
- ✅ Startup protocol (read progress files)

**Still To Implement:**
- [ ] Browser-based E2E testing (currently just has infrastructure)
- [ ] Verification-before-implementation (run passing tests first)
- [ ] Visual appearance validation
- [ ] Enhanced test coverage

## Repository Structure Plan

```
ultra-coding-agent/
├── README.md                     # ✅ Updated with roadmap
├── COLLABORATION.md              # ✅ This file
├── LICENSE                       # ⏳ Need to add
├── .gitignore                    # ✅ Complete
│
├── coding_agent.py      # ✅ Main entry (needs --brief param)
├── agent.py                      # ✅ Agent session logic
├── client.py                     # ✅ Claude SDK client
├── security.py                   # ✅ Command allowlist
├── progress.py                   # ✅ Progress tracking
├── prompts.py                    # ✅ Prompt utilities
│
├── agents/                       # 🔜 Multi-agent system
│   ├── __init__.py
│   ├── base_agent.py            # Base agent class
│   ├── architect.py             # System design agent
│   ├── initializer.py           # Project setup (refactored from agent.py)
│   ├── coder.py                 # Feature implementation (refactored)
│   ├── reviewer.py              # Code review agent
│   ├── product_owner.py         # Acceptance testing agent
│   └── orchestrator.py          # Agent coordinator
│
├── generators/                   # 🔜 Code generation utilities
│   ├── __init__.py
│   ├── brief_parser.py          # Brief → requirements
│   ├── test_generator.py        # Features → E2E tests
│   └── spec_generator.py        # Requirements → app_spec.txt
│
├── prompts/                      # ✅ Existing prompts
│   ├── app_spec.txt             # Application specification template
│   ├── initializer_prompt.md    # First session prompt
│   ├── coding_prompt.md         # Continuation prompt
│   │
│   └── agents/                  # 🔜 Agent-specific prompts
│       ├── architect_prompt.md
│       ├── reviewer_prompt.md
│       └── po_prompt.md
│
├── requirements.txt              # ✅ Python deps
├── test_security.py              # ✅ Security tests
│
└── examples/                     # 🔜 Example briefs and outputs
    ├── claude_clone_brief.md
    ├── simple_todo_brief.md
    └── ecommerce_brief.md
```

## Implementation Priority

### Phase 2A: Brief-to-Feature-List (Current Focus)
1. Create `generators/brief_parser.py`
2. Add `--brief` parameter to main script
3. Update initializer to use parsed brief
4. Test with example briefs

### Phase 2B: Test Generation
1. Create `generators/test_generator.py`
2. Generate Playwright test scaffolding
3. Integrate with initializer workflow

### Phase 3: Multi-Agent System
1. Create `agents/` module structure
2. Implement base agent class
3. Build Architect agent
4. Build Product Owner agent
5. Build Code Reviewer agent
6. Build Orchestrator
7. Integrate into main workflow

### Phase 4: Refinements
1. Enhanced error handling
2. Better progress visualization
3. Agent communication logs
4. Performance optimizations

## Questions for Collaboration

1. **Brief Format:** Do you want to support:
   - Plain text files?
   - Markdown with sections?
   - Structured YAML/JSON?
   - All of the above?

2. **Test Strategy:** Should tests be:
   - Generated upfront (all 200 at once)?
   - Generated incrementally (per feature)?
   - Mix of both?

3. **Architecture Agent:** How opinionated should it be?
   - Strongly opinionated (enforce best practices)?
   - Flexible (consider multiple approaches)?
   - Configurable (user sets preferences)?

4. **Quality Gates:** How strict?
   - Block on any code review issues?
   - Allow warnings but block errors?
   - Advisory only?

5. **Agent Communication:** How should agents share context?
   - Files only (architecture.md, etc.)?
   - Structured data (JSON)?
   - Agent memory/context sharing?

## Next Session Plan

I'll start implementing the brief parser. Here's what I'll do:

1. Create `generators/` directory structure
2. Implement `brief_parser.py` with Claude API
3. Add example briefs in `examples/`
4. Update `coding_agent.py` with `--brief` flag
5. Test the flow end-to-end with a simple brief

Let me know if you have preferences on any of the collaboration questions above, or if you'd like me to proceed with my best judgment on these decisions.
