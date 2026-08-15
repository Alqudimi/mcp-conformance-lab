# Testing and Verification

The project uses multiple test layers because protocol tooling can fail at different boundaries. Unit tests cover pure domain and rule behavior, transport tests cover security gates and environment resolution, integration tests exercise local MCP sessions, and shell smoke tests validate the packaged CLI against real stdio and Streamable HTTP fixtures.

## Local quality gates

```bash
python -m pytest -q
ruff check src tests
ruff format --check src tests
mypy src
python -m build
```

For a dependency audit in a clean environment:

```bash
python -m venv /tmp/mcp-audit-venv
/tmp/mcp-audit-venv/bin/python -m pip install . pip-audit
/tmp/mcp-audit-venv/bin/pip-audit
```

The audit should be run in a clean environment because a global developer image can contain unrelated packages and vulnerabilities. The package itself is not published to PyPI as part of this repository setup, so pip-audit reports it as an untracked local distribution while still checking its dependencies.

## End-to-end scenario

The stdio fixture validates discovery, baseline creation, unchanged checks, SARIF output, evidence writing, and manifest verification:

```bash
mcp-conformance baseline --config examples/fixture.yaml
mcp-conformance check --config examples/fixture.yaml --format sarif
mcp-conformance verify .mcp-lab/runs/<run-id>
```

The regression path is equally important. Renaming the fixture tool from `echo` to `echo_v2` causes `MCP-BASELINE-TOOL-REMOVED` and `MCP-BASELINE-TOOL-ADDED`, and the CLI exits with code `2` under the default `fail_on: high` policy.

The Streamable HTTP fixture can be started with `python examples/http_fixture_server.py`, after which `mcp-conformance discover --config examples/http_fixture.yaml` validates the HTTP adapter. The fixture binds only to localhost and has no destructive tools.

## Failure scenarios covered

The test suite covers invalid configuration fields, missing files, path escapes, non-canonical ordering, duplicate identifiers, invalid JSON Schema, capability mismatch, missing HTTP header environment, stdio without explicit opt-in, evidence tampering, baseline changes, and CLI output shapes. The security-sensitive tests assert rejection rather than attempting to prove a sandbox.
