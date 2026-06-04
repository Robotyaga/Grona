"""Readable example for deterministic dataset quality review."""

from __future__ import annotations

from grona.dataset_review_cli import DEMO_JSONL, create_review_demo_manifest
from grona import DatasetIngestor, DatasetQualityReviewer, DatasetReviewConfig


def main() -> None:
    """Run manifest-aware ingestion, quality review, and candidate seed preview."""
    manifest = create_review_demo_manifest()
    samples, ingestion_report = DatasetIngestor().ingest_jsonl_text(manifest, DEMO_JSONL)
    reviewer = DatasetQualityReviewer(DatasetReviewConfig(human_review_threshold=0.55))
    reviews, review_report = reviewer.review_samples(samples, manifest)
    seeds = reviewer.accepted_knowledge_seed_candidates(samples, reviews)

    print(ingestion_report.to_text())
    print()
    print(review_report.to_text())
    print()
    print("Accepted raw KnowledgeSeed candidates:")
    for seed in seeds:
        print(f"- {seed.id}: confidence={seed.confidence:.2f}")


if __name__ == "__main__":
    main()
