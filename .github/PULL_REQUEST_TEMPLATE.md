## Summary

Describe the problem and the smallest useful change.

## Verification

- [ ] `python -m pytest -q`
- [ ] `ruff check src tests`
- [ ] `ruff format --check src tests`
- [ ] `mypy src`
- [ ] `python -m build` when packaging changes

## Contract and security impact

Does this change modify a public CLI, evidence schema, baseline behavior, transport execution, or secret handling? Describe migration and explicit opt-in requirements.

## Documentation

- [ ] README or docs updated when behavior changed.
- [ ] Changelog entry added when user-visible.
