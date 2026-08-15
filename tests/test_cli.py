from typer.testing import CliRunner

from mcp_conformance_lab.cli import app

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
    assert "mcp-conformance 0.1.0" in result.stdout
