"""Demonstrate deterministic KnowledgeSeed validation."""

from collections import Counter

from grona import (
    DocumentIngestor,
    KnowledgeSeed,
    KnowledgeSource,
    KnowledgeValidator,
    ToolResult,
    create_demo_document_sources,
    create_demo_knowledge_seeds,
    knowledge_seed_from_document_chunk,
    knowledge_seed_from_tool_result,
)


def print_result(seed: KnowledgeSeed, validator: KnowledgeValidator) -> None:
    result = validator.validate(seed)
    print("=" * 80)
    print(f"Seed: {seed.id}")
    print(f"Source: {seed.source.name} ({seed.source.source_type})")
    print(result.to_text())


def main() -> None:
    validator = KnowledgeValidator()
    seeds = list(create_demo_knowledge_seeds())

    document_source = KnowledgeSource(
        "source:demo-documents",
        "document",
        "Demo document chunks",
        reliability=0.82,
    )
    chunks = DocumentIngestor().ingest(create_demo_document_sources()[0])
    seeds.append(knowledge_seed_from_document_chunk(chunks[0], document_source))

    tool_source = KnowledgeSource("source:mock-tool", "tool_result", "Mock tool output", 0.72)
    tool_result = ToolResult(
        tool_name="mock_code_inspector",
        success=True,
        output="Mock code inspector found test, lint, and structure review checkpoints.",
        details=("Suggested checks: tests, linting, imports, error paths.",),
        metadata={"domain": "code"},
    )
    seeds.append(knowledge_seed_from_tool_result(tool_result, tool_source))

    results = [validator.validate(seed) for seed in seeds]
    counts = Counter(result.status for result in results)

    print("Growth Lab KnowledgeSeed demo")
    print("Deterministic validation only; no real AI, web, tools, or training.")
    print()
    print(f"Total seeds: {len(seeds)}")
    for status in ("validated", "weak", "quarantined", "rejected"):
        print(f"{status}: {counts.get(status, 0)}")

    for seed in seeds:
        print_result(seed, validator)


if __name__ == "__main__":
    main()
