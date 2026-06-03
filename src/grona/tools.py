"""Safe mock tool adapter prototype for Grona."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from .feedback import Metadata
from .safety import (
    ACTION_TYPES,
    RISK_LEVELS,
    PolicyDecision,
    SafetyPolicy,
    ToolAction,
    create_default_safety_policy,
)


@dataclass(frozen=True)
class ToolSpec:
    """Description of a future tool capability."""

    name: str
    description: str
    action_type: str = "unknown"
    risk_level: str = "low"
    read_only: bool = True
    input_schema: Metadata = field(default_factory=dict)
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("tool spec name cannot be empty")
        if self.action_type not in ACTION_TYPES:
            raise ValueError(f"unsupported action_type: {self.action_type}")
        if self.risk_level not in RISK_LEVELS:
            raise ValueError(f"unsupported risk_level: {self.risk_level}")


@dataclass(frozen=True)
class ToolRequest:
    """A requested call to a registered tool adapter."""

    tool_name: str
    task: str
    inputs: Metadata = field(default_factory=dict)
    requested_by: str = "unknown"
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        tool_name: str,
        task: str,
        inputs: Mapping[str, object] | None = None,
        requested_by: str = "unknown",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "tool_name", tool_name)
        object.__setattr__(self, "task", task)
        object.__setattr__(self, "inputs", dict(inputs or {}))
        object.__setattr__(self, "requested_by", requested_by)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not tool_name:
            raise ValueError("tool request tool_name cannot be empty")
        if not task:
            raise ValueError("tool request task cannot be empty")


@dataclass(frozen=True)
class ToolResult:
    """Structured result from a mock tool adapter."""

    tool_name: str
    success: bool
    output: str
    details: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        tool_name: str,
        success: bool,
        output: str,
        details: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "tool_name", tool_name)
        object.__setattr__(self, "success", success)
        object.__setattr__(self, "output", output)
        object.__setattr__(self, "details", tuple(details))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not tool_name:
            raise ValueError("tool result tool_name cannot be empty")
        if not output:
            raise ValueError("tool result output cannot be empty")

    def to_text(self) -> str:
        """Format a tool result for humans."""
        status = "success" if self.success else "blocked"
        lines = [f"Tool: {self.tool_name}", f"Status: {status}", f"Output: {self.output}"]
        if self.details:
            lines.append("Details:")
            lines.extend(f"- {detail}" for detail in self.details)
        return "\n".join(lines)


class ToolAdapter(Protocol):
    """Minimal contract for mock and future tool adapters."""

    spec: ToolSpec

    def plan_action(self, request: ToolRequest) -> ToolAction:
        """Plan the tool action for safety evaluation."""

    def execute(self, request: ToolRequest) -> ToolResult:
        """Execute or simulate a tool request."""


@dataclass(frozen=True)
class MockToolAdapter:
    """Deterministic mock tool adapter. It performs no external work."""

    spec: ToolSpec
    output: str
    details: tuple[str, ...] = ()

    def __init__(
        self,
        spec: ToolSpec,
        output: str,
        details: Sequence[str] = (),
    ) -> None:
        object.__setattr__(self, "spec", spec)
        object.__setattr__(self, "output", output)
        object.__setattr__(self, "details", tuple(details))

    def plan_action(self, request: ToolRequest) -> ToolAction:
        """Return the deterministic action plan for this mock tool."""
        return ToolAction(
            name=self.spec.name,
            description=self.spec.description,
            command=None,
            action_type=self.spec.action_type,
            risk_level=self.spec.risk_level,
            read_only=self.spec.read_only,
            requires_confirmation=self.spec.risk_level in {"medium", "high"},
            metadata={
                "tool_name": self.spec.name,
                "requested_by": request.requested_by,
                **self.spec.metadata,
            },
        )

    def execute(self, request: ToolRequest) -> ToolResult:
        """Return a deterministic mock result without touching external systems."""
        return ToolResult(
            tool_name=self.spec.name,
            success=True,
            output=self.output,
            details=(
                *self.details,
                f"Requested by: {request.requested_by}",
                "Mock tool only; no filesystem, network, subprocess, or API access.",
            ),
            metadata={
                "tool_adapter": "mock",
                "action_type": self.spec.action_type,
                "risk_level": self.spec.risk_level,
                "read_only": self.spec.read_only,
                "requested_by": request.requested_by,
            },
        )


class ToolRegistry:
    """Registry for tool adapters."""

    def __init__(self, adapters: Iterable[ToolAdapter] = ()) -> None:
        self._adapters: dict[str, ToolAdapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: ToolAdapter) -> None:
        """Register a tool adapter by tool name."""
        self._adapters[adapter.spec.name] = adapter

    def get(self, tool_name: str) -> ToolAdapter | None:
        """Return a tool adapter by name, if registered."""
        return self._adapters.get(tool_name)

    def list(self) -> tuple[ToolAdapter, ...]:
        """Return tools in deterministic name order."""
        return tuple(self._adapters[name] for name in sorted(self._adapters))

    def find_by_action_type(self, action_type: str) -> tuple[ToolAdapter, ...]:
        """Return tools matching an action type."""
        return tuple(tool for tool in self.list() if tool.spec.action_type == action_type)

    def find_by_metadata(self, key: str, value: object) -> tuple[ToolAdapter, ...]:
        """Return tools matching a simple metadata key/value."""
        return tuple(tool for tool in self.list() if tool.spec.metadata.get(key) == value)


class SafeToolRunner:
    """Policy-aware coordinator for mock tool adapters."""

    def __init__(
        self,
        registry: ToolRegistry,
        policy: SafetyPolicy | None = None,
        force_dry_run: bool = False,
    ) -> None:
        self.registry = registry
        self.policy = policy or create_default_safety_policy(dry_run=force_dry_run)
        self.force_dry_run = force_dry_run

    def run(self, request: ToolRequest) -> ToolResult:
        """Plan, evaluate, and run or dry-run a mock tool request."""
        adapter = self.registry.get(request.tool_name)
        if adapter is None:
            return ToolResult(
                tool_name=request.tool_name,
                success=False,
                output=f"No tool adapter registered for {request.tool_name}.",
                details=("The tool request was not executed.",),
                metadata={"tool_missing": True, "requested_by": request.requested_by},
            )

        action = adapter.plan_action(request)
        policy = self.policy.with_dry_run(True) if self.force_dry_run else self.policy
        decision = policy.evaluate(action)
        if not decision.allowed:
            return policy_tool_result(request, decision, "Safety policy blocked mock tool execution.")
        if decision.dry_run:
            return policy_tool_result(request, decision, "Safety policy returned a dry-run tool plan.")

        result = adapter.execute(request)
        return ToolResult(
            tool_name=result.tool_name,
            success=result.success,
            output=result.output,
            details=(*result.details, decision.to_text()),
            metadata={
                **result.metadata,
                **tool_policy_metadata(decision),
                "tool_action_name": action.name,
            },
        )


def policy_tool_result(
    request: ToolRequest,
    decision: PolicyDecision,
    output: str,
) -> ToolResult:
    """Create a result for blocked or dry-run tool policy outcomes."""
    return ToolResult(
        tool_name=request.tool_name,
        success=decision.allowed,
        output=output,
        details=(decision.to_text(),),
        metadata={
            **tool_policy_metadata(decision),
            "requested_by": request.requested_by,
        },
    )


def tool_policy_metadata(decision: PolicyDecision) -> Metadata:
    """Convert a policy decision into tool result metadata."""
    return {
        "policy_allowed": decision.allowed,
        "policy_dry_run": decision.dry_run,
        "policy_risk_level": decision.risk_level,
        "policy_required_confirmation": decision.required_confirmation,
        "policy_blocked_by": list(decision.blocked_by),
    }


def tool_request_for_module(module_name: str, task: str) -> ToolRequest | None:
    """Return a deterministic demo tool request for a selected module."""
    mapping = {
        "code-assistant": "mock_code_inspector",
        "document-search": "mock_document_search",
        "media-video-tool": "mock_media_metadata_reader",
        "cybersecurity-scanner": "mock_security_checklist",
        "automotive-diagnostics": "mock_automotive_checklist",
    }
    tool_name = mapping.get(module_name)
    if tool_name is None:
        return None
    return ToolRequest(
        tool_name=tool_name,
        task=task,
        inputs={"task": task, "module_name": module_name},
        requested_by=module_name,
        metadata={"demo_tool_request": True},
    )


def create_default_tool_registry() -> ToolRegistry:
    """Create deterministic mock tools for examples and tests."""
    return ToolRegistry(
        (
            MockToolAdapter(
                ToolSpec(
                    name="mock_code_inspector",
                    description="Mock read-only code structure inspection.",
                    action_type="read_file",
                    risk_level="low",
                    read_only=True,
                    input_schema={"task": "str", "module_name": "str"},
                    metadata={"domain": "code"},
                ),
                output="Mock code inspector found test, lint, and structure review checkpoints.",
                details=("Suggested checks: tests, linting, imports, error paths.",),
            ),
            MockToolAdapter(
                ToolSpec(
                    name="mock_document_search",
                    description="Mock read-only document search.",
                    action_type="read_file",
                    risk_level="low",
                    read_only=True,
                    input_schema={"task": "str", "module_name": "str"},
                    metadata={"domain": "document"},
                ),
                output="Mock document search prepared query terms and citation placeholders.",
                details=("Suggested checks: source scope, query terms, citations.",),
            ),
            MockToolAdapter(
                ToolSpec(
                    name="mock_media_metadata_reader",
                    description="Mock read-only media metadata inspection.",
                    action_type="read_file",
                    risk_level="low",
                    read_only=True,
                    input_schema={"task": "str", "module_name": "str"},
                    metadata={"domain": "media"},
                ),
                output="Mock media metadata reader prepared codec and export checkpoints.",
                details=("Suggested checks: codec, duration, audio, metadata, export target.",),
            ),
            MockToolAdapter(
                ToolSpec(
                    name="mock_security_checklist",
                    description="Mock security checklist planning.",
                    action_type="network_request",
                    risk_level="medium",
                    read_only=True,
                    input_schema={"task": "str", "module_name": "str"},
                    metadata={"domain": "cybersecurity"},
                ),
                output="Mock security checklist prepared review categories.",
                details=("Suggested checks: secrets, auth, ports, logs, permissions.",),
            ),
            MockToolAdapter(
                ToolSpec(
                    name="mock_automotive_checklist",
                    description="Mock automotive checklist planning.",
                    action_type="read_file",
                    risk_level="low",
                    read_only=True,
                    input_schema={"task": "str", "module_name": "str"},
                    metadata={"domain": "automotive"},
                ),
                output="Mock automotive checklist prepared diagnostic checkpoints.",
                details=("Suggested checks: coolant, thermostat, radiator, fan, leaks.",),
            ),
        )
    )
