from grona import (
    ContextBuilder,
    InMemoryKeywordMemory,
    JsonlMemoryStore,
    MemoryRecord,
    Orchestrator,
    Router,
    create_default_memory_modules,
    create_default_registry,
)
from grona.cli import main


def test_memory_record_creation() -> None:
    record = MemoryRecord(
        id="auto-1",
        content="Check coolant level and fan activation.",
        domains=("automotive",),
        keywords=("coolant", "fan"),
        source="test-memory",
        metadata={"kind": "checklist"},
    )

    assert record.id == "auto-1"
    assert record.domains == ("automotive",)
    assert record.keywords == ("coolant", "fan")
    assert record.metadata == {"kind": "checklist"}


def test_in_memory_keyword_memory_searches_by_keyword() -> None:
    memory = InMemoryKeywordMemory(
        [
            MemoryRecord(
                id="cooling",
                content="Inspect coolant circulation and radiator flow.",
                domains=("automotive",),
                keywords=("coolant", "radiator"),
            )
        ]
    )

    results = memory.search(
        "Diagnose coolant overheating",
        domains=("automotive car engine",),
        capabilities=("diagnostics",),
        limit=3,
    )

    assert len(results) == 1
    assert results[0].metadata["record_id"] == "cooling"
    assert "keyword match" in "; ".join(results[0].metadata["reasons"])


def test_in_memory_keyword_memory_searches_by_domain() -> None:
    memory = InMemoryKeywordMemory(
        [
            MemoryRecord(
                id="security",
                content="Review permissions and authentication boundaries.",
                domains=("cybersecurity",),
                keywords=("permissions",),
            )
        ]
    )

    results = memory.search(
        "Review an access issue",
        domains=("cybersecurity security network",),
        capabilities=("incident triage",),
        limit=3,
    )

    assert len(results) == 1
    assert results[0].source.startswith("memory:")
    assert results[0].relevance == 1.0


def test_memory_relevance_is_deterministic_and_irrelevant_records_are_skipped() -> None:
    records = [
        MemoryRecord(
            id="code",
            content="Check tests and linting.",
            domains=("code",),
            keywords=("tests", "linting"),
        ),
        MemoryRecord(
            id="media",
            content="Inspect color grading workflow.",
            domains=("media",),
            keywords=("color",),
        ),
    ]
    memory = InMemoryKeywordMemory(records)

    first = memory.search(
        "Improve tests",
        domains=("code software programming",),
        capabilities=("debugging",),
        limit=3,
    )
    second = memory.search(
        "Improve tests",
        domains=("code software programming",),
        capabilities=("debugging",),
        limit=3,
    )

    assert [(item.source, item.relevance) for item in first] == [
        (item.source, item.relevance) for item in second
    ]
    assert [item.metadata["record_id"] for item in first] == ["code"]


def test_context_builder_works_without_memory_modules() -> None:
    decision = Router(create_default_registry(), top_k=2).route("Analyze engine overheating")

    items = ContextBuilder().build(decision)

    assert items
    assert all(item.metadata.get("context_kind") == "stub" for item in items)


def test_context_builder_includes_memory_context() -> None:
    decision = Router(create_default_registry(), top_k=2).route("Analyze engine overheating")
    builder = ContextBuilder(memory_modules=create_default_memory_modules())

    items = builder.build(decision)

    assert any(item.source.startswith("memory:") for item in items)
    assert any(item.metadata.get("context_kind") == "stub" for item in items)


def test_memory_context_items_are_included_in_orchestration_result() -> None:
    router = Router(create_default_registry(), top_k=2)
    builder = ContextBuilder(memory_modules=create_default_memory_modules())

    result = Orchestrator(router, context_builder=builder).run("Analyze engine overheating")

    assert any(item.source.startswith("memory:") for item in result.context_items)
    assert result.metadata["source_counts"]["memory"] > 0
    assert "memory" in result.summary


def test_context_builder_respects_max_context_limit() -> None:
    decision = Router(create_default_registry(), top_k=3).route(
        "Review repository code security documents and planning risks"
    )
    builder = ContextBuilder(
        memory_modules=create_default_memory_modules(),
        max_context_items=2,
        memory_context_limit=3,
    )

    items = builder.build(decision)

    assert len(items) == 2


def test_jsonl_memory_store_round_trips_records(tmp_path) -> None:
    store = JsonlMemoryStore(tmp_path / "memory.jsonl")
    record = MemoryRecord(
        id="doc",
        content="Index documents before summarization.",
        domains=("document",),
        keywords=("index", "summary"),
    )

    store.save([record])

    assert store.load() == (record,)
    assert store.to_memory_module().search(
        "Summarize document",
        domains=("document search",),
        capabilities=("summarization",),
        limit=1,
    )


def test_cli_use_demo_memory_with_orchestration(capsys) -> None:
    assert main(["Analyze", "engine", "overheating", "--orchestrate", "--use-demo-memory"]) == 0

    output = capsys.readouterr().out
    assert "memory:" in output
    assert "Orchestration summary:" in output


def test_cli_use_demo_memory_without_orchestration_prints_note(capsys) -> None:
    assert main(["Analyze", "engine", "overheating", "--use-demo-memory"]) == 0

    output = capsys.readouterr().out
    assert "Memory note:" in output
