from grona import (
    FeedbackRecord,
    InMemoryFeedbackStore,
    JsonlFeedbackStore,
    Router,
    create_default_registry,
    summarize_feedback,
)


def make_record(task: str = "Analyze engine overheating symptoms") -> FeedbackRecord:
    decision = Router(create_default_registry(), top_k=3).route(task)
    return FeedbackRecord.from_decision(
        decision,
        rating=5,
        success=True,
        notes="Good route",
        metadata={"source": "test"},
        timestamp="2026-01-01T00:00:00+00:00",
    )


def test_feedback_record_creation_and_serialization() -> None:
    record = FeedbackRecord(
        task="task",
        selected_modules=("code-assistant",),
        skipped_modules=("document-search",),
        confidence=0.75,
        route_summary="Selected: code-assistant. Skipped: document-search.",
        timestamp="2026-01-01T00:00:00+00:00",
        rating=4,
        success=True,
        notes="Useful route",
        metadata={"case": "unit"},
    )

    restored = FeedbackRecord.from_dict(record.to_dict())

    assert restored == record


def test_feedback_record_from_decision_preserves_route_data() -> None:
    record = make_record()

    assert record.task == "Analyze engine overheating symptoms"
    assert "automotive-diagnostics" in record.selected_modules
    assert "cybersecurity-scanner" in record.skipped_modules
    assert record.confidence > 0
    assert "Selected:" in record.route_summary
    assert record.rating == 5
    assert record.success is True
    assert record.notes == "Good route"
    assert record.metadata == {"source": "test"}


def test_in_memory_feedback_store_add_list_count_and_clear() -> None:
    store = InMemoryFeedbackStore()
    record = make_record()

    store.add(record)

    assert store.count() == 1
    assert store.list() == (record,)

    store.clear()

    assert store.count() == 0
    assert store.list() == ()


def test_jsonl_feedback_store_write_read_list_count_and_clear(tmp_path) -> None:
    store = JsonlFeedbackStore(tmp_path / "feedback.jsonl")
    record = make_record()

    store.add(record)

    assert store.count() == 1
    assert store.list() == (record,)

    store.clear()

    assert store.count() == 0
    assert store.list() == ()


def test_feedback_summary_by_module_and_average_confidence() -> None:
    first = make_record("Analyze engine overheating symptoms")
    second = make_record("Review firewall logs for suspicious port scans")
    failed = FeedbackRecord.from_decision(
        Router(create_default_registry(), top_k=3).route("Unknown task"),
        success=False,
        timestamp="2026-01-01T00:00:00+00:00",
    )
    store = InMemoryFeedbackStore([first, second, failed])

    summary = summarize_feedback(store.list())
    by_module = store.summarize_by_module()

    assert summary.total_records == 3
    assert summary.average_confidence >= 0
    assert summary.success_count == 2
    assert summary.failure_count == 1
    assert by_module["automotive-diagnostics"] == 1
    assert by_module["cybersecurity-scanner"] == 1
