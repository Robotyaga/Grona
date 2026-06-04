"""CLI demo for manifest-aware JSONL dataset ingestion."""

from __future__ import annotations

from collections.abc import Sequence

from .dataset_manifest import DatasetIngestor, DatasetManifest

DEMO_JSONL = "\n".join(
    (
        '{"instruction":"Explain safe dataset ingestion.",'
        '"input":"A small JSONL corpus.",'
        '"output":"Keep provenance, license, and review metadata visible."}',
        '{"conversations":['
        '{"from":"human","value":"How should dataset rows become knowledge?"},'
        '{"from":"gpt","value":"Only as candidates with source metadata and review."}'
        "]}",
        '{"text":"Generic dataset text should preserve manifest provenance before '
        'becoming a seed candidate."}',
        '{"input":"broken row without text or output"}',
    )
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the deterministic JSONL dataset ingestion demo."""
    _ = argv
    print(format_jsonl_dataset_demo())
    return 0


def format_jsonl_dataset_demo() -> str:
    """Return deterministic demo output for manifest-aware JSONL ingestion."""
    manifest = create_demo_manifest()
    ingestor = DatasetIngestor()
    samples, report = ingestor.ingest_jsonl_text(manifest, DEMO_JSONL)
    sample_lines = [
        f"- {sample.id}: type={sample.sample_type}, domains={','.join(sample.domains) or 'none'}"
        for sample in samples
    ]
    return "\n".join(
        (
            "JSONL dataset ingestion demo",
            "Execution: deterministic offline JSONL text only; no downloads or file writes.",
            "",
            report.to_text(),
            "",
            "Normalized samples:",
            *(sample_lines or ["- none"]),
        )
    )


def create_demo_manifest() -> DatasetManifest:
    """Create a deterministic manifest for the JSONL ingestion demo."""
    return DatasetManifest(
        name="jsonl-demo-corpus",
        description="Tiny in-memory JSONL corpus for manifest-aware ingestion demos.",
        source="in-memory-demo-jsonl",
        format="jsonl",
        license="MIT-demo",
        allowed_uses=("knowledge_seed_candidate", "benchmark_candidate"),
        domains=("documents", "general"),
        capabilities=("dataset_ingestion", "knowledge_seed_candidate"),
        requires_review=True,
        metadata={"demo_only": True, "language": "en", "reliability": 0.72},
    )
