from grona import FeedbackRecord, JsonlFeedbackStore, Router, create_default_registry
from grona.cli import format_decision, main


def test_cli_formatter_prints_selected_skipped_reasons_and_scores() -> None:
    decision = Router(create_default_registry(), top_k=2).route(
        "Analyze engine overheating symptoms"
    )
    output = format_decision(decision)

    assert "Selected modules:" in output
    assert "Skipped modules:" in output
    assert "automotive-diagnostics" in output
    assert "score" in output
    assert "reason:" in output


def test_cli_does_not_write_feedback_without_feedback_file(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["Analyze", "engine", "overheating"]) == 0

    capsys.readouterr()
    assert not list(tmp_path.glob("*.jsonl"))


def test_cli_writes_feedback_when_feedback_file_is_provided(tmp_path, capsys) -> None:
    feedback_file = tmp_path / "feedback.jsonl"

    assert main(
        [
            "Analyze",
            "engine",
            "overheating",
            "--feedback-file",
            str(feedback_file),
            "--rating",
            "5",
            "--success",
            "true",
            "--notes",
            "Good route",
        ]
    ) == 0

    capsys.readouterr()
    records = JsonlFeedbackStore(feedback_file).list()
    assert len(records) == 1
    assert records[0].rating == 5
    assert records[0].success is True
    assert records[0].notes == "Good route"


def test_cli_adaptive_mode_handles_missing_feedback_file(tmp_path, capsys) -> None:
    feedback_file = tmp_path / "missing.jsonl"

    assert main(
        [
            "Analyze",
            "engine",
            "overheating",
            "--adaptive",
            "--feedback-file",
            str(feedback_file),
        ]
    ) == 0

    output = capsys.readouterr().out
    assert "Adaptive routing: enabled (no feedback history)" in output
    assert feedback_file.exists()


def test_cli_adaptive_mode_loads_feedback_history(tmp_path, capsys) -> None:
    feedback_file = tmp_path / "feedback.jsonl"
    decision = Router(create_default_registry(), top_k=3).route(
        "Analyze engine overheating symptoms"
    )
    JsonlFeedbackStore(feedback_file).add(
        FeedbackRecord.from_decision(decision, success=True, rating=5)
    )

    assert main(
        [
            "Analyze",
            "engine",
            "overheating",
            "--adaptive",
            "--feedback-file",
            str(feedback_file),
        ]
    ) == 0

    output = capsys.readouterr().out
    assert "Adaptive routing: enabled (feedback history loaded)" in output
    assert "adaptive boost" in output
