"""Demonstrate deterministic execution adapters in Grona."""

from grona import (
    ContextBuilder,
    ExecutionAdapterRegistry,
    ExecutionRequest,
    ExpertResult,
    Orchestrator,
    PythonFunctionAdapter,
    Router,
    StaticExecutionAdapter,
    create_default_adapter_registry,
    create_default_memory_modules,
    create_default_registry,
)
from grona.cli import format_orchestration_result


def custom_general_handler(request: ExecutionRequest) -> ExpertResult:
    """Return a deterministic result from a Python callable adapter."""
    return ExpertResult(
        module_name=request.module_name,
        task=request.task,
        summary="Python function adapter prepared a planning checklist.",
        details=(
            "Clarify the goal before choosing a backend.",
            f"Received {len(request.context_items)} focused context items.",
        ),
        confidence=0.72,
        metadata={"handler": "custom_general_handler"},
    )


def run_with_registry(title: str, registry: ExecutionAdapterRegistry, task: str) -> None:
    """Run one deterministic adapter scenario."""
    router = Router(create_default_registry(), top_k=3)
    orchestrator = Orchestrator(
        router,
        context_builder=ContextBuilder(memory_modules=create_default_memory_modules()),
        adapter_registry=registry,
    )
    print("=" * 80)
    print(title)
    print(format_orchestration_result(orchestrator.run(task)))
    print()


def main() -> None:
    run_with_registry(
        "StaticExecutionAdapter with default demo modules",
        create_default_adapter_registry(),
        "Review this Python package for tests and exposed secrets.",
    )

    function_registry = ExecutionAdapterRegistry(
        (
            PythonFunctionAdapter(
                name="planning-function-adapter",
                supported_modules=("general-reasoning",),
                handler=custom_general_handler,
                description="Demo adapter wrapping a local Python callable.",
            ),
        )
    )
    run_with_registry(
        "PythonFunctionAdapter for general reasoning",
        function_registry,
        "Plan an ambiguous project report with risks and next checks.",
    )

    partial_registry = ExecutionAdapterRegistry(
        (
            StaticExecutionAdapter(
                name="code-only-static-adapter",
                responses={
                    "code-assistant": (
                        "Code-only adapter prepared a code review outline.",
                        ("This registry intentionally omits other modules.",),
                    ),
                },
            ),
        )
    )
    run_with_registry(
        "Missing adapter behavior",
        partial_registry,
        "Diagnose engine overheating and review the diagnostic notes.",
    )

    run_with_registry(
        "Mixed task with multiple modules",
        create_default_adapter_registry(),
        "Review Python tests, exposed secrets, and document the remediation plan.",
    )


if __name__ == "__main__":
    main()
