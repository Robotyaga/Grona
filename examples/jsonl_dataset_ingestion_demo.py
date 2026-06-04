"""Run a deterministic manifest-aware JSONL dataset ingestion example."""

from grona import DatasetIngestor
from grona.jsonl_dataset_cli import DEMO_JSONL, create_demo_manifest


def main() -> None:
    """Print manifest policy decisions, normalized samples, and report output."""
    manifest = create_demo_manifest()
    ingestor = DatasetIngestor()
    samples, report = ingestor.ingest_jsonl_text(manifest, DEMO_JSONL)

    print(report.to_text())
    print("\nNormalized samples:")
    for sample in samples:
        print(f"- {sample.id}")
        print(f"  type: {sample.sample_type}")
        print(f"  domains: {', '.join(sample.domains) or 'none'}")
        print(f"  source license: {sample.source.license}")
        print(f"  manifest: {sample.metadata.get('manifest_name')}")


if __name__ == "__main__":
    main()
