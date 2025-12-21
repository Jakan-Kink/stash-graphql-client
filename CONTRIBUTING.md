# Contributing to stash-graphql-client

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the stash-graphql-client project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Testing Requirements](#testing-requirements)
- [Code Quality Standards](#code-quality-standards)
- [Architecture Overview](#architecture-overview)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [AI-Assisted Contributions](#ai-assisted-contributions)
- [License](#license)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please read it before contributing.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Poetry for dependency management
- Git for version control
- A Stash instance (optional, for integration testing)

### Repository Structure

```
stash-graphql-client/
├── stash_graphql_client/     # Main package
│   ├── client/               # Client mixins and base classes
│   ├── types/                # Pydantic models for Stash entities
│   └── utils/                # Utility functions
├── tests/                    # Test suite
│   ├── client/               # Client tests
│   ├── types/                # Model tests
│   └── fixtures/             # Test fixtures and data
├── docs/                     # Documentation
└── .github/                  # GitHub configuration
```

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/stash-graphql-client.git
cd stash-graphql-client
```

### 2. Install Dependencies

**IMPORTANT:** This project uses Poetry for dependency management.

```bash
# Install Poetry if you don't have it
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate the virtual environment
poetry shell
```

**Never edit `pyproject.toml` directly for dependencies.** Use Poetry commands:

```bash
# Add a production dependency
poetry add <package>

# Add a development dependency
poetry add --group dev <package>

# Add a test dependency
poetry add --group test <package>

# Update dependencies
poetry update
```

### 3. Set Up Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Test the hooks (optional)
pre-commit run --all-files
```

## Development Workflow

### Branch Strategy

- `main` - Stable release branch
- `develop` - Development branch (if used)
- `feature/*` - New features
- `fix/*` - Bug fixes
- `chores/*` - Maintenance tasks (dependency updates, etc.)
- `docs/*` - Documentation updates

### Making Changes

1. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Write code following project patterns
   - Add tests for new functionality
   - Update documentation as needed

3. **Run code quality checks**

```bash
# Format code (includes import sorting)
poetry run ruff format .

# Lint and auto-fix issues
poetry run ruff check --fix .

# Security scanning (via Ruff)
poetry run ruff check --select S .
```

**Note:** The project also uses **Snyk** for dependency vulnerability scanning. Snyk checks are run automatically in CI/CD pipelines.

4. **Run tests**

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_file.py

# Run tests in parallel (faster)
poetry run pytest -n 8

# Run verbose output
poetry run pytest -v
```

5. **Commit your changes**

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: Add support for fuzzy date filtering

- Implements FuzzyDate validation for Scene queries
- Adds tests for year/month/day precision
- Updates documentation with examples"
```

**Commit Message Format:**

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or updates
- `refactor:` Code refactoring
- `chore:` Maintenance tasks (dependencies, config, etc.)
- `perf:` Performance improvements

## Testing Requirements

### Testing Philosophy

This project follows **strict testing principles**:

- ✅ **Mock at HTTP boundary only** - Use `respx` to mock GraphQL HTTP responses
- ✅ **Test real code paths** - Execute actual client methods, serialization, deserialization
- ✅ **Verify request AND response** - Every GraphQL call must assert both query/variables AND response data
- ✅ **Use real Pydantic models** - Test actual type validation and model construction
- ❌ **Never mock internal methods** - No mocking of client mixin methods, helper functions, or type conversions

### Mandatory Test Pattern

Every test with GraphQL calls MUST verify:

1. **Call count** - Exact number of GraphQL requests made
2. **Request content** - Query structure AND variables for each call
3. **Response data** - Returned data structure and key fields

**Example:**

```python
import respx
import httpx
import pytest
from stash_graphql_client import StashClient

@pytest.mark.asyncio
async def test_find_scene(respx_mock):
    """Test finding a scene by ID."""

    # 1. Mock the GraphQL HTTP response
    graphql_route = respx.post("http://localhost:9999/graphql").mock(
        return_value=httpx.Response(200, json={
            "data": {
                "findScene": {
                    "id": "123",
                    "title": "Test Scene",
                    "urls": [],
                    "organized": True,
                    # ... all required fields
                }
            }
        })
    )

    # 2. Execute real client code
    client = StashClient(url="http://localhost:9999/graphql")
    scene = await client.find_scene("123")

    # 3. REQUIRED: Verify call count
    assert len(graphql_route.calls) == 1

    # 4. REQUIRED: Verify request content
    request = json.loads(graphql_route.calls[0].request.content)
    assert "findScene" in request["query"]
    assert request["variables"]["id"] == "123"

    # 5. REQUIRED: Verify response data
    assert scene.id == "123"
    assert scene.title == "Test Scene"
```

### Coverage Requirements

- **Minimum coverage:** 70% overall
- **Parallel execution:** Tests run with pytest-xdist (8 workers by default)
- **Complete GraphQL responses:** All test fixtures must include ALL required fields

For detailed testing patterns, see [TESTING_REQUIREMENTS.md](TESTING_REQUIREMENTS.md).

## Code Quality Standards

### Code Formatting

- **Formatter:** Ruff (replaces Black and isort)
- **Line length:** 100 characters (configured in `pyproject.toml`)
- **Import sorting:** Automatically handled by Ruff

### Linting

- **Linter:** Ruff (replaces Flake8, pycodestyle, pyflakes, etc.)
- **Rules:** Configured in `pyproject.toml`
- **Auto-fix:** Use `poetry run ruff check --fix .`

### Type Checking (Planned)

**Note:** Full mypy compliance is planned but not currently enforced.

Type hints should follow these guidelines:

- Use modern syntax (`list[str]` not `List[str]`)
- Compatible with Python 3.12+
- Complete and accurate where possible

**Future Goal:** Enable strict mypy checking across the codebase.

### Security

The project uses multiple layers of security scanning:

- **Ruff Security Rules:** Built-in security linting (`poetry run ruff check --select S .`)
- **Snyk:** Dependency vulnerability scanning (runs in CI/CD)
- **Pre-commit hooks:** Automated security checks before commits

## Architecture Overview

### Core Patterns

This project uses several advanced architectural patterns:

#### 1. Pydantic v2 with Wrap Validators

All entity types use Pydantic `BaseModel` with `mode='wrap'` validators for identity map integration.

```python
from pydantic import BaseModel, model_validator

class StashObject(BaseModel):
    @model_validator(mode='wrap')
    @classmethod
    def _identity_map_validator(cls, data, handler):
        # Check cache BEFORE Pydantic processes data
        # ...
```

#### 2. UNSET Pattern

Three-state field system: UNSET (not queried), None (null), or actual value.

```python
from stash_graphql_client.types import UNSET, UnsetType

class Scene(StashObject):
    # Required field, but UNSET if not in GraphQL fragment
    title: str | UnsetType = UNSET

    # Optional field - can be value, None, or UNSET
    rating100: int | None | UnsetType = UNSET
```

See [docs/guide/unset-pattern.md](docs/guide/unset-pattern.md) for details.

#### 3. Identity Map

`StashEntityStore` caches entities and ensures same-ID objects share references.

```python
scene1 = Scene.from_dict({"id": "123", "title": "Test"})
scene2 = Scene.from_dict({"id": "123", "title": "Test"})
assert scene1 is scene2  # Same cached object
```

#### 4. Dirty Tracking

Snapshot-based change detection for minimal update payloads.

```python
scene = await client.find_scene("123")
scene.title = "Updated"
print(scene.is_dirty())  # True
print(scene.get_changed_fields())  # {"title": "Updated"}
```

### When Adding New Features

1. **Read existing code first** - Understand patterns before implementing
2. **Follow established patterns** - Use UNSET, identity map, wrap validators
3. **Add comprehensive tests** - Follow HTTP-only mocking pattern
4. **Update documentation** - Keep docs in sync with code
5. **Avoid over-engineering** - Keep solutions simple and focused

## Pull Request Process

### Before Submitting

- [ ] Code passes all quality checks (`ruff format`, `ruff check`)
- [ ] All tests pass (`pytest`)
- [ ] Coverage meets minimum threshold (70%)
- [ ] Documentation is updated (if applicable)
- [ ] Commit messages follow conventional format
- [ ] Branch is up-to-date with `main`

### Submitting a PR

1. **Push your branch**

```bash
git push origin feature/your-feature-name
```

2. **Create Pull Request on GitHub**
   - Use the PR template (auto-populated)
   - Provide clear description of changes
   - Link related issues
   - Add appropriate labels

3. **PR Review Process**
   - Maintainers will review your PR
   - Address feedback and requested changes
   - Keep the PR updated with `main` if needed
   - CI checks must pass

4. **After Approval**
   - Maintainer will merge using "Squash and Merge"
   - Your contribution will be in the next release!

### PR Template

When you create a PR, the template will include:

- **Summary** - What does this PR do?
- **Motivation** - Why is this change needed?
- **Changes** - List of specific changes made
- **Testing** - How was this tested?
- **Checklist** - Pre-submission checklist items

## Issue Guidelines

### Reporting Bugs

Use the **Bug Report** template and include:

- Environment details (Python version, OS, stash-graphql-client version)
- Steps to reproduce
- Expected behavior
- Actual behavior
- Minimal code example
- Error messages and stack traces

### Requesting Features

Use the **Feature Request** template and include:

- Clear use case description
- Proposed solution or API design
- Alternatives considered
- Example code showing desired usage
- Potential implementation approach (optional)

### Documentation Issues

Use the **Documentation** template for:

- Corrections to existing docs
- Missing documentation
- Unclear explanations
- Example requests

### Questions

For usage questions:

- Use **GitHub Discussions** (preferred)
- Use **Question/Support** issue template (if Discussions not available)
- Check existing issues and docs first

## AI-Assisted Contributions

### Our Stance on AI Tools

We welcome contributions created with the assistance of AI tools (ChatGPT, Claude, GitHub Copilot, etc.). AI can be a valuable productivity multiplier when used responsibly.

### Requirements for AI-Assisted Contributions

✅ **Allowed:**
- Using AI tools to generate boilerplate code
- AI-assisted code review and refactoring suggestions
- AI-generated test cases (with human verification)
- Using AI for documentation writing and examples
- AI help with debugging and problem-solving

❌ **Not Allowed:**
- Submitting AI-generated code without understanding it
- Blindly accepting AI suggestions without testing
- AI-generated code that violates project patterns or quality standards
- Including AI tool configuration files in your contributions (see below)

### Guidelines

1. **Understand the Code:** You must fully understand any AI-generated code you submit. You are responsible for its correctness, security, and maintainability.

2. **Follow Project Patterns:** AI suggestions must conform to project architecture (UNSET pattern, identity map, Pydantic validators, etc.). Don't let AI introduce anti-patterns.

3. **Test Thoroughly:** AI-generated code must pass all quality checks and tests. Add tests if they don't exist.

4. **Review Carefully:** Treat AI output as you would a junior developer's PR - review critically, verify assumptions, test edge cases.

### AI Configuration Files - DO NOT COMMIT

**IMPORTANT:** Do not include AI tool configuration files in your pull requests:

❌ **Never commit:**
- `.claude/` directories with personal AI settings
- `.cursorrules` files
- `.aider` configuration
- Copilot or similar tool-specific workspace settings
- Any personal AI assistant configurations

✅ **Project-level AI config is OK:**
- Shared `.github/` templates are fine
- **GitHub Copilot Custom Agents** (`.github/agents/*.agent.md`)
- Public documentation about AI tool compatibility
- General guidance files (like this section)

**Why?** Personal AI configurations:
- Pollute the repository with individual preferences
- Create merge conflicts
- May expose personal workflow details
- Aren't useful to other contributors with different tools

### Best Practices

1. **Start with Documentation:** Read existing code and architecture docs before generating code
2. **Iterate in Small Chunks:** Generate and test small pieces rather than entire files
3. **Verify Patterns:** Cross-reference AI output against existing patterns in the codebase
4. **Human Review:** Have a human (you!) review all AI suggestions before committing
5. **Test Real Scenarios:** AI-generated tests should cover realistic use cases, not just happy paths

### Example Good AI Usage

```
Developer: "I need to add a new field to the Scene type for parental_rating with UNSET support"

AI: [Generates code following UNSET pattern]

Developer: ✅ Reviews code
           ✅ Verifies UNSET pattern is correct
           ✅ Adds comprehensive tests
           ✅ Updates documentation
           ✅ Submits PR with confidence
```

### Example Bad AI Usage

```
Developer: "Generate a complete StashClient implementation"

AI: [Generates 2000 lines of code]

Developer: ❌ Doesn't review thoroughly
           ❌ Doesn't understand wrap validators
           ❌ Doesn't test edge cases
           ❌ Submits PR hoping CI will catch issues
```

## Development Tips

### Using AI Tools Effectively

- Ask AI to explain existing patterns before generating new code
- Use AI for tedious boilerplate, human brain for architecture
- Verify AI assumptions against real Stash API documentation
- When AI suggests a pattern, search the codebase to see if it already exists

### Running Specific Tests

```bash
# Run tests for a specific module
poetry run pytest tests/client/test_scene_mixin.py

# Run tests matching a pattern
poetry run pytest -k "test_create"

# Run with verbose output and show print statements
poetry run pytest -v -s

# Run without parallel execution
poetry run pytest -n 0
```

### Debugging Tests

```bash
# Run with debugger on failure
poetry run pytest --pdb

# Stop on first failure
poetry run pytest -x

# Show local variables on failure
poetry run pytest -l
```

### Updating Dependencies

```bash
# Update all dependencies
poetry update

# Update specific dependency
poetry update <package-name>

# Check for outdated dependencies
poetry show --outdated
```

## Getting Help

- **Documentation:** Check [docs/](docs/) directory
- **Discussions:** GitHub Discussions for Q&A
- **Issues:** Search existing issues before creating new ones
- **Email:** github@jakan.co for private inquiries

## License

By contributing to stash-graphql-client, you agree that your contributions will be licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This means:

- Your contributions must be open source
- Derivative works must also be AGPL-3.0
- Network use requires source disclosure
- You retain copyright but grant usage rights

See [LICENSE](LICENSE) for full details.

## Recognition

Contributors are recognized in:

- GitHub Contributors page
- Release notes (for significant contributions)
- Project documentation (for major features)

Thank you for contributing to stash-graphql-client! 🎉

---

**Questions?** Open a Discussion or contact github@jakan.co
