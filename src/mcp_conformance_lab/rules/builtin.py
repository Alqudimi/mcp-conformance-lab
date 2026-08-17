"""Built-in deterministic contract rules."""

from __future__ import annotations

from collections import Counter

from jsonschema import SchemaError
from jsonschema.validators import validator_for

from ..domain.models import Finding, FindingStatus, Severity
from .protocol import ConformanceRule, RuleContext


def _result(
    rule_id: str,
    context: RuleContext,
    status: FindingStatus,
    severity: Severity,
    title: str,
    message: str,
    remediation: str | None = None,
) -> Finding:
    """Create a stable rule result."""
    return Finding(
        finding_id=f"{rule_id}:{context.target}",
        rule_id=rule_id,
        severity=severity,
        status=status,
        title=title,
        message=message,
        target=context.target,
        remediation=remediation,
    )


class UniqueIdentifiersRule:
    """Ensure every advertised MCP item has a unique identifier."""

    rule_id = "MCP-CONTRACT-001"

    def evaluate(self, context: RuleContext) -> Finding:
        """Detect duplicate tool, resource, or prompt identifiers."""
        duplicates: list[str] = []
        for label, identifiers in (
            ("tool", [item.name for item in context.snapshot.tools]),
            ("resource", [item.uri for item in context.snapshot.resources]),
            ("prompt", [item.name for item in context.snapshot.prompts]),
        ):
            duplicates.extend(
                f"{label}:{identifier}"
                for identifier, count in Counter(identifiers).items()
                if count > 1
            )
        if duplicates:
            return _result(
                self.rule_id,
                context,
                FindingStatus.FAILED,
                Severity.HIGH,
                "Duplicate MCP identifiers detected",
                "The server advertises duplicate identifiers: " + ", ".join(sorted(duplicates)),
                "Make every tool, resource, and prompt identifier unique.",
            )
        return _result(
            self.rule_id,
            context,
            FindingStatus.PASSED,
            Severity.INFO,
            "MCP identifiers are unique",
            "Tools, resources, and prompts have unique identifiers.",
        )


class ToolSchemaRule:
    """Validate tool input and output JSON Schemas without executing tools."""

    rule_id = "MCP-CONTRACT-002"

    @staticmethod
    def _valid_schema(schema: dict[str, object]) -> bool:
        """Return whether a schema is valid under its declared dialect."""
        try:
            validator = validator_for(schema)
            validator.check_schema(schema)
        except SchemaError:
            return False
        return True

    def evaluate(self, context: RuleContext) -> Finding:
        """Check that every advertised tool has valid schema objects."""
        invalid: list[str] = []
        for tool in context.snapshot.tools:
            if not self._valid_schema(tool.input_schema):
                invalid.append(f"{tool.name}:input")
            if tool.output_schema is not None and not self._valid_schema(tool.output_schema):
                invalid.append(f"{tool.name}:output")
        if invalid:
            return _result(
                self.rule_id,
                context,
                FindingStatus.FAILED,
                Severity.HIGH,
                "Invalid tool JSON Schema",
                "The following schemas are invalid: " + ", ".join(sorted(invalid)),
                "Publish a valid JSON Schema for every tool input and output.",
            )
        return _result(
            self.rule_id,
            context,
            FindingStatus.PASSED,
            Severity.INFO,
            "Tool schemas are valid",
            "All advertised tool schemas pass JSON Schema validation.",
        )


class CapabilityConsistencyRule:
    """Check that advertised collections are consistent with server capabilities."""

    rule_id = "MCP-CONTRACT-003"

    def evaluate(self, context: RuleContext) -> Finding:
        """Detect items present without their corresponding capability."""
        capability_names = context.snapshot.capabilities.keys()
        mismatches: list[str] = []
        if context.snapshot.tools and "tools" not in capability_names:
            mismatches.append("tools")
        if context.snapshot.resources and "resources" not in capability_names:
            mismatches.append("resources")
        if context.snapshot.prompts and "prompts" not in capability_names:
            mismatches.append("prompts")
        if mismatches:
            return _result(
                self.rule_id,
                context,
                FindingStatus.FAILED,
                Severity.MEDIUM,
                "Contract capability mismatch",
                "Items were listed without a matching server capability: " + ", ".join(mismatches),
                "Declare the capability before exposing its collection.",
            )
        return _result(
            self.rule_id,
            context,
            FindingStatus.PASSED,
            Severity.INFO,
            "Capabilities match advertised collections",
            "The snapshot collections are consistent with server capabilities.",
        )


class SizeLimitsRule:
    """Ensure advertised collections stay within the configured policy bounds.

    The execution policy declares ``max_items`` as a hard contract ceiling, but
    without this rule a server advertising more tools, resources, or prompts
    than the client policy permits would silently exceed the limit. This rule
    closes that gap by failing loudly when any collection exceeds the limit.
    """

    rule_id = "MCP-CONTRACT-004"

    def evaluate(self, context: RuleContext) -> Finding:
        """Report when advertised collections exceed ``policy.max_items``."""
        limit = context.policy.max_items
        collections: tuple[tuple[str, int], ...] = (
            ("tools", len(context.snapshot.tools)),
            ("resources", len(context.snapshot.resources)),
            ("prompts", len(context.snapshot.prompts)),
        )
        exceeded = [f"{label} ({count}/{limit})" for label, count in collections if count > limit]
        if exceeded:
            return _result(
                self.rule_id,
                context,
                FindingStatus.FAILED,
                Severity.HIGH,
                "Advertised collection exceeds policy size limit",
                "The following collections exceed the configured limit: "
                + ", ".join(sorted(exceeded)),
                "Reduce advertised tools, resources, or prompts below the "
                f"configured limit of {limit} or raise policy.max_items.",
            )
        return _result(
            self.rule_id,
            context,
            FindingStatus.PASSED,
            Severity.INFO,
            "Advertised collections respect policy size limits",
            "All advertised tool, resource, and prompt collections are below "
            f"the configured limit of {limit}.",
        )


DEFAULT_RULES: tuple[ConformanceRule, ...] = (
    UniqueIdentifiersRule(),
    ToolSchemaRule(),
    CapabilityConsistencyRule(),
    SizeLimitsRule(),
)


def evaluate_rules(
    context: RuleContext,
    rules: tuple[ConformanceRule, ...] = DEFAULT_RULES,
) -> tuple[Finding, ...]:
    """Evaluate rules in declaration order."""
    return tuple(rule.evaluate(context) for rule in rules)
