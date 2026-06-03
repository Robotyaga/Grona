from grona import (
    ContextBuilder,
    DocumentChunk,
    DocumentIngestor,
    DocumentSource,
    Router,
    TextChunker,
    assign_domains,
    create_default_registry,
    create_demo_document_sources,
    extract_keywords,
)
from grona.cli import main


def test_document_source_creation() -> None:
    source = DocumentSource(
        id="note-1",
        title="Note",
        content="A short note about coolant.",
        source_type="note",
        metadata={"kind": "demo"},
    )

    assert source.id == "note-1"
    assert source.source_type == "note"
    assert source.metadata == {"kind": "demo"}


def test_document_chunk_creation() -> None:
    chunk = DocumentChunk(
        id="note-1:chunk-0000",
        source_id="note-1",
        content="Check coolant and radiator flow.",
        index=0,
        keywords=("coolant", "radiator"),
        domains=("automotive",),
        metadata={"source_title": "Note"},
    )

    assert chunk.id == "note-1:chunk-0000"
    assert chunk.keywords == ("coolant", "radiator")
    assert chunk.domains == ("automotive",)


def test_text_chunker_empty_input() -> None:
    source = DocumentSource("empty", "Empty", "   ", source_type="text")

    assert TextChunker(max_chars=20, overlap_chars=5).chunk(source) == ()


def test_text_chunker_deterministic_chunks() -> None:
    source = DocumentSource(
        "src",
        "Source",
        "alpha beta gamma delta epsilon zeta eta theta iota kappa",
        source_type="text",
    )
    chunker = TextChunker(max_chars=24, overlap_chars=5)

    first = chunker.chunk(source)
    second = chunker.chunk(source)

    assert first == second
    assert len(first) > 1
    assert [chunk.id for chunk in first] == [
        f"src:chunk-{index:04d}" for index in range(len(first))
    ]


def test_text_chunker_overlap_behavior() -> None:
    source = DocumentSource(
        "overlap",
        "Overlap",
        "alpha beta gamma delta epsilon",
        source_type="text",
    )
    chunks = TextChunker(max_chars=18, overlap_chars=6).chunk(source)

    assert len(chunks) >= 2
    assert chunks[0].content.endswith("gamma")
    assert chunks[1].content.startswith("gamma")


def test_keyword_extraction_is_deterministic() -> None:
    keywords = extract_keywords("Python python tests lint code code code", limit=4)

    assert keywords == ("code", "python", "lint", "tests")


def test_domain_assignment_matches_known_domains() -> None:
    assert assign_domains("coolant radiator thermostat") == ("automotive",)
    assert assign_domains("python tests package") == ("code",)
    assert assign_domains("firewall secrets port scan") == ("cybersecurity",)
    assert assign_domains("MotionCam video codec export") == ("media",)
    assert assign_domains("document indexing retrieval notes") == (
        "documents",
        "document",
        "search",
        "retrieval",
    )
    assert assign_domains("unclear broad task") == ("general",)


def test_document_ingestor_ingest() -> None:
    source = DocumentSource(
        "auto",
        "Auto note",
        "Check coolant level, radiator flow, thermostat behavior, and fan activation.",
        source_type="note",
    )

    chunks = DocumentIngestor(TextChunker(max_chars=80, overlap_chars=10)).ingest(source)

    assert len(chunks) == 1
    assert chunks[0].source_id == "auto"
    assert "coolant" in chunks[0].keywords
    assert "automotive" in chunks[0].domains


def test_chunks_to_memory_records() -> None:
    chunk = DocumentChunk(
        "doc:chunk-0000",
        "doc",
        "Document indexing notes preserve citations.",
        0,
        keywords=("document", "indexing"),
        domains=("documents", "document", "search", "retrieval"),
        metadata={"source_title": "Docs"},
    )

    records = DocumentIngestor().chunks_to_memory_records([chunk])

    assert len(records) == 1
    assert records[0].id == "doc:chunk-0000"
    assert records[0].source == "document_ingestion"
    assert records[0].metadata["source_id"] == "doc"


def test_build_memory_module() -> None:
    sources = create_demo_document_sources()
    memory = DocumentIngestor(TextChunker(max_chars=180, overlap_chars=20)).build_memory_module(
        "ingested-docs",
        sources,
    )

    assert memory.name == "ingested-docs"
    assert memory.records
    assert "automotive" in memory.domains


def test_context_builder_retrieves_ingested_document_context() -> None:
    memory = DocumentIngestor(TextChunker(max_chars=180, overlap_chars=20)).build_memory_module(
        "ingested-docs",
        create_demo_document_sources(),
    )
    decision = Router(create_default_registry(), top_k=2).route("Diagnose engine overheating")
    builder = ContextBuilder(memory_modules=(memory,), max_context_items=4)

    items = builder.build(decision)

    assert any(
        item.source.startswith("memory:ingested-docs:document_ingestion")
        for item in items
    )
    assert any(item.metadata.get("memory_origin") == "document_ingestion" for item in items)


def test_cli_ingest_demo_docs_with_orchestration(capsys) -> None:
    assert main(
        [
            "Diagnose",
            "engine",
            "overheating",
            "--orchestrate",
            "--ingest-demo-docs",
        ]
    ) == 0

    output = capsys.readouterr().out
    assert "--ingest-demo-docs added deterministic ingested memory" in output
    assert "memory:demo-document-ingestion:document_ingestion" in output


def test_cli_ingest_demo_docs_without_orchestration_prints_note(capsys) -> None:
    assert main(["Diagnose", "engine", "overheating", "--ingest-demo-docs"]) == 0

    output = capsys.readouterr().out
    assert "--ingest-demo-docs is only used with orchestration" in output
