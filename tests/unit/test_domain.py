from pathlib import Path

import pytest

from mcp_conformance_lab.config.loader import load_config
from mcp_conformance_lab.domain.canonical import canonical_bytes, sha256_digest
from mcp_conformance_lab.domain.models import Finding, FindingStatus, Severity
from mcp_conformance_lab.domain.policies import ExecutionPolicy, exit_code_for_findings


def make_finding(severity: Severity, status: FindingStatus = FindingStatus.FAILED) -> Finding:
    return Finding(
        finding_id="finding-1",
        rule_id="MCP-CONTRACT-001",
        severity=severity,
        status=status,
        title="Test finding",
        message="A deterministic test finding",
        target="fixture",
    )


def test_canonical_bytes_are_independent_of_mapping_order() -> None:
    left = {"b": 2, "a": {"y": True, "x": 1}}
    right = {"a": {"x": 1, "y": True}, "b": 2}

    assert canonical_bytes(left) == canonical_bytes(right)
    assert sha256_digest(left) == sha256_digest(right)


def test_exit_code_respects_fail_threshold() -> None:
    findings = (make_finding(Severity.MEDIUM), make_finding(Severity.HIGH))

    assert exit_code_for_findings(findings, Severity.HIGH) == 2
    assert exit_code_for_findings(findings, Severity.CRITICAL) == 0


def test_low_findings_do_not_fail_default_threshold() -> None:
    assert exit_code_for_findings((make_finding(Severity.LOW),), Severity.HIGH) == 0


def test_working_directory_must_remain_inside_allowed_root(tmp_path: Path) -> None:
    policy = ExecutionPolicy(allowed_working_root=tmp_path)

    assert policy.validate_working_directory(tmp_path / "child") == (tmp_path / "child").resolve()
    with pytest.raises(ValueError, match="escapes allowed root"):
        policy.validate_working_directory(tmp_path.parent)


def test_config_loader_resolves_relative_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "mcp-lab.yaml"
    config_path.write_text(
        """
schema_version: 1
name: fixture
transport:
  kind: stdio
  command: python
  args: [fixture.py]
policy:
  allow_exec: true
reports:
  directory: runs
baseline: baseline.json
""".lstrip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.reports.directory == (tmp_path / "runs").resolve()
    assert config.baseline == (tmp_path / "baseline.json").resolve()
    assert config.transport.args == ("fixture.py",)


def test_config_loader_rejects_unknown_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        """
schema_version: 1
name: fixture
unknown: true
transport:
  kind: stdio
  command: python
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(Exception, match="validation failed"):
        load_config(config_path)
