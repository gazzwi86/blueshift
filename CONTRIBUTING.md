# Contributing to Ultra Coding Agent

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

Please be respectful and constructive in all interactions. We're building something together.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment:

```bash
uv venv
uv sync
cp .env.example .env
# Configure your .env with test credentials
```

4. Run preflight checks to ensure everything works:

```bash
python preflight.py
```

## Development Workflow

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### Making Changes

1. Create a feature branch from `main`
2. Make your changes
3. Run tests:

```bash
python -m lib.security.test_security
python preflight.py
```

4. Commit with clear messages
5. Push and create a pull request

### Commit Messages

Use clear, descriptive commit messages:

```
Add HITL timeout configuration option

- Add timeout parameter to checkpoint()
- Update HITLCheckpoint to handle timeouts
- Add tests for timeout behavior
```

## Project Structure

### Library Code (`lib/`)

The `lib/` directory contains reusable, project-agnostic modules. When contributing to library code:

- Keep modules focused and single-purpose
- Maintain backward compatibility
- Add type hints
- Include docstrings
- Add tests where applicable

### Project-Specific Code (root)

Files in the root directory are project-specific configurations. When contributing:

- Document any new configuration options
- Update `.env.example` if adding new environment variables
- Keep security configurations restrictive by default

## Adding New Features

### New Library Module

1. Create the module in `lib/`
2. Add exports to `lib/__init__.py` or the appropriate subpackage
3. Add tests if applicable
4. Update `ARCHITECTURE.md`

### New MCP Server Support

1. Add server configuration to `client.py`
2. Add any required environment variables to `.env.example`
3. Update credentials handling if needed
4. Document in README

### New Security Commands

1. Add to `ALLOWED_COMMANDS` in `security.py`
2. If the command needs validation, add to `COMMANDS_NEEDING_EXTRA_VALIDATION`
3. Implement validation function in `lib/security/base.py`
4. Add test cases to `lib/security/test_security.py`

## Testing

### Running Tests

```bash
# Security tests
python -m lib.security.test_security

# Full preflight check
python preflight.py

# Quick preflight (skip security tests)
python preflight.py -q
```

### Writing Tests

- Add test cases to `lib/security/test_security.py` for security-related changes
- Test both allowed and blocked cases
- Include edge cases

## Pull Request Process

1. Ensure all tests pass
2. Update documentation as needed
3. Add a clear description of changes
4. Link any related issues
5. Request review from maintainers

### PR Checklist

- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No sensitive data committed
- [ ] `.env.example` updated (if new env vars)
- [ ] `ARCHITECTURE.md` updated (if structure changed)

## Security Considerations

### Never Commit

- API keys or tokens
- Private keys
- Passwords or secrets
- `.env` files
- `secrets/` directory contents

### Always Review

- New bash commands added to allowlist
- Changes to security validation logic
- New MCP server configurations
- Credential handling code

## Questions?

Open an issue for questions or discussion. We're happy to help!
