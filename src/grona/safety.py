"""Tool safety policy and dry-run execution planning for Grona."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .adapters import ExecutionAdapter, ExecutionRequest
from .executor import ExpertResult
from .feedback import Metadata

ACTION_TYPES = (
    "read_file",
    "write_file",
    "run_command",
    "network_request",
    "delete_file",
    "modify_system",
    "unknown",
)
RISK_LEVELS = ("low", "medium", "high", "critical")
DESTRUCTIVE_ACTION_TYPES = {"write_file", "delete_file", "modify_system", "run_command"}


@dataclass(frozen=True)
class ToolAction:
    """A planned future tool action. It is never executed by this model."""

    name: str
    description: str
    command: str | None = None
    action_type: str = "unknown"
    risk_level: str = "low"
    read_only: bool = True
    requires_confirmation: bool = False
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("tool action name cannot be empty")
        if self.action_type not in ACTION_TYPES:
            raise ValueError(f"unsupported action_type: {self.action_type}")
        if self.risk_level not in RISK_LEVELS:
            raise ValueError(f"unsupported risk_level: {self.risk_level}")


@dataclass(frozen=True)
class PolicyDecision:
    """A safety decision for one planned tool action."""

    allowed: bool
    dry_run: bool
    risk_level: str
    reasons: tuple[str, ...] = ()
    required_confirmation: bool = False
    blocked_by: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        allowed: bool,
        dry_run: bool,
        risk_level: str,
        reasons: Sequence[str] = (),
        required_confirmation: bool = False,
        blocked_by: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "allowed", allowed)
        object.__setattr__(self, "dry_run", dry_run)
        object.__setattr__(self, "risk_level", risk_level)
        object.__setattr__(self, "reasons", tuple(reasons))
        object.__setattr__(self, "required_confirmation", required_confirmation)
        object.__setattr__(self, "blocked_by", tuple(blocked_by))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if risk_level not in RISK_LEVELS:
            raise ValueError(f"unsupported risk_level: {risk_level}")

    def to_text(self) -> str:
        """Format the policy decision for humans."""
        status = "allowed" if self.allowed else "blocked"
        dry_run = "dry-run" if self.dry_run else "live-plan"
        confirmation = "requires confirmation" if self.required_confirmation else "no confirmation"
        lines = [f"Policy decision: {status} ({dry_run}, {self.risk_level}, {confirmation})"]
        if self.reasons:
            lines.append("Reasons:")
            lines.extend(f"- {reason}" for reason in self.reasons)
        if self.blocked_by:
            lines.append("Blocked by:")
            lines.extend(f"- {item}" for item in self.blocked_by)
        return "\n".join(lines)


class SafetyPolicy:
    """Deterministic policy evaluator for future tool actions."""

    def __init__(
        self,
        dry_run: bool = False,
        allowed_action_types: Sequence[str] | None = None,
        denied_action_types: Sequence[str] = (),
        allowed_command_keywords: Sequence[str] | None = None,
        denied_command_keywords: Sequence[str] = (),
        allow_destructive: bool = False,
        allow_high_risk: bool = False,
        allow_unknown: bool = False,
    ) -> None:
        self.dry_run = dry_run
        self.allowed_action_types = tuple(allowed_action_types) if allowed_action_types else None
        self.denied_action_types = tuple(denied_action_types)
        self.allowed_command_keywords = (
            tuple(keyword.lower() for keyword in allowed_command_keywords)
            if allowed_command_keywords
            else None
        )
        self.denied_command_keywords = tuple(keyword.lower() for keyword in denied_command_keywords)
        self.allow_destructive = allow_destructive
        self.allow_high_risk = allow_high_risk
        self.allow_unknown = allow_unknown

    def evaluate(self, action: ToolAction) -> PolicyDecision:
        """Evaluate a planned action without executing it."""
        reasons: list[str] = []
        blocked_by: list[str] = []

        if action.action_type in self.denied_action_types:
            blocked_by.append(f"denied action type: {action.action_type}")
        if (
            self.allowed_action_types is not None
            and action.action_type not in self.allowed_action_types
        ):
            blocked_by.append(f"action type not allowlisted: {action.action_type}")
        if action.action_type == "unknown" and not self.allow_unknown:
            blocked_by.append("unknown actions are blocked by default")

        command = (action.command or "").lower()
        if command:
            denied_keywords = [word for word in self.denied_command_keywords if word in command]
            if denied_keywords:
                blocked_by.append("denied command keyword: " + ", ".join(denied_keywords))
            if self.allowed_command_keywords is not None:
                allowed_keywords = [
                    word for word in self.allowed_command_keywords if word in command
                ]
                if not allowed_keywords:
                    blocked_by.append("command keyword not allowlisted")

        destructive = is_destructive_action(action)
        if destructive and not self.allow_destructive:
            blocked_by.append("destructive actions are blocked by default")

        if action.risk_level == "critical":
            blocked_by.append("critical actions are blocked by default")
        if action.risk_level == "high" and not self.allow_high_risk:
            blocked_by.append("high-risk actions are blocked by default")

        required_confirmation = (
            action.requires_confirmation or action.risk_level in {"medium", "high"}
        )
        dry_run = self.dry_run or action.risk_level == "medium" or required_confirmation
        allowed = not blocked_by

        if allowed and action.read_only and action.risk_level == "low":
            reasons.append("low-risk read-only action is allowed")
        if allowed and action.risk_level == "medium":
            reasons.append("medium-risk action is allowed only as a dry-run plan")
        if required_confirmation:
            reasons.append("action requires confirmation before any future live execution")
        if dry_run:
            reasons.append("policy selected dry-run planning; no tool execution occurs")
        if blocked_by:
            reasons.append("policy blocked the action before execution")

        return PolicyDecision(
            allowed=allowed,
            dry_run=dry_run,
            risk_level=action.risk_level,
            reasons=reasons,
            required_confirmation=required_confirmation,
            blocked_by=blocked_by,
            metadata={
                "action_name": action.name,
                "action_type": action.action_type,
                "read_only": action.read_only,
            },
        )

    def with_dry_run(self, dry_run: bool) -> SafetyPolicy:
        """Return a copy of the policy with dry-run changed."""
        return SafetyPolicy(
            dry_run=dry_run,
            allowed_action_types=self.allowed_action_types,
            denied_action_types=self.denied_action_types,
            allowed_command_keywords=self.allowed_command_keywords,
            denied_command_keywords=self.denied_command_keywords,
            allow_destructive=self.allow_destructive,
            allow_high_risk=self.allow_high_risk,
            allow_unknown=self.allow_unknown,
        )


def is_destructive_action(action: ToolAction) -> bool:
    """Return whether an action should be treated as destructive."""
    return not action.read_only or action.action_type in DESTRUCTIVE_ACTION_TYPES


@dataclass(frozen=True)
class ExecutionPlan:
    """A dry-run plan for future execution. It does not execute actions."""

    request: ExecutionRequest
    actions: tuple[ToolAction, ...]
    policy_decisions: tuple[PolicyDecision, ...]
    approved: bool
    dry_run: bool
    summary: str

    def __init__(
        self,
        request: ExecutionRequest,
        actions: Sequence[ToolAction],
        policy_decisions: Sequence[PolicyDecision],
        summary: str | None = None,
    ) -> None:
        decisions = tuple(policy_decisions)
        approved = all(decision.allowed for decision in decisions)
        dry_run = any(decision.dry_run for decision in decisions)
        action_tuple = tuple(actions)
        object.__setattr__(self, "request", request)
        object.__setattr__(self, "actions", action_tuple)
        object.__setattr__(self, "policy_decisions", decisions)
        object.__setattr__(self, "approved", approved)
        object.__setattr__(self, "dry_run", dry_run)
        object.__setattr__(
            self,
            "summary",
            summary or summarize_plan(request, action_tuple, decisions),
        )


class SafeExecutionAdapter:
    """Safety wrapper for deterministic execution adapters."""

    def __init__(
        self,
        adapter: ExecutionAdapter,
        policy: SafetyPolicy | None = None,
        force_dry_run: bool = False,
        execute_on_dry_run: bool = False,
    ) -> None:
        self.adapter = adapter
        self.policy = policy or create_default_safety_policy(dry_run=force_dry_run)
        self.force_dry_run = force_dry_run
        self.execute_on_dry_run = execute_on_dry_run
        self.name = f"safe-{adapter.name}"
        self.description = f"Safety wrapper around {adapter.description}"
        self.supported_modules = adapter.supported_modules

    def plan(self, request: ExecutionRequest) -> ExecutionPlan:
        """Create a policy-evaluated execution plan without executing actions."""
        actions = planned_actions_for_adapter(self.adapter, request)
        policy = self.policy
        if self.force_dry_run and not policy.dry_run:
            policy = policy.with_dry_run(True)
        decisions = tuple(policy.evaluate(action) for action in actions)
        return ExecutionPlan(request=request, actions=actions, policy_decisions=decisions)

    def execute(self, request: ExecutionRequest) -> ExpertResult:
        """Evaluate policy and either return a plan result or call the wrapped adapter."""
        plan = self.plan(request)
        if not plan.approved:
            return safety_result(request, plan, "Safety policy blocked planned execution.", 0.0)
        if plan.dry_run and not self.execute_on_dry_run:
            return safety_result(request, plan, "Safety policy produced a dry-run plan.", 0.2)

        result = self.adapter.execute(request)
        metadata = {
            **result.metadata,
            **safety_metadata(plan),
            "safe_adapter_name": self.name,
        }
        return ExpertResult(
            module_name=result.module_name,
            task=result.task,
            summary=result.summary,
            details=(*result.details, plan.summary),
            confidence=result.confidence,
            metadata=metadata,
        )


def planned_actions_for_adapter(
    adapter: ExecutionAdapter,
    request: ExecutionRequest,
) -> tuple[ToolAction, ...]:
    """Ask an adapter for planned actions or build deterministic defaults."""
    planner = getattr(adapter, "planned_actions", None)
    if callable(planner):
        return tuple(planner(request))
    return default_planned_actions(request)


def default_planned_actions(request: ExecutionRequest) -> tuple[ToolAction, ...]:
    """Return deterministic future-facing action plans for demo modules."""
    module_name = request.module_name
    if module_name == "code-assistant":
        return (
            ToolAction(
                name="analyze_code_structure",
                description="Plan a read-only code structure analysis.",
                action_type="read_file",
                risk_level="low",
                read_only=True,
            ),
        )
    if module_name == "document-search":
        return (
            ToolAction(
                name="search_documents",
                description="Plan a read-only document search.",
                action_type="read_file",
                risk_level="low",
                read_only=True,
            ),
        )
    if module_name == "media-video-tool":
        return (
            ToolAction(
                name="inspect_media_metadata",
                description="Plan a read-only media metadata inspection.",
                action_type="read_file",
                risk_level="low",
                read_only=True,
            ),
        )
    if module_name == "cybersecurity-scanner":
        return (
            ToolAction(
                name="security_review",
                description="Plan a security review without network scanning.",
                action_type="network_request",
                risk_level="medium",
                read_only=True,
                requires_confirmation=True,
            ),
        )
    return (
        ToolAction(
            name=f"plan_{module_name}",
            description="Plan a read-only deterministic adapter action.",
            action_type="read_file",
            risk_level="low",
            read_only=True,
        ),
    )


def safety_result(
    request: ExecutionRequest,
    plan: ExecutionPlan,
    summary: str,
    confidence: float,
) -> ExpertResult:
    """Create an ExpertResult that explains policy-only execution planning."""
    details = tuple(
        (
            plan.summary,
            *(decision.to_text() for decision in plan.policy_decisions),
        )
    )
    return ExpertResult(
        module_name=request.module_name,
        task=request.task,
        summary=summary,
        details=details,
        confidence=confidence,
        metadata=safety_metadata(plan),
    )


def safety_metadata(plan: ExecutionPlan) -> Metadata:
    """Summarize a plan for result and orchestration metadata."""
    blocked = sum(1 for decision in plan.policy_decisions if not decision.allowed)
    allowed = sum(1 for decision in plan.policy_decisions if decision.allowed)
    return {
        "safety_policy_used": True,
        "planned_action_count": len(plan.actions),
        "allowed_action_count": allowed,
        "blocked_action_count": blocked,
        "dry_run_tools": plan.dry_run,
        "execution_plan_summary": plan.summary,
    }


def summarize_plan(
    request: ExecutionRequest,
    actions: tuple[ToolAction, ...],
    decisions: tuple[PolicyDecision, ...],
) -> str:
    """Summarize a dry-run execution plan."""
    allowed = sum(1 for decision in decisions if decision.allowed)
    blocked = sum(1 for decision in decisions if not decision.allowed)
    dry_run = any(decision.dry_run for decision in decisions)
    return (
        f"Planned {len(actions)} tool actions for {request.module_name}: "
        f"{allowed} allowed, {blocked} blocked, dry_run={dry_run}."
    )


def create_default_safety_policy(dry_run: bool = False) -> SafetyPolicy:
    """Create the default conservative safety policy."""
    return SafetyPolicy(
        dry_run=dry_run,
        denied_action_types=("delete_file", "modify_system"),
        denied_command_keywords=("rm", "del", "format", "shutdown", "curl", "wget"),
        allow_destructive=False,
        allow_high_risk=False,
        allow_unknown=False,
    )
