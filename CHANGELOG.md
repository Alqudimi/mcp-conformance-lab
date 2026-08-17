# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- `SizeLimitsRule` (`MCP-CONTRACT-004`) fails loudly when advertised tools, resources, or prompts exceed `policy.max_items`, closing the gap where the size policy was declared but never enforced by any rule.
- Rule unit tests covering pass, boundary, and per-collection failure cases (`tests/unit/test_rules.py`).

## [0.1.1] - 2026-08-16

### Fixed

- Configured missing, non-regular, and malformed baselines now produce explicit machine-readable findings instead of being silently skipped.
- Added regression tests for missing, directory, malformed, and valid baseline paths.

## [0.1.0] - 2026-08-15

### Added

- Python CLI package with `doctor`, `discover`, `snapshot`, `baseline`, `check`, and `verify` commands.
- MCP stdio and Streamable HTTP adapters over the official Python SDK.
- Deterministic contract snapshots and SHA-256 digests.
- Built-in rules for identifier uniqueness, JSON Schema validity, and capability consistency.
- Baseline comparison with severity-aware findings and exit codes.
- Explicit `MCP-BASELINE-MISSING` and `MCP-BASELINE-INVALID` findings for configured baseline failures.
- Atomic local evidence bundles with manifest verification.
- JSON, SARIF 2.1.0, and terminal reports.
- Safe fixture servers and integration-oriented examples.
- Unit tests, type checking, linting, packaging, and security-focused project documentation.

### Deliberately out of scope

- Gateway, firewall, dashboard, remote evidence store, LLM-based judgment, and automatic destructive tool execution.
