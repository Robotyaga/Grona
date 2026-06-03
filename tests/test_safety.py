from grona import (
    ExecutionPlan,
    ExecutionRequest,
    Orchestrator,
    PolicyDecision,
    Router,
    SafeExecutionAdapter,
    SafetyPolicy,
    StaticExecutionAdapter,
    ToolAction,
    create_default_adapter_registry,
    create_default_registry,
    create_default_safety_policy,
)
from grona.cli import main


def test_tool_action_creation() -> None:
    action = ToolAction(
        name="read_notes",
        description="Read notes.",
        action_type="read_file",
        risk_level="low",
        read_only=True,
        metadata={"source": "test"},
    )

    assert action.name == "read_notes"
    assert action.command is None
    assert action.metadata == {"source": "test"}


def test_policy_decision_formatting() -> None:
    decision = PolicyDecision(
        allowed=False,
        dry_run=True,
        risk_level="high",
        reasons=("policy blocked the action",),
        required_confirmation=True,
        blocked_by=("high-risk actions are blocked by default",),
    )

    output = decision.to_text()

    assert "Policy decision: blocked" in output
    assert "requires confirmation" in output
    assert "Blocked by:" in output


def test_safety_policy_allows_read_only_low_risk_action() -> None:
    decision = create_default_safety_policy().evaluate(
        ToolAction(
            name="read_file",
            description="Read a file.",
            action_type="read_file",
            risk_level="low",
            read_only=True,
        )
    )

    assert decision.allowed is True
    assert decision.dry_run is False
    assert "low-risk read-only action is allowed" in decision.reasons


def test_safety_policy_blocks_critical_action() -> None:
    decision = create_default_safety_policy().evaluate(
        ToolAction(
            name="critical_change",
            description="Modify a system file.",
            action_type="modify_system",
            risk_level="critical",
            read_only=False,
        )
    )

    assert decision.allowed is False
    assert any("critical" in item for item in decision.blocked_by)


def test_safety_policy_blocks_destructive_action() -> None:
    decision = create_default_safety_policy().evaluate(
        ToolAction(
            name="delete_file",
            description="Delete a file.",
            action_type="delete_file",
            risk_level="high",
            read_only=False,
        )
    )

    assert decision.allowed is False
    assert any("destructive" in item for item in decision.blocked_by)


def test_safety_policy_applies_dry_run() -> None:
    decision = create_default_safety_policy(dry_run=True).evaluate(
        ToolAction(
            name="read_file",
            description="Read a file.",
            action_type="read_file",
            risk_level="low",
            read_only=True,
        )
    )

    assert decision.allowed is True
    assert decision.dry_run is True


def test_safety_policy_allowlist_and_denylist_behavior() -> None:
    policy = SafetyPolicy(
        allowed_action_types=("read_file",),
        denied_command_keywords=("curl",),
    )

    denied_type = policy.evaluate(
        ToolAction(
            name="network",
            description="Network request.",
            command="curl https://example.com",
            action_type="network_request",
            risk_level="medium",
            read_only=True,
        )
    )
    allowed_type = policy.evaluate(
        ToolAction(
            name="read",
            description="Read file.",
            command="cat README.md",
            action_type="read_file",
            risk_level="low",
            read_only=True,
        )
    )

    assert denied_type.allowed is False
    assert any("not allowlisted" in item for item in denied_type.blocked_by)
    assert any("denied command keyword" in item for item in denied_type.blocked_by)
    assert allowed_type.allowed is True


def test_execution_plan_creation() -> None:
    request = ExecutionRequest("Review code", "code-assistant")
    action = ToolAction(
        name="read_code",
        description="Read code.",
        action_type="read_file",
        risk_level="low",
        read_only=True,
    )
    decision = create_default_safety_policy().evaluate(action)

    plan = ExecutionPlan(request, (action,), (decision,))

    assert plan.approved is True
    assert plan.dry_run is False
    assert "Planned 1 tool actions" in plan.summary


def test_safe_execution_adapter_returns_dry_run_result_for_medium_risk() -> None:
    adapter = create_default_adapter_registry().get("cybersecurity-scanner")
    assert adapter is not None
    safe_adapter = SafeExecutionAdapter(adapter, create_default_safety_policy())

    result = safe_adapter.execute(ExecutionRequest("Review security logs", "cybersecurity-scanner"))

    assert result.summary == "Safety policy produced a dry-run plan."
    assert result.metadata["safety_policy_used"] is True
    assert result.metadata["dry_run_tools"] is True


def test_safe_execution_adapter_blocks_unknown_action() -> None:
    class UnknownPlanningAdapter:
        name = "unknown-planner"
        description = "Plans an unknown action."
        supported_modules = ("general-reasoning",)

        def planned_actions(self, request: ExecutionRequest) -> tuple[ToolAction, ...]:
            return (
                ToolAction(
                    name="unknown",
                    description="Unknown action.",
                    action_type="unknown",
                    risk_level="low",
                    read_only=True,
                ),
            )

        def execute(self, request: ExecutionRequest):  # noqa: ANN001, ANN201
            raise AssertionError("wrapped adapter should not execute")

    result = SafeExecutionAdapter(
        UnknownPlanningAdapter(),
        create_default_safety_policy(),
    ).execute(ExecutionRequest("Plan", "general-reasoning"))

    assert result.summary == "Safety policy blocked planned execution."
    assert result.metadata["blocked_action_count"] == 1


def test_orchestrator_metadata_includes_safety_summary() -> None:
    router = Router(create_default_registry(), top_k=3)
    result = Orchestrator(
        router,
        adapter_registry=create_default_adapter_registry(),
        safety_policy=create_default_safety_policy(),
    ).run("Review this Python project for tests and security issues")

    assert result.metadata["safety_policy_used"] is True
    assert result.metadata["planned_action_count"] > 0
    assert "safety planned" in result.summary


def test_cli_safe_adapter_behavior(capsys) -> None:
    assert main(
        [
            "Review",
            "this",
            "project",
            "for",
            "security",
            "issues",
            "--orchestrate",
            "--use-demo-adapters",
            "--safe",
        ]
    ) == 0

    output = capsys.readouterr().out
    assert "Safety: policy used" in output
    assert "Execution: safety policy planning only" in output


def test_cli_dry_run_tools_enables_safety_policy(capsys) -> None:
    assert main(["Review", "code", "--use-demo-adapters", "--dry-run-tools"]) == 0

    output = capsys.readouterr().out
    assert "--dry-run-tools enables the default safety policy" in output
    assert "dry-run True" in output
