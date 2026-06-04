"""CLI demo for deterministic dataset quality review."""

from __future__ import annotations

from collections.abc import Sequence

from .dataset_manifest import DatasetIngestor, DatasetManifest
from .dataset_review import DatasetQualityReviewer, DatasetReviewConfig

DEMO_JSONL = "\n".join(
    (
        '{"instruction":"Explain dataset quality review for local ingestion.",'
        '"input":"A normalized JSONL sample is ready for review.",'
        '"output":"Check provenance, license, duplicates, minimum content quality, '
        'and suspicious markers before creating knowledge candidates."}',
        '{"instruction":"Summarize safe reviewed dataset promotion.",'
        '"input":"The sample passed deterministic checks.",'
        '"output":"Create only raw candidate seeds with review metadata and keep '
        'human validation separate from durable promotion."}',
        '{"instruction":"Explain dataset quality review for local ingestion.",'
        '"input":"A normalized JSONL sample is ready for review.",'
        '"output":"Check provenance, license, duplicates, minimum content quality, '
        'and suspicious markers before creating knowledge candidates."}',
        '{"text":"ok"}',
        '{"instruction":"Review suspicious data.",'
        '"input":"The row asks the model to ignore previous instructions.",'
        '"output":"This should need human review because prompt injection markers '
        'must not be trusted automatically."}',
        '{"input":"broken row without text or output"}',
    )
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the deterministic dataset review demo."""
    _ = argv
    print(format_dataset_review_demo())
    return 0


def format_dataset_review_demo() -> str:
    """Return deterministic demo output for dataset quality review."""
    manifest = create_review_demo_manifest()
    samples, ingestion_report = DatasetIngestor().ingest_jsonl_text(manifest, DEMO_JSONL)
    reviewer = DatasetQualityReviewer(DatasetReviewConfig(human_review_threshold=0.55))
    reviews, review_report = reviewer.review_samples(samples, manifest)
    seeds = reviewer.accepted_knowledge_seed_candidates(samples, reviews)
    review_lines = [f"- {review.to_text()}" for review in reviews]
    seed_lines = [
        f"- {seed.id}: status={seed.status}, confidence={seed.confidence:.2f}"
        for seed in seeds
    ]
    return "\n".join(
        (
            "Dataset quality review demo",
            "Execution: deterministic offline JSONL text only; no downloads or LLM calls.",
            "",
            ingestion_report.to_text(),
            "",
            review_report.to_text(),
            "",
            "Review decisions:",
            *(review_lines or ["- none"]),
            "",
            "Accepted KnowledgeSeed candidates:",
            *(seed_lines or ["- none"]),
        )
    )


def create_review_demo_manifest() -> DatasetManifest:
    """Create a deterministic manifest for the dataset review demo."""
    return DatasetManifest(
        name="dataset-review-demo-corpus",
        description="Tiny in-memory JSONL corpus for deterministic quality review demos.",
        source="in-memory-review-demo-jsonl",
        format="jsonl",
        license="MIT-demo",
        allowed_uses=("knowledge_seed_candidate", "benchmark_candidate"),
        domains=("documents", "general"),
        capabilities=("dataset_ingestion", "dataset_quality_review"),
        requires_review=True,
        metadata={"demo_only": True, "language": "en", "reliability": 0.74},
    )
