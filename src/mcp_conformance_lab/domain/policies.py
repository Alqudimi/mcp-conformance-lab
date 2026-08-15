"""Safe execution policies and deterministic exit-code mapping."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import Finding, FindingStatus, Severity


class ExecutionPolicy(BaseModel):
    """Boundaries applied to every connection and test case."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    connect_timeout_seconds: float = Field(default=10.0, gt=0, le=300)
    case_timeout_seconds: float = Field(default=5.0, gt=0, le=300)
    max_output_bytes: int = Field(default=1_048_576, gt=0, le=100_000_000)
    max_items: int = Field(default=1_000, gt=0, le=100_000)
    allow_exec: bool = False
    inherit_environment: bool = False
    allowed_working_root: Path | None = None
    fail_on: Severity = Severity.HIGH

    @field_validator("allowed_working_root")
    @classmethod
    def normalize_working_root(cls, value: Path | None) -> Path | None:
        """Resolve an optional working-root boundary once at configuration time."""
        return value.expanduser().resolve() if value is not None else None

    def validate_working_directory(self, cwd: Path) -> Path:
        """Return a resolved cwd only when it remains within the configured root."""
        resolved = cwd.expanduser().resolve()
        if self.allowed_working_root is None:
            return resolved
        try:
            resolved.relative_to(self.allowed_working_root)
        except ValueError as exc:
            raise ValueError(f"working directory escapes allowed root: {resolved}") from exc
        return resolved


_SEVERITY_TO_EXIT = {
    Severity.INFO: 0,
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3,
}


def exit_code_for_findings(findings: tuple[Finding, ...], fail_on: Severity) -> int:
    """Map actionable findings to a stable process exit code."""
    for finding in findings:
        if (
            finding.status in {FindingStatus.ERROR, FindingStatus.FAILED}
            and finding.severity.rank >= fail_on.rank
        ):
            return _SEVERITY_TO_EXIT[finding.severity]
    return 0
