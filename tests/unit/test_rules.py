from mcp_conformance_lab.application.compare import compare_snapshots
from mcp_conformance_lab.application.snapshot import snapshot_digest
from mcp_conformance_lab.domain.models import (
    ContractSnapshot,
    PromptContract,
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
