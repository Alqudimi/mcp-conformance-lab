"""Immutable domain models for MCP contracts and test results."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    """Actionability level of a finding."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        """Return a comparable severity rank."""
        return {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }[self]


class FindingStatus(StrEnum):
    """Outcome of one conformance rule."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TransportKind(StrEnum):
    """Supported MCP transport families."""

    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable_http"


class EvidenceRef(BaseModel):
    """Pointer to a bounded artifact inside an evidence bundle."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    description: str = Field(min_length=1)


class Finding(BaseModel):
    """Machine-readable result with actionable context."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    finding_id: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    severity: Severity
    status: FindingStatus
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)
    target: str = Field(min_length=1)
    evidence_refs: tuple[EvidenceRef, ...] = ()
    remediation: str | None = None


class ToolContract(BaseModel):
    """Public contract for an MCP tool."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    description: str | None = None
    input_schema: dict[str, object] = Field(default_factory=dict)
    output_schema: dict[str, object] | None = None
    annotations: dict[str, object] = Field(default_factory=dict)


class ResourceContract(BaseModel):
    """Public contract for an MCP resource."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    uri: str = Field(min_length=1)
    name: str | None = None
    description: str | None = None
    mime_type: str | None = None


class PromptArgument(BaseModel):
    """Argument declaration for an MCP prompt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    description: str | None = None
    required: bool = False


class PromptContract(BaseModel):
    """Public contract for an MCP prompt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    description: str | None = None
    arguments: tuple[PromptArgument, ...] = ()


class ServerInfo(BaseModel):
    """Server identity returned by MCP initialization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str | None = None
    version: str | None = None
    title: str | None = None


class ContractSnapshot(BaseModel):
    """Canonicalizable MCP server contract snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = Field(default=1, ge=1)
    protocol_version: str = Field(min_length=1)
    server_info: ServerInfo = Field(default_factory=ServerInfo)
    capabilities: dict[str, object] = Field(default_factory=dict)
    tools: tuple[ToolContract, ...] = ()
    resources: tuple[ResourceContract, ...] = ()
    prompts: tuple[PromptContract, ...] = ()


class TestResult(BaseModel):
    """One rule outcome included in a run report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    finding: Finding
    duration_ms: float = Field(ge=0)


class RunReport(BaseModel):
    """Complete in-memory report before evidence serialization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = Field(default=1, ge=1)
    target: str = Field(min_length=1)
    contract_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    results: tuple[TestResult, ...] = ()
