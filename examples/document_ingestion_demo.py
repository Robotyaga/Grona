"""Demonstrate deterministic in-memory document ingestion for Grona."""

from grona import (
    ContextBuilder,
    DocumentIngestor,
    DocumentSource,
    Router,
    TextChunker,
    create_default_registry,
    create_demo_document_sources,
)
from grona.cli import format_orchestration_result
from grona.orchestrator import Orchestrator


def print_chunks() -> None:
    source = DocumentSource(
        id="custom-overheating-note",
        title="Garage overheating note",
        source_type="note",
        content=(
            "When an engine overheats at idle, check coolant level, fan activation, "
            "radiator flow, thermostat behavior, and visible leaks before replacing parts."
        ),
        metadata={"example": True},
    )
    ingestor = DocumentIngestor(TextChunker(max_chars=90, overlap_chars=15))
    chunks = ingestor.ingest(source)
    records = ingestor.chunks_to_memory_records(chunks)

    print("=" * 80)
    print("Custom document chunks")
    for chunk in chunks:
        print(f"- {chunk.id}: {chunk.content}")
        print(f"  keywords: {', '.join(chunk.keywords)}")
        print(f"  domains: {', '.join(chunk.domains)}")
    print()

    print("=" * 80)
    print("Memory records from chunks")
    for record in records:
        print(f"- {record.id}: {record.source}; {', '.join(record.domains)}")
    print()


def print_ingested_orchestration() -> None:
    ingestor = DocumentIngestor(TextChunker(max_chars=160, overlap_chars=20))
    memory = ingestor.build_memory_module(
        "demo-document-ingestion",
        create_demo_document_sources(),
    )
    router = Router(create_default_registry(), top_k=3)
    builder = ContextBuilder(memory_modules=(memory,), max_context_items=5)
    result = Orchestrator(router, context_builder=builder).run(
        "Diagnose engine overheating and explain what to inspect first"
    )

    print("=" * 80)
    print("Orchestration with ingested document memory")
    print(format_orchestration_result(result))
    print()


def main() -> None:
    print_chunks()
    print_ingested_orchestration()


if __name__ == "__main__":
    main()
