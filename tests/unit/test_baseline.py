from pathlib import Path

from mcp_conformance_lab.application.service import compare_with_baseline
from mcp_conformance_lab.domain.models import ContractSnapshot, ServerInfo


def make_snapshot() -> ContractSnapshot:
    return ContractSnapshot(
        protocol_version="2025-06-18",
        server_info=ServerInfo(name="fixture", version="1.0.0"),
        capabilities={},
    )


def test_configured_missing_baseline_is_reported(tmp_path: Path) -> None:
    findings = compare_with_baseline("fixture", make_snapshot(), tmp_path / "missing.json")

    assert len(findings) == 1
    assert findings[0].rule_id == "MCP-BASELINE-MISSING"
    assert findings[0].status.value == "error"
    assert findings[0].severity.value == "high"


def test_directory_baseline_is_unavailable(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    baseline.mkdir()

    findings = compare_with_baseline("fixture", make_snapshot(), baseline)

    assert len(findings) == 1
    assert findings[0].rule_id == "MCP-BASELINE-UNAVAILABLE"
    assert findings[0].status.value == "error"


def test_invalid_baseline_is_reported(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text("{not-json", encoding="utf-8")

    findings = compare_with_baseline("fixture", make_snapshot(), baseline)

    assert len(findings) == 1
    assert findings[0].rule_id == "MCP-BASELINE-INVALID"
    assert findings[0].status.value == "error"


def test_valid_baseline_is_compared(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(make_snapshot().model_dump_json(), encoding="utf-8")

    findings = compare_with_baseline("fixture", make_snapshot(), baseline)

    assert any(finding.rule_id == "MCP-BASELINE-UNCHANGED" for finding in findings)
    assert all(finding.status.value == "passed" for finding in findings)
