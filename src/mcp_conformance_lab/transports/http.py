"""Streamable HTTP transport adapter."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from ..config.schema import HTTPTransportConfig
from ..domain.errors import ConfigurationError, ProtocolError, TransportError, TransportTimeoutError
from ..domain.policies import ExecutionPolicy


def _resolve_headers(config: HTTPTransportConfig) -> dict[str, str]:
    """Resolve header values from named environment variables without logging secrets."""
    headers: dict[str, str] = {}
    for header_name, env_name in config.headers_env.items():
        value = os.environ.get(env_name)
        if value is None:
            raise ConfigurationError(
                f"required HTTP header environment variable is missing: {env_name}",
                details={"header": header_name, "environment_variable": env_name},
            )
        headers[header_name] = value
    return headers


@asynccontextmanager
async def open_streamable_http_session(
    config: HTTPTransportConfig,
    policy: ExecutionPolicy,
) -> AsyncIterator[ClientSession]:
    """Open and initialize a Streamable HTTP MCP session."""
    headers = _resolve_headers(config)
    client = httpx.AsyncClient(
        headers=headers,
        timeout=httpx.Timeout(
            timeout=policy.case_timeout_seconds,
            connect=policy.connect_timeout_seconds,
        ),
        follow_redirects=False,
    )
    try:
        try:
            with anyio.fail_after(policy.connect_timeout_seconds):
                async with streamable_http_client(str(config.url), http_client=client) as (
                    read_stream,
                    write_stream,
                    _get_session_id,
                ):
                    async with ClientSession(read_stream, write_stream) as session:
                        try:
                            await session.initialize()
                        except Exception as exc:
                            raise ProtocolError(
                                "MCP initialization failed",
                                details={"endpoint": str(config.url)},
                            ) from exc
                        yield session
        except TimeoutError as exc:
            raise TransportTimeoutError(
                "MCP Streamable HTTP initialization exceeded its timeout"
            ) from exc
        except httpx.HTTPError as exc:
            raise TransportError(
                "MCP Streamable HTTP request failed",
                details={"endpoint": str(config.url)},
            ) from exc
    finally:
        await client.aclose()
