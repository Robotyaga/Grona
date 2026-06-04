from json import loads

from grona import (
    BenchmarkCase,
    BenchmarkResult,
    FeedbackRecord,
    KnowledgeSeed,
    KnowledgeSource,
    SeedReviewDecision,
    TrainingDataExporter,
    TrainingDataset,
    TrainingExample,
    TrainingExportConfig,
)
from grona.entrypoint import main


def test_training_example_creation() -> None:
    example = TrainingExample(
        instruction="Explain routing trace.",
        input="task text",
        output="selected module summary",
        source="test",
        domains=("routing",),
        capabilities=("route_trace",),
        provenance={"origin": "unit-test"},
        license="MIT",
        validation_status="validated",
        metadata={"score": 1.0},
    )

    assert example.instruction == "Explain routing trace."
    assert example.domains == ("routing",)
    assert example.to_alpaca_record() == {
        "instruction": "Explain routing trace.",
        "input": "task text",
        "output": "selected module summary",
    }
    assert example.to_native_record()["provenance"] == {"origin": "unit-test"}


def test_training_dataset_summary() -> None:
    dataset = TrainingDataset(
        "demo",
        "Demo dataset.",
        (
            demo_example("b", source="feedback", status="reviewed"),
            demo_example("a", source="knowledge", status="validated"),
        ),
        created_at="2026-01-01T00:00:00+00:00",
    )

    text = dataset.to_text()

    assert dataset.count() == 2
    assert dataset.domains() == ("routing",)
    assert dataset.sources() == ("feedback", "knowledge")
    assert dataset.validation_status_counts() == {"reviewed": 1, "validated": 1}
    assert "Training dataset: demo" in text
    assert "Examples: 2" in text


def test_exporter_from_validated_knowledge_seed() -> None:
    exporter = TrainingDataExporter()
    seed = demo_seed("seed:validated", status="validated")

    example = exporter.from_knowledge_seed(seed)

    assert example is not None
    assert example.output == seed.content
    assert example.validation_status == "validated"
    assert example.provenance["seed_id"] == "seed:validated"
    assert example.license == "demo-license"


def test_rejected_and_raw_examples_are_skipped_by_default() -> None:
    exporter = TrainingDataExporter()

    raw = exporter.from_knowledge_seed(demo_seed("seed:raw", status="new"))
    rejected = exporter.from_knowledge_seed(demo_seed("seed:rejected", status="rejected"))

    assert raw is None
    assert rejected is None


def test_config_allows_synthetic_demo_examples() -> None:
    exporter = TrainingDataExporter(TrainingExportConfig(allow_synthetic_demo=True))
    case = BenchmarkCase("case:demo", "Route a demo task.", expected_domains=("routing",))
    result = BenchmarkResult(
        "case:demo",
        "baseline",
        selected_modules=("general-reasoning",),
        selected_domains=("general",),
        routing_score=0.5,
        context_score=0.5,
        growth_score=0.0,
    )

    example = exporter.from_benchmark_result(case, result)

    assert example is not None
    assert example.validation_status == "synthetic_demo"
    assert example.source == "benchmark"


def test_native_jsonl_export_preserves_metadata() -> None:
    dataset = TrainingDataset(
        "demo",
        "Demo dataset.",
        (demo_example("a", metadata={"seed_id": "seed:a"}),),
    )

    row = loads(dataset.to_native_jsonl())

    assert row["metadata"]["seed_id"] == "seed:a"
    assert row["provenance"]["origin"] == "unit-test"
    assert row["validation_status"] == "validated"


def test_alpaca_export_contains_instruction_input_output_only() -> None:
    dataset = TrainingDataset("demo", "Demo dataset.", (demo_example("a"),))

    row = loads(dataset.to_alpaca_jsonl())

    assert set(row) == {"instruction", "input", "output"}
    assert row["instruction"] == "Instruction a"


def test_deterministic_output_ordering() -> None:
    dataset = TrainingDataset(
        "demo",
        "Demo dataset.",
        (
            demo_example("z", source="z-source"),
            demo_example("a", source="a-source"),
        ),
    )

    rows = [loads(line) for line in dataset.to_native_jsonl().splitlines()]

    assert [row["source"] for row in rows] == ["a-source", "z-source"]


def test_review_decision_exports_only_promote_candidates_by_default() -> None:
    exporter = TrainingDataExporter()
    seeds = (
        demo_seed("seed:promote", status="new"),
        demo_seed("seed:reject", status="new"),
    )
    decisions = (
        SeedReviewDecision(
            "seed:promote",
            "promote_candidate",
            recommended_status="validated",
        ),
        SeedReviewDecision(
            "seed:reject",
            "reject_broken",
            recommended_status="rejected",
        ),
    )

    examples = exporter.from_review_decisions(seeds, decisions)

    assert len(examples) == 1
    assert examples[0].metadata["review_decision"] == "promote_candidate"


def test_positive_feedback_record_exports_as_reviewed() -> None:
    exporter = TrainingDataExporter()
    record = FeedbackRecord(
        task="Route this task.",
        selected_modules=("general-reasoning",),
        skipped_modules=(),
        confidence=0.9,
        route_summary="Selected: general-reasoning. Skipped: none.",
        timestamp="2026-01-01T00:00:00+00:00",
        rating=5,
        success=True,
    )

    example = exporter.from_feedback_record(record)

    assert example is not None
    assert example.validation_status == "reviewed"
    assert example.capabilities == ("routing", "feedback_analysis")


def test_cli_training_export_demo_behavior(capsys) -> None:
    assert main(["--training-export-demo"]) == 0

    output = capsys.readouterr().out
    assert "TrainingDataExporter demo" in output
    assert "deterministic offline export only" in output
    assert "Grona-native JSONL preview" in output
    assert "Alpaca-like JSONL preview" in output
    assert "Examples: 2" in output


def demo_seed(id: str, status: str) -> KnowledgeSeed:
    source = KnowledgeSource(
        "source:demo",
        "user_note",
        "Demo source",
        0.9,
        metadata={"license": "demo-license"},
    )
    return KnowledgeSeed(
        id=id,
        content="Validated routing knowledge should preserve provenance and review status.",
        source=source,
        domains=("routing",),
        keywords=("routing", "provenance"),
        confidence=0.9,
        status=status,
        metadata={"license": "demo-license"},
    )


def demo_example(
    suffix: str,
    source: str = "knowledge",
    status: str = "validated",
    metadata: dict[str, object] | None = None,
) -> TrainingExample:
    return TrainingExample(
        instruction=f"Instruction {suffix}",
        input=f"Input {suffix}",
        output=f"Output {suffix}",
        source=source,
        domains=("routing",),
        capabilities=("route_trace",),
        provenance={"origin": "unit-test"},
        license="demo-license",
        validation_status=status,
        metadata=metadata or {},
    )
