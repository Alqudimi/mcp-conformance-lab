"""Command-line entry point for MCP Conformance Lab."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, NoReturn

import anyio
import typer

from .application.service import (
    compare_with_baseline,
    discover_target,
    write_baseline,
)
from .application.snapshot import snapshot_bytes
from .config.loader import load_config
from .config.schema import LabConfig
from .domain.errors import ConformanceError
from .domain.models import ContractSnapshot, Finding, RunReport
from .domain.policies import exit_code_for_findings
from .evidence.bundle import EvidenceBundleWriter, verify_bundle
from .evidence.reports import (
    json_report_bytes,
    make_run_report,
    sarif_report_bytes,
    terminal_report,
)
from .version import __version__

app = typer.Typer(
    name="mcp-conformance",
    help="Deterministic conformance and regression testing for MCP servers.",
    no_args_is_help=True,
    add_completion=False,
)


OutputFormat = Literal["terminal", "json", "sarif"]


def version_callback(value: bool) -> None:
    """Print the version and exit before command validation."""
    if value:
        typer.echo(f"mcp-conformance {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the installed package version.",
    ),
) -> None:
    """Inspect MCP server contracts without sending data to external analyzers."""


def _fail(error: ConformanceError) -> NoReturn:
    """Render one expected failure without exposing implementation details."""
    typer.echo(f"Error [{error.code}]: {error.message}", err=True)
    raise typer.Exit(code=4)


def _load(path: Path) -> LabConfig:
    """Load a config and render expected errors consistently."""
    try:
        return load_config(path)
    except ConformanceError as error:
        _fail(error)


def _collect_findings(
    config_path: Path,
) -> tuple[LabConfig, ContractSnapshot, tuple[Finding, ...]]:
    """Discover a target and add baseline findings when configured."""
    config = _load(config_path)
    try:
        snapshot, findings = anyio.run(discover_target, config)
        findings = findings + compare_with_baseline(config.name, snapshot, config.baseline)
        return config, snapshot, findings
    except ConformanceError as error:
        _fail(error)


def _render(report: RunReport, output_format: OutputFormat) -> None:
    """Print a report in the requested format."""
    if output_format == "json":
        typer.echo(json_report_bytes(report).decode("utf-8"))
    elif output_format == "sarif":
        typer.echo(sarif_report_bytes(report).decode("utf-8"))
    else:
        typer.echo(terminal_report(report), nl=False)


@app.command()
def doctor() -> None:
    """Check that the local installation is usable."""
    typer.echo(f"mcp-conformance {__version__} is installed")


@app.command()
def discover(
    config: Path = typer.Option(..., "--config", exists=True, readable=True),
    output_format: OutputFormat = typer.Option("terminal", "--format"),
) -> None:
    """Discover an MCP contract and run read-only snapshot rules."""
    config_model, snapshot, findings = _collect_findings(config)
    report = make_run_report(config_model.name, snapshot, findings)
    _render(report, output_format)
    raise typer.Exit(code=exit_code_for_findings(findings, config_model.policy.fail_on))


@app.command()
def snapshot(
    config: Path = typer.Option(..., "--config", exists=True, readable=True),
    output: Path = typer.Option(..., "--output"),
) -> None:
    """Write the canonical contract snapshot to a JSON file."""
    config_model = _load(config)
    try:
        contract, _findings = anyio.run(discover_target, config_model)
        write_baseline(output, contract, snapshot_bytes(contract))
        typer.echo(f"Snapshot written: {output.expanduser().resolve()}")
    except ConformanceError as error:
        _fail(error)


@app.command()
def baseline(
    config: Path = typer.Option(..., "--config", exists=True, readable=True),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    """Create or replace a baseline snapshot for a target."""
    config_model = _load(config)
    destination = output or config_model.baseline
    if destination is None:
        destination = config.parent / ".mcp-lab" / "baseline.json"
    try:
        contract, _findings = anyio.run(discover_target, config_model)
        write_baseline(destination, contract, snapshot_bytes(contract))
        typer.echo(f"Baseline written: {destination.expanduser().resolve()}")
    except ConformanceError as error:
        _fail(error)


@app.command()
def check(
    config: Path = typer.Option(..., "--config", exists=True, readable=True),
    output_format: OutputFormat = typer.Option("terminal", "--format"),
) -> None:
    """Run conformance rules, compare an optional baseline, and write evidence."""
    config_model, snapshot, findings = _collect_findings(config)
    report = make_run_report(config_model.name, snapshot, findings)
    try:
        bundle = EvidenceBundleWriter().write(
            config_model.reports.directory,
            config_model.name,
            snapshot,
            findings,
        )
    except ConformanceError as error:
        _fail(error)
    _render(report, output_format)
    typer.echo(f"Evidence: {bundle}", err=True)
    raise typer.Exit(code=exit_code_for_findings(findings, config_model.policy.fail_on))


@app.command()
def verify(bundle: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
    """Verify the hashes in an evidence bundle."""
    try:
        valid = verify_bundle(bundle)
    except ConformanceError as error:
        _fail(error)
    if not valid:
        typer.echo("Evidence verification failed", err=True)
        raise typer.Exit(code=3)
    typer.echo("Evidence verification passed")


def main() -> None:
    """Run the Typer application."""
    app()


if __name__ == "__main__":
    main()
