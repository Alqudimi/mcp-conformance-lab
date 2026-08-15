"""Application orchestration for discovery and contract checks."""

from __future__ import annotations

import json
from pathlib import Path

from mcp import ClientSession

from ..config.schema import HTTPTransportConfig, LabConfig, StdioTransportConfig
from ..domain.errors import ConfigurationError, EvidenceError
from ..domain.models import ContractSnapshot, Finding
from ..rules.builtin import DEFAULT_RULES, evaluate_rules
from ..rules.protocol import ConformanceRule, RuleContext
from ..transports.http import open_streamable_http_session
from ..transports.stdio import open_stdio_session
from .discover import discover_session


async def _discover_with_session(
    session: ClientSession,
    config: LabConfig,
    rules: tuple[ConformanceRule, ...],
) -> tuple[ContractSnapshot, tuple[Finding, ...]]:
    """Run discovery and synchronous snapshot rules inside an open session."""
    snapshot = await discover_session(session, config.policy)
    findings = evaluate_rules(RuleContext(config.name, snapshot, config.policy), rules)
    return snapshot, findings


async def discover_target(
    config: LabConfig,
    rules: tuple[ConformanceRule, ...] = DEFAULT_RULES,
) -> tuple[ContractSnapshot, tuple[Finding, ...]]:
    """Open the configured transport, discover its contract, and evaluate rules."""
    transport = config.transport
    if isinstance(transport, StdioTransportConfig):
        async with open_stdio_session(transport, config.policy) as session:
            return await _discover_with_session(session, config, rules)
    if isinstance(transport, HTTPTransportConfig):
        async with open_streamable_http_session(transport, config.policy) as session:
            return await _discover_with_session(session, config, rules)
    raise ConfigurationError("unsupported transport configuration")


def read_baseline(path: Path) -> ContractSnapshot:
    """Read and validate a stored contract baseline."""
    if not path.is_file():
        raise ConfigurationError(f"baseline file does not exist: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("baseline root must be an object")
        return ContractSnapshot.model_validate(value)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise EvidenceError(f"could not read baseline: {path}") from exc


def write_baseline(path: Path, snapshot: ContractSnapshot, payload: bytes) -> None:
    """Atomically write a canonical baseline snapshot."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_bytes(payload)
        temporary.replace(path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise EvidenceError(f"could not write baseline: {path}") from exc
