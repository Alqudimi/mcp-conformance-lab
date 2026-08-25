import pytest
from typer.testing import CliRunner

from mcp_conformance_lab.cli import _failure_exit_code, app
from mcp_conformance_lab.domain.errors import (
    ConfigurationError,
    ConformanceError,
    EvidenceError,
    ProtocolError,
    TransportError,
)

runner = CliRunner()


def test_help_lists_doctor_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "doctor" in result.stdout
    assert "conformance" in result.stdout.lower()


def test_doctor_reports_installation() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "is installed" in result.stdout


def test_version_option_reports_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "mcp-conformance 0.1.1" in result.stdout


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (ConfigurationError("invalid configuration"), 2),
        (TransportError("target unavailable"), 4),
        (ProtocolError("invalid MCP response"), 4),
        (EvidenceError("could not write evidence"), 5),
    ],
)
def test_failure_exit_codes_follow_documented_contract(
    error: ConformanceError, expected_code: int
) -> None:
    assert _failure_exit_code(error) == expected_code
