"""Run a deterministic TrainingDataExporter example."""

from grona import TrainingDataExporter
from grona.training_cli import create_training_export_demo_seeds


def main() -> None:
    """Print deterministic in-memory training export previews."""
    exporter = TrainingDataExporter()
    examples = exporter.from_knowledge_seeds(create_training_export_demo_seeds())
    dataset = exporter.build_dataset(
        name="example-training-export",
        description="Example Grona-native and Alpaca-like training export preview.",
        examples=examples,
        created_at="2026-01-01T00:00:00+00:00",
        metadata={"example": True, "writes_files": False},
    )

    print(dataset.to_text())
    print("\nGrona-native JSONL:")
    print(dataset.to_native_jsonl(exporter.config.include_metadata))
    print("\nAlpaca-like JSONL:")
    print(dataset.to_alpaca_jsonl())


if __name__ == "__main__":
    main()
