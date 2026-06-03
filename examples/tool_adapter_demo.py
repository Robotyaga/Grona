"""Demonstrate Grona's safe mock tool adapter prototype."""

from grona import (
    Orchestrator,
    Router,
    SafeToolRunner,
    SafetyPolicy,
    ToolRequest,
    ToolSpec,
    create_default_adapter_registry,
    create_default_registry,
    create_default_safety_policy,
    create_default_tool_registry,
)
from grona.cli import format_orchestration_result
from grona.tools import MockToolAdapter, ToolRegistry


def print_available_tools() -> None:
    registry = create_default_tool_registry()
    print("=" * 80)
    print("Available mock tools")
    for adapter in registry.list():
        print(
            f"- {adapter.spec.name}: {adapter.spec.action_type}, "
            f"risk={adapter.spec.risk_level}, read_only={adapter.spec.read_only}"
        )
    print()


def print_safe_runner_examples() -> None:
    registry = create_default_tool_registry()
    runner = SafeToolRunner(registry, create_default_safety_policy())

    print("=" * 80)
    print("Allowed read-only mock tool")
    print(
        runner.run(
            ToolRequest(
                "mock_code_inspector",
                "Review Python tests",
                requested_by="code-assistant",
            )
        ).to_text()
    )
    print()

    print("=" * 80)
    print("Dry-run medium-risk mock tool")
    print(
        runner.run(
            ToolRequest(
                "mock_security_checklist",
                "Review security exposure",
                requested_by="cybersecurity-scanner",
            )
        ).to_text()
    )
    print()


def print_blocked_tool_example() -> None:
    dangerous_registry = ToolRegistry(
        (
            MockToolAdapter(
                ToolSpec(
                    name="mock_delete_cache",
                    description="Mock destructive delete action for policy demonstration.",
                    action_type="delete_file",
                    risk_level="high",
                    read_only=False,
                    metadata={"domain": "safety-demo"},
                ),
                output="This should not execute under the default policy.",
            ),
        )
    )
    runner = SafeToolRunner(dangerous_registry, create_default_safety_policy())

    print("=" * 80)
    print("Blocked risky mock tool")
    print(
        runner.run(
            ToolRequest(
                "mock_delete_cache",
                "Clean a cache",
                requested_by="general-reasoning",
            )
        ).to_text()
    )
    print()


def print_allowlist_example() -> None:
    policy = SafetyPolicy(allowed_action_types=("read_file",))
    runner = SafeToolRunner(create_default_tool_registry(), policy)

    print("=" * 80)
    print("Policy allowlist blocks non-read action type")
    print(
        runner.run(
            ToolRequest(
                "mock_security_checklist",
                "Review security exposure",
                requested_by="cybersecurity-scanner",
            )
        ).to_text()
    )
    print()


def print_orchestration_example() -> None:
    router = Router(create_default_registry(), top_k=3)
    orchestrator = Orchestrator(
        router,
        adapter_registry=create_default_adapter_registry(),
        safety_policy=create_default_safety_policy(),
        tool_runner=SafeToolRunner(create_default_tool_registry(), create_default_safety_policy()),
    )

    print("=" * 80)
    print("Orchestration with demo adapters and mock tools")
    print(format_orchestration_result(orchestrator.run("Review Python tests and exposed secrets")))
    print()


def main() -> None:
    print_available_tools()
    print_safe_runner_examples()
    print_blocked_tool_example()
    print_allowlist_example()
    print_orchestration_example()


if __name__ == "__main__":
    main()
