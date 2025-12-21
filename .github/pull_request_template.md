## Summary

<!-- Provide a concise summary of what this PR does -->

## Motivation

<!-- Why is this change needed? What problem does it solve? Link related issues. -->

Closes #(issue)

## Type of Change

<!-- Mark the relevant option with an 'x' -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🔧 Refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] ✅ Test improvements
- [ ] 🔨 Build/CI changes
- [ ] 🎨 Code style/formatting

## Changes Made

<!-- List the specific changes in this PR -->

-
-
-

## Testing

<!-- Describe how you tested these changes -->

### Test Cases Added/Updated

<!-- List new or modified tests -->

-
-

### Manual Testing Performed

<!-- Describe manual testing steps -->

1.
2.
3.

### Test Results

```bash
# Paste relevant test output
poetry run pytest ...
```

## Architecture/Design Decisions

<!-- If this PR involves architectural decisions, explain them here -->

<!-- Delete this section if not applicable -->

## Screenshots/Examples

<!-- If applicable, add screenshots or code examples demonstrating the changes -->

<!-- Delete this section if not applicable -->

## Documentation

<!-- What documentation was updated? -->

- [ ] README.md updated
- [ ] Docstrings added/updated
- [ ] Type hints added/updated
- [ ] docs/ updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] No documentation changes needed

## Checklist

### Code Quality

- [ ] Code passes `poetry run ruff format .` (formatting)
- [ ] Code passes `poetry run ruff check .` (linting)
- [ ] Code passes security checks (`poetry run ruff check --select S .`)
- [ ] All tests pass (`poetry run pytest`)
- [ ] Coverage meets minimum threshold (70%)
- [ ] No new warnings or errors introduced

### Testing Requirements

- [ ] Tests follow HTTP-only mocking pattern (no internal method mocks)
- [ ] All GraphQL calls verify: call count, request content, and response data
- [ ] Test fixtures include ALL required fields for Pydantic models
- [ ] New functionality has comprehensive test coverage

### Architecture Compliance

- [ ] Follows UNSET pattern for optional fields
- [ ] Uses identity map via `StashObject.from_dict()`
- [ ] Implements dirty tracking for entity changes
- [ ] Follows existing code patterns and conventions

### Git & Documentation

- [ ] Commit messages follow conventional format (`feat:`, `fix:`, `docs:`, etc.)
- [ ] Commits are signed (GPG/SSH)
- [ ] Branch is up-to-date with `main`
- [ ] No merge conflicts
- [ ] PR description is clear and complete

### License & Legal

- [ ] I agree to license my contributions under AGPL-3.0
- [ ] No proprietary or copyrighted code included without permission
- [ ] No secrets or credentials committed

## Breaking Changes

<!-- If this is a breaking change, describe: -->
<!-- - What breaks -->
<!-- - Migration path for users -->
<!-- - Why the breaking change is necessary -->

<!-- Delete this section if not applicable -->

## Related Issues/PRs

<!-- Link related issues and PRs -->

- Related to #
- Depends on #
- Blocks #

## Additional Notes

<!-- Any other information reviewers should know -->

---

## For Reviewers

<!-- Notes for code reviewers -->

### Areas Needing Extra Attention

-
-

### Questions for Reviewers

-
- ***

🤖 Generated with [Claude Code](https://claude.com/claude-code)
