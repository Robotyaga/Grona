from grona import (
    AutomotiveDiagnosticsExpertExecutor,
    CodeExpertExecutor,
    ContextBuilder,
    ContextItem,
    CybersecurityExpertExecutor,
    DocumentSearchExpertExecutor,
    ExpertExecutorRegistry,
    ExpertResult,
    GeneralReasoningExpertExecutor,
    MediaWorkflowExpertExecutor,
    Orchestrator,
    Router,
    create_default_executor_registry,
    create_default_memory_modules,
    create_default_registry,
)
from grona.cli import main


def demo_context() -> tuple[ContextItem, ...]:
    return (
        ContextItem(
            source="memory:test:auto",
            content="Check coolant, thermostat, radiator flow, and fan activation.",
            relevance=1.0,
            metadata={"context_kind": "memory"},
        ),
    )


def test_expert_result_creation_and_formatting() -> None:
    result = ExpertResult(
        module_name="code-assistant",
        task="Review code",
        summary="Prepared a code outline.",
        details=("Run tests.", "Check linting."),
        confidence=0.75,
        metadata={"executor_kind": "deterministic_demo"},
    )

    text = result.to_text()

    assert "Expert: code-assistant" in text
    assert "Run tests." in text
    assert result.confidence == 0.75


def test_demo_executors_return_deterministic_results() -> None:
    executors = (
        CodeExpertExecutor(),
        AutomotiveDiagnosticsExpertExecutor(),
        CybersecurityExpertExecutor(),
        MediaWorkflowExpertExecutor(),
        DocumentSearchExpertExecutor(),
        GeneralReasoningExpertExecutor(),
    )

    for executor in executors:
        first = executor.execute("Demo task", demo_context())
        second = executor.execute("Demo task", demo_context())
        assert first == second
        assert first.module_name == executor.module_name
        assert first.details
        assert first.metadata["executor_kind"] == "deterministic_demo"


def test_executor_registry_register_get_list_and_missing() -> None:
    registry = ExpertExecutorRegistry()
    executor = CodeExpertExecutor()

    registry.register(executor)

    assert registry.get("code-assistant") is executor
    assert registry.list() == (executor,)
    assert registry.missing(("code-assistant", "missing-module")) == ("missing-module",)


def test_orchestrator_without_executor_registry_still_works() -> None:
    router = Router(create_default_registry(), top_k=2)

    result = Orchestrator(router).run("Analyze engine overheating symptoms")

    assert result.expert_results == ()
    assert result.metadata["execution"] == "not_run"


def test_orchestrator_with_executor_registry_returns_expert_results() -> None:
    router = Router(create_default_registry(), top_k=2)
    orchestrator = Orchestrator(router, executor_registry=create_default_executor_registry())

    result = orchestrator.run("Analyze engine overheating symptoms")

    assert result.expert_results
    assert result.metadata["execution"] == "executed"
    assert result.metadata["expert_result_count"] == len(result.expert_results)
    assert any(item.module_name == "automotive-diagnostics" for item in result.expert_results)


def test_missing_executor_behavior_does_not_crash() -> None:
    router = Router(create_default_registry(), top_k=2)
    registry = ExpertExecutorRegistry((CodeExpertExecutor(),))

    result = Orchestrator(router, executor_registry=registry).run(
        "Analyze engine overheating symptoms"
    )

    assert result.metadata["missing_executors"]
    assert "missing executors" in result.summary


def test_execution_with_memory_context_includes_relevant_details() -> None:
    router = Router(create_default_registry(), top_k=2)
    builder = ContextBuilder(memory_modules=create_default_memory_modules())
    orchestrator = Orchestrator(
        router,
        context_builder=builder,
        executor_registry=create_default_executor_registry(),
    )

    result = orchestrator.run("Diagnose engine overheating")
    automotive = next(
        item for item in result.expert_results if item.module_name == "automotive-diagnostics"
    )

    assert any("coolant" in detail.lower() for detail in automotive.details)
    assert result.metadata["source_counts"]["memory"] > 0


def test_mixed_task_produces_multiple_expert_results() -> None:
    router = Router(create_default_registry(), top_k=3)
    orchestrator = Orchestrator(router, executor_registry=create_default_executor_registry())

    result = orchestrator.run("Review this Python package for tests and exposed secrets")

    module_names = {item.module_name for item in result.expert_results}
    assert "code-assistant" in module_names
    assert "cybersecurity-scanner" in module_names


def test_cli_execute_demo_experts_implies_orchestration(capsys) -> None:
    assert main(["Diagnose", "engine", "overheating", "--execute-demo-experts"]) == 0

    output = capsys.readouterr().out
    assert "Execution note: --execute-demo-experts implies --orchestrate." in output
    assert "Expert results:" in output
    assert "automotive-diagnostics" in output


def test_cli_execute_demo_experts_with_memory(capsys) -> None:
    assert main(
        [
            "Diagnose",
            "engine",
            "overheating",
            "--orchestrate",
            "--use-demo-memory",
            "--execute-demo-experts",
        ]
    ) == 0

    output = capsys.readouterr().out
    assert "memory:" in output
    assert "Expert results:" in output
    assert "deterministic demo executors only" in output
