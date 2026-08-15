"""Report renderers for terminal and CI integrations."""

from __future__ import annotations

from typing import Any

from ..application.snapshot import snapshot_digest
from ..domain.canonical import canonical_bytes
from ..domain.models import ContractSnapshot, Finding, FindingStatus, RunReport, TestResult


def make_run_report(
    target: str,
    snapshot: ContractSnapshot,
    findings: tuple[Finding, ...],
) -> RunReport:
    """Build a typed run report with deterministic rule ordering."""
    results = tuple(
        TestResult(finding=finding, duration_ms=0.0)
        for finding in sorted(findings, key=lambda item: item.finding_id)
    )
    return RunReport(
        target=target,
        contract_digest=snapshot_digest(snapshot),
        results=results,
    )


def json_report_bytes(report: RunReport) -> bytes:
    """Render the report as canonical JSON bytes."""
    return canonical_bytes(report)


def _sarif_level(finding: Finding) -> str:
    """Map project severity to SARIF result level."""
    if finding.status is FindingStatus.PASSED:
        return "none"
    if finding.severity.rank >= 3:
        return "error"
    if finding.severity.rank == 2:
        return "warning"
    return "note"


def sarif_payload(report: RunReport) -> dict[str, Any]:
    """Build a SARIF 2.1.0 payload from a typed report."""
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for item in report.results:
        finding = item.finding
        rules.setdefault(
            finding.rule_id,
            {
                "id": finding.rule_id,
                "name": finding.title,
                "shortDescription": {"text": finding.title},
                "help": {
                    "text": finding.remediation or "Review the MCP contract and rerun the rule."
                },
            },
        )
        results.append(
            {
                "ruleId": finding.rule_id,
                "level": _sarif_level(finding),
                "message": {"text": finding.message},
                "properties": {
                    "findingId": finding.finding_id,
                    "status": finding.status.value,
                    "severity": finding.severity.value,
                    "target": finding.target,
                },
            }
        )
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "MCP Conformance Lab",
                        "version": "0.1.0",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }


def sarif_report_bytes(report: RunReport) -> bytes:
    """Render SARIF as canonical JSON bytes."""
    return canonical_bytes(sarif_payload(report))


def terminal_report(report: RunReport) -> str:
    """Render a concise, actionable terminal summary."""
    lines = [
        f"Target: {report.target}",
        f"Contract digest: {report.contract_digest}",
        "",
    ]
    for item in report.results:
        finding = item.finding
        lines.append(
            f"[{finding.status.value.upper()}] {finding.rule_id} "
            f"({finding.severity.value}) — {finding.title}: {finding.message}"
        )
    return "\n".join(lines) + "\n"
