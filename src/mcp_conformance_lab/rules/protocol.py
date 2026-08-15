"""Rule interfaces for deterministic MCP conformance checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..domain.models import ContractSnapshot, Finding
from ..domain.policies import ExecutionPolicy


@dataclass(frozen=True)
class RuleContext:
    """Immutable inputs available to one rule evaluation."""

    target: str
    snapshot: ContractSnapshot
    policy: ExecutionPolicy


class ConformanceRule(Protocol):
    """Synchronous rule contract for snapshot-level checks."""

    rule_id: str

    def evaluate(self, context: RuleContext) -> Finding:
        """Return one pass/fail finding for the rule."""
        ...
