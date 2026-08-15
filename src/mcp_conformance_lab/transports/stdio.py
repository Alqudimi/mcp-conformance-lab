"""Safe stdio transport adapter."""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, get_default_environment, stdio_client

from ..config.schema import StdioTransportConfig
from ..domain.errors import ConfigurationError, TransportError
from ..domain.policies import ExecutionPolicy


def _build_environment(config: StdioTransportConfig, policy: ExecutionPolicy) -> dict[str, str]:
    """Build a minimal child environment without inheriting secrets by default."""
    base = dict(os.environ) if policy.inherit_environment else get_default_environment()
    base.update(config.env)
    return base


def _resolve_cwd(config: StdioTransportConfig, policy: ExecutionPolicy) -> Path | None:
    """Resolve and validate the child working directory."""
    if config.cwd is None:
        return None
    try:
        return policy.validate_working_directory(config.cwd)
    except ValueError as exc:
        raise ConfigurationError(str(exc)) from exc


@asynccontextmanager
async def open_stdio_session(
    config: StdioTransportConfig,
    policy: ExecutionPolicy,
) -> AsyncIterator[ClientSession]:
    """Open an MCP stdio session using an argv list and SDK-managed cleanup."""
    if not config.allow_exec or not policy.allow_exec:
        raise ConfigurationError(
            "stdio execution is disabled; set both transport.allow_exec and "
            "policy.allow_exec to true"
        )
    params = StdioServerParameters(
        command=config.command,
        args=list(config.args),
        env=_build_environment(config, policy),
        cwd=_resolve_cwd(config, policy),
    )
    try:
        async with (
            stdio_client(params, errlog=sys.stderr) as (read_stream, write_stream),
            ClientSession(read_stream, write_stream) as session,
        ):
            yield session
    except ConfigurationError:
        raise
    except OSError as exc:
        raise TransportError(
            f"could not start stdio MCP server: {config.command}",
            details={"command": config.command},
        ) from exc
