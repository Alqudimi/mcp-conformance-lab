import pytest

from mcp_conformance_lab.config.schema import HTTPTransportConfig, StdioTransportConfig
from mcp_conformance_lab.domain.errors import ConfigurationError
from mcp_conformance_lab.domain.policies import ExecutionPolicy
from mcp_conformance_lab.transports.http import _resolve_headers
from mcp_conformance_lab.transports.stdio import open_stdio_session


def test_http_headers_are_resolved_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    config = HTTPTransportConfig(
        url="http://127.0.0.1:8765/mcp",
        headers_env={"Authorization": "MCP_TEST_TOKEN"},
    )
    monkeypatch.setenv("MCP_TEST_TOKEN", "secret-value")

    assert _resolve_headers(config) == {"Authorization": "secret-value"}


def test_missing_http_header_environment_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    config = HTTPTransportConfig(
        url="http://127.0.0.1:8765/mcp",
        headers_env={"Authorization": "MCP_MISSING_TOKEN"},
    )
    monkeypatch.delenv("MCP_MISSING_TOKEN", raising=False)

    with pytest.raises(ConfigurationError, match="environment variable is missing"):
        _resolve_headers(config)


@pytest.mark.asyncio
async def test_stdio_requires_both_explicit_execution_flags() -> None:
    config = StdioTransportConfig(command="python3", allow_exec=True)

    with pytest.raises(ConfigurationError, match="stdio execution is disabled"):
        async with open_stdio_session(config, ExecutionPolicy(allow_exec=False)):
            raise AssertionError("session should not open")
