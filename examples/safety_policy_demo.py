"""Demonstrate Grona's deterministic tool safety policy layer."""

from grona import (
    ExecutionRequest,
    Orchestrator,
    Router,
    SafeExecutionAdapter,
    StaticExecutionAdapter,
    ToolAction,
    create_default_adapter_registry,
    create_default_registry,
    create_default_safety_policy,
)
from grona.cli import format_orchestration_result

ACTIONS = (
    ToolAction(
        name="read_project_notes",
        description="Read project notes for context.",
        action_type="read_file",
        risk_level="low",
        read_only=True,
    ),
    ToolAction(
        name="review_security_surface",
        description="Plan a security review that would require confirmation later.",
        action_type="network_request",
        risk_level="medium",
        read_only=True,
        requires_confirmation=True,
    ),
    ToolAction(
        name="delete_cache",
        description="Delete a cache directory.",
        action_type="delete_file",
        risk_level="high",
        read_only=False,
    ),
    ToolAction(
        name="mystery_tool",
        description="Unknown future tool action.",
        action_type="unknown",
        risk_level="low",
        read_only=True,
    ),
)


def print_policy_decisions() -> None:
    policy = create_default_safety_policy()
    print("=" * 80)
    print("Policy decisions")
    for action in ACTIONS:
        print(f"Action: {action.name}")
        print(policy.evaluate(action).to_text())
        print()


def print_safe_adapter_demo() -> None:
    adapter = StaticExecutionAdapter(
        name="demo-static-adapter",
        responses={
            "code-assistant": (
                "Static adapter would prepare a code review result.",
                ("No command execution happens in this demo.",),
            )
        },
    )
    safe_adapter = SafeExecutionAdapter(adapter, create_default_safety_policy())
    request = ExecutionRequest("Review project code", "code-assistant")

    print("=" * 80)
    print("SafeExecutionAdapter")
    print(safe_adapter.execute(request).to_text())
    print()


def print_orchestrator_demo() -> None:
    router = Router(create_default_registry(), top_k=3)
    orchestrator = Orchestrator(
        router,
        adapter_registry=create_default_adapter_registry(),
        safety_policy=create_default_safety_policy(),
    )
    result = orchestrator.run("Review this Python project for tests and security issues")

    print("=" * 80)
    print("Orchestrator with safety enabled")
    print(format_orchestration_result(result))
    print()


def main() -> None:
    print_policy_decisions()
    print_safe_adapter_demo()
    print_orchestrator_demo()


if __name__ == "__main__":
    main()
