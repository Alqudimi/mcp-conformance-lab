"""Validated configuration models for MCP Conformance Lab."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from ..domain.models import TransportKind
from ..domain.policies import ExecutionPolicy


class StdioTransportConfig(BaseModel):
    """Configuration for an explicitly approved argv-based subprocess."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal[TransportKind.STDIO] = TransportKind.STDIO
    command: str = Field(min_length=1)
    args: tuple[str, ...] = ()
    allow_exec: bool = False
    cwd: Path | None = None
    env: dict[str, str] = Field(default_factory=dict)


class HTTPTransportConfig(BaseModel):
    """Configuration for a Streamable HTTP MCP target."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal[TransportKind.STREAMABLE_HTTP] = TransportKind.STREAMABLE_HTTP
    url: AnyHttpUrl
    headers_env: dict[str, str] = Field(default_factory=dict)


class ReportsConfig(BaseModel):
    """Output configuration for report and evidence artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    directory: Path = Path(".mcp-lab/runs")
    formats: tuple[Literal["terminal", "json", "sarif"], ...] = ("terminal", "json")


class LabConfig(BaseModel):
    """Top-level, versioned configuration contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    name: str = Field(min_length=1)
    transport: StdioTransportConfig | HTTPTransportConfig
    policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    baseline: Path | None = None
    reports: ReportsConfig = Field(default_factory=ReportsConfig)
