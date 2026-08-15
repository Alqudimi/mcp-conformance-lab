# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-08-15

### Added

- Python CLI package with `doctor`, `discover`, `snapshot`, `baseline`, `check`, and `verify` commands.
- MCP stdio and Streamable HTTP adapters over the official Python SDK.
- Deterministic contract snapshots and SHA-256 digests.
- Built-in rules for identifier uniqueness, JSON Schema validity, and capability consistency.
- Baseline comparison with severity-aware findings and exit codes.
- Atomic local evidence bundles with manifest verification.
- JSON, SARIF 2.1.0, and terminal reports.
- Safe fixture servers and integration-oriented examples.
- Unit tests, type checking, linting, packaging, and security-focused project documentation.

### Deliberately out of scope

- Gateway, firewall, dashboard, remote evidence store, LLM-based judgment, and automatic destructive tool execution.
