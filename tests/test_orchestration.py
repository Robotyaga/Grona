from grona import OrchestrationResult, Orchestrator, Router, create_default_registry
from grona.cli import format_orchestration_result, main


def test_orchestrator_returns_orchestration_result() -> None:
    router = Router(create_default_registry(), top_k=2)
    result = Orchestrator(router).run("Analyze engine overheating symptoms")

    assert isinstance(result, OrchestrationResult)
    assert result.task == "Analyze engine overheating symptoms"
    assert "automotive-diagnostics" in result.selected_modules
    assert len(result.context_items) == len(result.routing_decision.selected_modules)
    assert result.metadata["execution"] == "not_run"
    assert "would pass this focused context" in result.summary


def test_orchestrator_preserves_routing_decision() -> None:
    router = Router(create_default_registry(), top_k=2)
    result = Orchestrator(router).run("Review firewall logs for suspicious port scans")

    assert result.routing_decision.task == result.task
    assert result.selected_modules == result.routing_decision.selected_names
    assert "cybersecurity-scanner" in result.routing_decision.selected_names


def test_orchestration_result_to_text_is_non_empty() -> None:
    router = Router(create_default_registry(), top_k=1)
    result = Orchestrator(router).run("Find the PDF manual in my document archive")

    output = result.to_text()

    assert output
    assert "Context items:" in output
    assert "Orchestration summary:" in output
    assert "document-search" in output


def test_orchestration_formatter_includes_context_and_summary() -> None:
    router = Router(create_default_registry(), top_k=1)
    result = Orchestrator(router).run("Find the PDF manual in my document archive")

    output = format_orchestration_result(result)

    assert "Context items:" in output
    assert "Execution: not run" in output
    assert "Orchestration summary:" in output
    assert "document-search" in output


def test_cli_orchestrate_mode_prints_context(capsys) -> None:
    assert main(["Analyze", "engine", "overheating", "--orchestrate"]) == 0

    output = capsys.readouterr().out
    assert "Context items:" in output
    assert "Execution: not run" in output
    assert "Orchestration summary:" in output
