import json

from mcp_conformance_lab.domain.models import ContractSnapshot, Finding, FindingStatus, Severity
from mcp_conformance_lab.evidence.reports import (
    json_report_bytes,
    make_run_report,
    sarif_report_bytes,
    terminal_report,
)


def test_report_renderers_have_stable_machine_readable_shapes() -> None:
    snapshot = ContractSnapshot(protocol_version="2025-06-18", capabilities={})
    finding = Finding(
        finding_id="finding-1",
        rule_id="MCP-TEST-001",
        severity=Severity.INFO,
        status=FindingStatus.PASSED,
        title="Pass",
        message="Everything is fine",
        target="fixture",
    )
    report = make_run_report("fixture", snapshot, (finding,))

    json_payload = json.loads(json_report_bytes(report))
    sarif_payload = json.loads(sarif_report_bytes(report))

    assert json_payload["target"] == "fixture"
    assert sarif_payload["version"] == "2.1.0"
    assert sarif_payload["runs"][0]["results"][0]["ruleId"] == "MCP-TEST-001"
    assert "Contract digest" in terminal_report(report)
