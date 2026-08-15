"""Baseline comparison for MCP contract snapshots."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..domain.models import ContractSnapshot, Finding, FindingStatus, Severity
from .snapshot import canonical_snapshot_payload, snapshot_digest


def _finding(
    rule_id: str,
    severity: Severity,
    status: FindingStatus,
    title: str,
    message: str,
) -> Finding:
    """Create a baseline finding with a stable identifier."""
    return Finding(
        finding_id=f"{rule_id}:{severity}:{status}",
        rule_id=rule_id,
        severity=severity,
        status=status,
        title=title,
        message=message,
        target="contract-baseline",
    )


def _compare_collection(
    label: str,
    current: list[dict[str, Any]],
    baseline: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
) -> list[Finding]:
    """Compare one named contract collection."""
    findings: list[Finding] = []
    current_by_key = {key(item): item for item in current}
    baseline_by_key = {key(item): item for item in baseline}
    for item_key in sorted(set(baseline_by_key) - set(current_by_key)):
        findings.append(
            _finding(
                f"MCP-BASELINE-{label.upper()}-REMOVED",
                Severity.HIGH,
                FindingStatus.FAILED,
                f"{label} contract removed",
                f"The baseline {label} '{item_key}' is no longer advertised.",
            )
        )
    for item_key in sorted(set(current_by_key) - set(baseline_by_key)):
        findings.append(
            _finding(
                f"MCP-BASELINE-{label.upper()}-ADDED",
                Severity.LOW,
                FindingStatus.FAILED,
                f"{label} contract added",
                f"The current contract advertises new {label} '{item_key}'.",
            )
        )
    for item_key in sorted(set(current_by_key) & set(baseline_by_key)):
        if current_by_key[item_key] != baseline_by_key[item_key]:
            findings.append(
                _finding(
                    f"MCP-BASELINE-{label.upper()}-CHANGED",
                    Severity.MEDIUM,
                    FindingStatus.FAILED,
                    f"{label} contract changed",
                    f"The contract for {label} '{item_key}' changed from the baseline.",
                )
            )
    return findings


def compare_snapshots(
    current: ContractSnapshot,
    baseline: ContractSnapshot,
) -> tuple[Finding, ...]:
    """Compare normalized snapshots and return deterministic findings."""
    current_payload = canonical_snapshot_payload(current)
    baseline_payload = canonical_snapshot_payload(baseline)
    if snapshot_digest(current) == snapshot_digest(baseline):
        return (
            _finding(
                "MCP-BASELINE-UNCHANGED",
                Severity.INFO,
                FindingStatus.PASSED,
                "Contract matches baseline",
                "The normalized MCP contract digest is identical to the baseline.",
            ),
        )

    findings: list[Finding] = [
        _finding(
            "MCP-BASELINE-DIGEST-CHANGED",
            Severity.MEDIUM,
            FindingStatus.FAILED,
            "Contract digest changed",
            "The normalized MCP contract differs from the stored baseline.",
        )
    ]
    findings.extend(
        _compare_collection(
            "tool",
            current_payload["tools"],
            baseline_payload["tools"],
            lambda item: item["name"],
        )
    )
    findings.extend(
        _compare_collection(
            "resource",
            current_payload["resources"],
            baseline_payload["resources"],
            lambda item: item["uri"],
        )
    )
    findings.extend(
        _compare_collection(
            "prompt",
            current_payload["prompts"],
            baseline_payload["prompts"],
            lambda item: item["name"],
        )
    )
    if current_payload.get("capabilities") != baseline_payload.get("capabilities"):
        findings.append(
            _finding(
                "MCP-BASELINE-CAPABILITIES-CHANGED",
                Severity.HIGH,
                FindingStatus.FAILED,
                "Server capabilities changed",
                "The server capability declaration differs from the baseline.",
            )
        )
    return tuple(findings)
