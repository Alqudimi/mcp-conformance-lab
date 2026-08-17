from mcp_conformance_lab.application.compare import compare_snapshots
from mcp_conformance_lab.application.snapshot import snapshot_digest
from mcp_conformance_lab.domain.models import (
    ContractSnapshot,
    PromptContract,
    ResourceContract,
    ServerInfo,
    ToolContract,
)
from mcp_conformance_lab.domain.policies import ExecutionPolicy
from mcp_conformance_lab.rules.builtin import evaluate_rules
from mcp_conformance_lab.rules.protocol import RuleContext


def make_snapshot(*, duplicate: bool = False, changed: bool = False) -> ContractSnapshot:
    names = ("echo", "echo") if duplicate else ("echo",)
    return ContractSnapshot(
        protocol_version="2025-06-18",
        server_info=ServerInfo(name="fixture", version="1.0.0"),
        capabilities={"tools": {}, "prompts": {}},
        tools=tuple(
            ToolContract(
                name=name,
                description="Echo text",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            )
            for name in names
        ),
        prompts=(PromptContract(name="greet", description="Greeting"),),
    ).model_copy(
        update={"server_info": ServerInfo(name="fixture", version="2.0.0" if changed else "1.0.0")}
    )


def test_rules_pass_for_valid_snapshot() -> None:
    findings = evaluate_rules(RuleContext("fixture", make_snapshot(), ExecutionPolicy()))

    assert all(finding.status.value == "passed" for finding in findings)


def test_duplicate_identifier_rule_fails() -> None:
    findings = evaluate_rules(
        RuleContext("fixture", make_snapshot(duplicate=True), ExecutionPolicy())
    )

    duplicate = next(finding for finding in findings if finding.rule_id == "MCP-CONTRACT-001")
    assert duplicate.status.value == "failed"
    assert duplicate.severity.value == "high"


def test_snapshot_digest_changes_with_contract() -> None:
    assert snapshot_digest(make_snapshot()) != snapshot_digest(make_snapshot(changed=True))


def test_baseline_comparison_reports_changed_contract() -> None:
    findings = compare_snapshots(make_snapshot(changed=True), make_snapshot())

    assert any(finding.rule_id == "MCP-BASELINE-DIGEST-CHANGED" for finding in findings)
    assert any(finding.rule_id == "MCP-BASELINE-TOOL-CHANGED" for finding in findings) is False


def make_snapshot_over_limit(limit: int) -> ContractSnapshot:
    """Build a snapshot whose tool collection exceeds ``max_items`` by one."""
    return ContractSnapshot(
        protocol_version="2025-06-18",
        server_info=ServerInfo(name="fixture", version="1.0.0"),
        capabilities={"tools": {}},
        tools=tuple(
            ToolContract(
                name=f"tool-{index}",
                description="Echo text",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            )
            for index in range(limit + 1)
        ),
    )


def test_size_limits_rule_passes_under_limit() -> None:
    findings = evaluate_rules(
        RuleContext("fixture", make_snapshot(), ExecutionPolicy(max_items=10)),
    )

    size_limits = next(finding for finding in findings if finding.rule_id == "MCP-CONTRACT-004")
    assert size_limits.status.value == "passed"
    assert size_limits.severity.value == "info"


def test_size_limits_rule_fails_when_tools_exceed_limit() -> None:
    findings = evaluate_rules(
        RuleContext("fixture", make_snapshot_over_limit(limit=2), ExecutionPolicy(max_items=2)),
    )

    size_limits = next(finding for finding in findings if finding.rule_id == "MCP-CONTRACT-004")
    assert size_limits.status.value == "failed"
    assert size_limits.severity.value == "high"
    assert "tools (3/2)" in size_limits.message
    assert "Reduce advertised tools" in (size_limits.remediation or "")


def test_size_limits_rule_fails_when_resources_exceed_limit() -> None:
    snapshot = make_snapshot_over_limit(limit=1).model_copy(
        update={
            "tools": (),
            "capabilities": {"resources": {}},
            "resources": tuple(
                ResourceContract(uri=f"doc://{index}", name=f"doc-{index}") for index in range(3)
            ),
        },
    )
    findings = evaluate_rules(
        RuleContext("fixture", snapshot, ExecutionPolicy(max_items=2)),
    )

    size_limits = next(finding for finding in findings if finding.rule_id == "MCP-CONTRACT-004")
    assert size_limits.status.value == "failed"
    assert "resources (3/2)" in size_limits.message


def test_size_limits_rule_fails_when_prompts_exceed_limit() -> None:
    snapshot = make_snapshot_over_limit(limit=1).model_copy(
        update={
            "tools": (),
            "capabilities": {"prompts": {}},
            "prompts": tuple(PromptContract(name=f"prompt-{index}") for index in range(3)),
        },
    )
    findings = evaluate_rules(
        RuleContext("fixture", snapshot, ExecutionPolicy(max_items=2)),
    )

    size_limits = next(finding for finding in findings if finding.rule_id == "MCP-CONTRACT-004")
    assert size_limits.status.value == "failed"
    assert "prompts (3/2)" in size_limits.message


def test_size_limits_rule_respects_default_policy_limit() -> None:
    findings = evaluate_rules(
        RuleContext("fixture", make_snapshot_over_limit(limit=1000), ExecutionPolicy()),
    )

    size_limits = next(finding for finding in findings if finding.rule_id == "MCP-CONTRACT-004")
    assert size_limits.status.value == "failed"
