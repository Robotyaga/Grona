import pytest

from grona import (
    DatasetIngestor,
    DatasetLicensePolicy,
    DatasetManifest,
    JsonlDatasetRecord,
    read_jsonl_records,
)
from grona.entrypoint import main


def test_dataset_manifest_creation() -> None:
    manifest = demo_manifest()

    assert manifest.name == "demo-jsonl"
    assert manifest.format == "jsonl"
    assert manifest.license == "MIT"
    assert manifest.allowed_uses == ("knowledge_seed_candidate", "training_export_candidate")
    assert manifest.requires_review is True


def test_dataset_license_policy_allows_and_rejects_uses() -> None:
    policy = DatasetLicensePolicy()
    manifest = demo_manifest()
    unsafe = DatasetManifest(
        "unsafe-jsonl",
        "Unsafe manifest.",
        "memory",
        license="unknown",
        allowed_uses=("training_export_candidate",),
    )

    assert policy.can_create_knowledge_seed_candidates(manifest) is True
    assert policy.can_create_training_export_candidates(manifest) is True
    assert policy.review_required(manifest) is True
    assert policy.can_create_knowledge_seed_candidates(unsafe) is False
    assert policy.can_create_training_export_candidates(unsafe) is False
    decision = policy.decision_for_use(unsafe, "training_export_candidate")
    assert decision.allowed is False
    assert "license" in decision.reason


def test_jsonl_parser_valid_records() -> None:
    records = read_jsonl_records('{"text":"one"}\n{"text":"two"}')

    assert len(records) == 2
    assert records[0].data["text"] == "one"
    assert records[1].data["text"] == "two"


def test_jsonl_parser_invalid_record_behavior() -> None:
    with pytest.raises(ValueError, match="line 2"):
        read_jsonl_records('{"text":"one"}\nnot-json')

    records = read_jsonl_records('{"text":"one"}\nnot-json', strict=False)
    assert len(records) == 1


def test_jsonl_parser_skips_empty_lines_and_preserves_line_numbers() -> None:
    records = read_jsonl_records('\n{"text":"one"}\n\n{"text":"two"}')

    assert [record.line_number for record in records] == [2, 4]


def test_alpaca_like_normalization() -> None:
    records = read_jsonl_records(
        '{"instruction":"Explain routing.","input":"A task.","output":"Use visible traces."}'
    )
    samples, report = DatasetIngestor().ingest_records(demo_manifest(), records)

    assert len(samples) == 1
    assert samples[0].sample_type in {"instruction", "reasoning"}
    assert "Instruction:" in samples[0].content
    assert samples[0].metadata["manifest_name"] == "demo-jsonl"
    assert report.records_accepted == 1


def test_sharegpt_like_normalization() -> None:
    text = (
        '{"conversations":['
        '{"from":"human","value":"How should I review data?"},'
        '{"from":"gpt","value":"Check license and provenance."}'
        ']}'
    )
    samples, report = DatasetIngestor().ingest_jsonl_text(demo_manifest(), text)

    assert len(samples) == 1
    assert samples[0].sample_type in {"conversation", "factual_qa", "reasoning"}
    assert "user:" in samples[0].content
    assert "assistant:" in samples[0].content
    assert report.normalized_sample_count == 1


def test_generic_text_normalization() -> None:
    samples, _ = DatasetIngestor().ingest_jsonl_text(
        demo_manifest(),
        '{"text":"Dataset rows should preserve manifest provenance."}',
    )

    assert len(samples) == 1
    assert samples[0].content == "Dataset rows should preserve manifest provenance."
    assert samples[0].metadata["line_number"] == 1
    assert samples[0].source.license == "MIT"


def test_manifest_provenance_attached() -> None:
    samples, _ = DatasetIngestor().ingest_jsonl_text(
        demo_manifest(),
        '{"text":"Provenance must stay visible."}',
    )

    sample = samples[0]
    assert sample.metadata["manifest_source"] == "in-memory-test"
    assert sample.metadata["manifest_license"] == "MIT"
    assert sample.metadata["manifest_requires_review"] is True
    assert sample.source.metadata["allowed_uses"] == [
        "knowledge_seed_candidate",
        "training_export_candidate",
    ]


def test_dataset_ingestion_report_counts() -> None:
    samples, report = DatasetIngestor().ingest_jsonl_text(
        demo_manifest(),
        '{"text":"Accepted text."}\n{"input":"broken"}',
    )

    assert len(samples) == 1
    assert report.records_read == 2
    assert report.records_accepted == 1
    assert report.records_rejected == 1
    assert report.normalized_sample_count == 1
    assert "unsupported or incomplete" in report.rejection_reasons[0]
    assert "Dataset ingestion report" in report.to_text()


def test_conservative_policy_rejects_unsafe_training_use_by_default() -> None:
    manifest = DatasetManifest(
        "unsafe-training",
        "Unknown license should not be training-safe.",
        "memory",
        license="unknown",
        allowed_uses=("training_export_candidate",),
    )
    policy = DatasetLicensePolicy()

    assert policy.can_create_training_export_candidates(manifest) is False
    assert policy.decision_for_use(manifest, "knowledge_seed_candidate").allowed is False


def test_knowledge_seed_candidates_require_manifest_use() -> None:
    manifest = DatasetManifest(
        "routing-only",
        "Routing eval only.",
        "memory",
        license="MIT",
        allowed_uses=("routing_eval",),
    )
    ingestor = DatasetIngestor()
    records = read_jsonl_records('{"text":"This row should normalize but not become a seed."}')

    seeds, report = ingestor.knowledge_seed_candidates(manifest, records)

    assert seeds == ()
    assert report.records_accepted == 1


def test_cli_jsonl_dataset_demo_behavior(capsys) -> None:
    assert main(["--jsonl-dataset-demo"]) == 0

    output = capsys.readouterr().out
    assert "JSONL dataset ingestion demo" in output
    assert "deterministic offline JSONL text only" in output
    assert "Dataset ingestion report" in output
    assert "Normalized samples:" in output


def test_jsonl_record_creation() -> None:
    record = JsonlDatasetRecord(3, {"text": "hello"}, {"source": "unit-test"})

    assert record.line_number == 3
    assert record.data["text"] == "hello"
    assert record.metadata["source"] == "unit-test"


def demo_manifest() -> DatasetManifest:
    return DatasetManifest(
        name="demo-jsonl",
        description="A deterministic JSONL manifest for tests.",
        source="in-memory-test",
        format="jsonl",
        license="MIT",
        allowed_uses=("knowledge_seed_candidate", "training_export_candidate"),
        domains=("documents",),
        capabilities=("dataset_ingestion",),
        requires_review=True,
        metadata={"language": "en", "reliability": 0.8},
    )
