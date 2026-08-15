from pathlib import Path

from mcp_conformance_lab.domain.models import ContractSnapshot, Finding, FindingStatus, Severity
from mcp_conformance_lab.evidence.bundle import EvidenceBundleWriter, verify_bundle


def make_snapshot() -> ContractSnapshot:
    return ContractSnapshot(protocol_version="2025-06-18", capabilities={})


def make_finding() -> Finding:
    return Finding(
        finding_id="finding-1",
        rule_id="MCP-TEST-001",
        severity=Severity.INFO,
        status=FindingStatus.PASSED,
        title="Pass",
        message="Everything is fine",
        target="fixture",
    )


def test_evidence_bundle_is_written_and_verified(tmp_path: Path) -> None:
    bundle = EvidenceBundleWriter().write(
        tmp_path / "runs",
        "fixture",
        make_snapshot(),
        (make_finding(),),
    )

    assert (bundle / "contract.json").is_file()
    assert (bundle / "results.json").is_file()
    assert verify_bundle(bundle) is True


def test_evidence_verification_detects_tampering(tmp_path: Path) -> None:
    bundle = EvidenceBundleWriter().write(
        tmp_path / "runs",
        "fixture",
        make_snapshot(),
        (make_finding(),),
    )
    (bundle / "results.json").write_text("tampered", encoding="utf-8")

    assert verify_bundle(bundle) is False
