from grona import Router, create_default_registry
from grona.cli import format_decision


def test_cli_formatter_prints_selected_skipped_reasons_and_scores() -> None:
    decision = Router(create_default_registry(), top_k=2).route("Analyze engine overheating symptoms")
    output = format_decision(decision)

    assert "Selected modules:" in output
    assert "Skipped modules:" in output
    assert "automotive-diagnostics" in output
    assert "score" in output
    assert "reason:" in output
