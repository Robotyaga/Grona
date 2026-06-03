from grona import (
    CodeExpertExecutor,
    ContextItem,
    ExecutionAdapterRegistry,
    ExecutionRequest,
    ExpertExecutorRegistry,
    ExpertResult,
    Orchestrator,
    PythonFunctionAdapter,
    Router,
    StaticExecutionAdapter,
    create_default_adapter_registry,
    create_default_registry,
)
from grona.cli import format_orchestration_result, main


def demo_context() -> tuple[ContextItem, ...]:
    return (
        ContextItem(
            source="demo:test",
            content="Review tests, secrets, coolant, and planning constraints.",
            relevance=1.0,
            metadata={"context_kind": "stub"},
        ),
    )


def test_execution_request_creation() -> None:
    request = ExecutionRequest(
        task="Review code",
        module_name="code-assistant",
        context_items=demo_context(),
        metadata={"source": "test"},
    )

    assert request.task == "Review code"
    assert request.module_name == "code-assistant"
    assert request.context_items == demo_context()
    assert request.metadata == {"source": "test"}


def test_static_execution_adapter_returns_expert_result() -> None:
    adapter = StaticExecutionAdapter(
        name="static-test",
        responses={
            "code-assistant": (
                "Static adapter summary.",
                ("Static adapter detail.",),
            ),
        },
    )

    result = adapter.execute(
        ExecutionRequest("Review code", "code-assistant", demo_context())
    )

    assert result.module_name == "code-assistant"
    assert result.summary == "Static adapter summary."
    assert "Static adapter detail." in result.details
    assert result.metadata["adapter_name"] == "static-test"
    assert result.metadata["execution_backend"] == "adapter"


def test_python_function_adapter_wraps_callable() -> None:
    def handler(request: ExecutionRequest) -> ExpertResult:
        return ExpertResult(
            module_name=request.module_name,
            task=request.task,
            summary="Callable summary.",
            details=("Callable detail.",),
            confidence=0.66,
            metadata={"handler": "test"},
        )

    adapter = PythonFunctionAdapter(
        name="function-test",
        supported_modules=("general-reasoning",),
        handler=handler,
    )

    result = adapter.execute(ExecutionRequest("Plan work", "general-reasoning"))

    assert result.summary == "Callable summary."
    assert result.metadata["handler"] == "test"
    assert result.metadata["adapter_name"] == "function-test"
    assert result.metadata["backend_kind"] == "python_function"


def test_execution_adapter_registry_register_get_list_and_missing() -> None:
    registry = ExecutionAdapterRegistry()
    later = StaticExecutionAdapter(name="z-later", responses={"code-assistant": ("z", ())})
    earlier = StaticExecutionAdapter(
        name="a-earlier",
        responses={"document-search": ("a", ())},
    )

    registry.register(later)
    registry.register(earlier)

    assert registry.get("code-assistant") is later
    assert registry.get("document-search") is earlier
    assert registry.list() == (earlier, later)
    assert registry.missing(("code-assistant", "missing-module")) == ("missing-module",)


def test_orchestrator_with_adapter_registry_returns_expert_results() -> None:
    router = Router(create_default_registry(), top_k=2)
    result = Orchestrator(
        router,
        adapter_registry=create_default_adapter_registry(),
    ).run("Analyze engine overheating symptoms")

    assert result.expert_results
    assert result.metadata["execution"] == "executed"
    assert result.metadata["execution_backend"] == "execution_adapter"
    assert result.metadata["missing_adapters"] == ()
    assert all(item.metadata["adapter_name"] for item in result.expert_results)


def test_missing_adapter_behavior_does_not_crash() -> None:
    router = Router(create_default_registry(), top_k=2)
    registry = ExecutionAdapterRegistry(
        (StaticExecutionAdapter(name="code-only", responses={"code-assistant": ("code", ())}),)
    )

    result = Orchestrator(router, adapter_registry=registry).run(
        "Analyze engine overheating symptoms"
    )

    assert result.metadata["missing_adapters"]
    assert "missing adapters" in result.summary


def test_orchestrator_prefers_executor_registry_over_adapter_registry() -> None:
    router = Router(create_default_registry(), top_k=3)
    executor_registry = ExpertExecutorRegistry((CodeExpertExecutor(),))
    adapter_registry = create_default_adapter_registry()

    result = Orchestrator(
        router,
        executor_registry=executor_registry,
        adapter_registry=adapter_registry,
    ).run("Review this Python package for tests and exposed secrets")

    assert result.metadata["execution_backend"] == "expert_executor"
    assert result.metadata["missing_executors"]
    assert result.metadata["missing_adapters"] == ()
    assert all("adapter_name" not in item.metadata for item in result.expert_results)


def test_orchestration_formatting_includes_adapter_backend() -> None:
    router = Router(create_default_registry(), top_k=1)
    result = Orchestrator(
        router,
        adapter_registry=create_default_adapter_registry(),
    ).run("Find the PDF manual in my document archive")

    output = format_orchestration_result(result)

    assert "Backend: adapter" in output
    assert "Execution: deterministic demo adapters only" in output


def test_cli_use_demo_adapters_implies_orchestration(capsys) -> None:
    assert main(["Diagnose", "engine", "overheating", "--use-demo-adapters"]) == 0

    output = capsys.readouterr().out
    assert "Execution note: --use-demo-adapters implies --orchestrate." in output
    assert "Backend: adapter" in output
    assert "deterministic demo adapters only" in output


def test_cli_demo_experts_take_precedence_over_adapters(capsys) -> None:
    assert main(
        [
            "Review",
            "Python",
            "tests",
            "and",
            "secrets",
            "--execute-demo-experts",
            "--use-demo-adapters",
        ]
    ) == 0

    output = capsys.readouterr().out
    assert "--execute-demo-experts takes precedence" in output
    assert "Backend: executor" in output
    assert "deterministic demo executors only" in output
