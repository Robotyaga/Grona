from collections import Counter

from grona import (
    DocumentChunk,
    KnowledgeSeed,
    KnowledgeSource,
    KnowledgeValidator,
    ToolResult,
    ValidationResult,
    create_demo_knowledge_seeds,
    knowledge_seed_from_document_chunk,
    knowledge_seed_from_tool_result,
)
from grona.cli import main


def test_knowledge_source_creation() -> None:
    source = KnowledgeSource(
        id="source:test",
        source_type="user_note",
        name="Test source",
        reliability=0.8,
        metadata={"kind": "unit"},
    )

    assert source.id == "source:test"
    assert source.source_type == "user_note"
    assert source.reliability == 0.8
    assert source.metadata == {"kind": "unit"}


def test_knowledge_seed_creation() -> None:
    source = KnowledgeSource("source:test", "document", "Test source", 0.8)
    seed = KnowledgeSeed(
        id="seed:test",
        content=(
            "Document chunk notes about code review, tests, linting, "
            "and public API boundaries."
        ),
        source=source,
        domains=("code",),
        keywords=("code", "tests", "lint"),
        confidence=0.75,
    )

    assert seed.id == "seed:test"
    assert seed.source == source
    assert seed.domains == ("code",)
    assert seed.status == "new"


def test_validation_result_formatting() -> None:
    result = ValidationResult(
        seed_id="seed:test",
        accepted=True,
        status="weak",
        score=0.61,
        reasons=("usable with caution",),
        warnings=("source reliability is low",),
    )

    text = result.to_text()

    assert "Seed: seed:test" in text
    assert "Status: weak" in text
    assert "Warnings:" in text


def test_validator_accepts_strong_seed() -> None:
    source = KnowledgeSource("source:strong", "user_note", "Strong source", 0.95)
    seed = KnowledgeSeed(
        id="seed:strong",
        content=(
            "Engine overheating triage should check coolant level, radiator flow, "
            "thermostat behavior, fan activation, leaks, and air pockets."
        ),
        source=source,
        domains=("automotive",),
        keywords=("engine", "overheating", "coolant", "radiator"),
        confidence=0.9,
    )

    result = KnowledgeValidator().validate(seed)

    assert result.accepted is True
    assert result.status == "validated"


def test_validator_rejects_empty_seed() -> None:
    source = KnowledgeSource("source:empty", "unknown", "Unknown", 0.3)
    seed = KnowledgeSeed(
        id="seed:empty",
        content="",
        source=source,
        domains=("general",),
        keywords=("empty",),
        confidence=0.2,
    )

    result = KnowledgeValidator().validate(seed)

    assert result.accepted is False
    assert result.status == "rejected"
    assert "content is empty" in result.reasons


def test_validator_weakens_low_reliability_source() -> None:
    source = KnowledgeSource("source:weak", "donor_model", "Weak donor", 0.3)
    seed = KnowledgeSeed(
        id="seed:weak-source",
        content=(
            "Media workflow notes should inspect codec selection, audio sync, color workflow, "
            "stabilization, export settings, and render constraints."
        ),
        source=source,
        domains=("media",),
        keywords=("media", "codec", "audio", "render"),
        confidence=0.9,
    )

    result = KnowledgeValidator().validate(seed)

    assert result.accepted is True
    assert result.status == "weak"
    assert "source reliability is low" in result.warnings


def test_validator_quarantines_low_confidence_seed() -> None:
    source = KnowledgeSource("source:feedback", "feedback", "Feedback", 0.7)
    seed = KnowledgeSeed(
        id="seed:low-confidence",
        content="Benchmark observation says routing changed, but evidence is incomplete.",
        source=source,
        domains=("general",),
        keywords=("benchmark", "routing"),
        confidence=0.2,
    )

    result = KnowledgeValidator().validate(seed)

    assert result.accepted is False
    assert result.status == "quarantined"
    assert "seed confidence is low" in result.warnings


def test_validator_warns_about_missing_domains_and_keywords() -> None:
    source = KnowledgeSource("source:missing", "user_note", "Missing metadata", 0.8)
    seed = KnowledgeSeed(
        id="seed:missing",
        content="Document notes should keep citations and retrieval behavior visible in traces.",
        source=source,
        domains=(),
        keywords=(),
        confidence=0.8,
    )

    result = KnowledgeValidator().validate(seed)

    assert result.accepted is True
    assert result.status == "weak"
    assert "domains are missing" in result.warnings
    assert "keywords are missing" in result.warnings


def test_document_chunk_to_seed_conversion() -> None:
    source = KnowledgeSource("source:doc", "document", "Document source", 0.82)
    chunk = DocumentChunk(
        id="doc:chunk-0001",
        source_id="doc",
        content="Code review chunk about tests, lint output, imports, and public API boundaries.",
        index=1,
        domains=("code",),
        keywords=("code", "tests", "lint"),
        metadata={"source_title": "Code notes"},
    )

    seed = knowledge_seed_from_document_chunk(chunk, source)

    assert seed.id == "seed:doc:chunk-0001"
    assert seed.content == chunk.content
    assert seed.domains == chunk.domains
    assert seed.metadata["origin"] == "document_chunk"
    assert seed.metadata["chunk_index"] == 1


def test_tool_result_to_seed_conversion() -> None:
    source = KnowledgeSource("source:tool", "tool_result", "Mock tool", 0.72)
    result = ToolResult(
        tool_name="mock_code_inspector",
        success=True,
        output="Mock code inspector found test, lint, and structure review checkpoints.",
        details=("Suggested checks: tests, linting, imports, error paths.",),
        metadata={"domain": "code"},
    )

    seed = knowledge_seed_from_tool_result(result, source)

    assert seed.id == "seed:tool:mock_code_inspector"
    assert seed.domains == ("code",)
    assert "inspector" in seed.keywords
    assert seed.metadata["origin"] == "tool_result"


def test_demo_seeds_produce_deterministic_validation_counts() -> None:
    validator = KnowledgeValidator()
    results = [validator.validate(seed) for seed in create_demo_knowledge_seeds()]
    counts = Counter(result.status for result in results)

    assert counts == {"validated": 3, "weak": 2, "quarantined": 2, "rejected": 1}


def test_cli_growth_demo_behavior(capsys) -> None:
    assert main(["--growth-demo"]) == 0

    output = capsys.readouterr().out
    assert "Growth Lab demo: KnowledgeSeed validation" in output
    assert "validated: 3" in output
    assert "weak: 2" in output
    assert "quarantined: 2" in output
    assert "rejected: 1" in output
