from grona import Orchestrator, Router, create_default_registry
from grona.cli import format_orchestration_result, main


def test_orchestrator_routes_builds_context_and_runs_selected_modules() -> None:
    router = Router(create_default_registry(), top_k=2)
    result = Orchestrator(router).run("Analyze engine overheating symptoms")

    assert result.task == "Analyze engine overheating symptoms"
    assert "automotive-diagnostics" in result.selected_modules
    assert len(result.context_items) == len(result.routing_decision.selected_modules)
    assert len(result.module_outputs) == len(result.routing_decision.selected_modules)
    assert result.summary.startswith("Selected")
    assert result.metadata["context_count"] == len(result.context_items)


def test_orchestration_formatter_includes_context_outputs_and_summary() -> None:
    router = Router(create_default_registry(), top_k=1)
    result = Orchestrator(router).run("Find the PDF manual in my document archive")

    output = format_orchestration_result(result)

    assert "Context items:" in output
    assert "Module outputs:" in output
    assert "Orchestration summary:" in output
    assert "document-search" in output


def test_cli_orchestrate_mode_prints_context(capsys) -> None:
    assert main(["Analyze", "engine", "overheating", "--orchestrate"]) == 0

    output = capsys.readouterr().out
    assert "Context items:" in output
    assert "Module outputs:" in output
    assert "Orchestration summary:" in output
