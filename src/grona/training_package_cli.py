"""CLI demo for deterministic training dataset packages."""

from __future__ import annotations

from collections.abc import Sequence

from .training import TrainingExample
from .training_package import (
    DatasetCardDraft,
    TrainingSplitConfig,
    build_training_dataset_package,
)

DEMO_CREATED_AT = "2026-01-01T00:00:00+00:00"


def main(argv: Sequence[str] | None = None) -> int:
    """Print the deterministic training package demo."""
    _ = argv
    print(format_training_package_demo())
    return 0


def format_training_package_demo() -> str:
    """Return deterministic demo output for split/package/manifest behavior."""
    package = build_training_dataset_package(
        create_training_package_demo_examples(),
        split_config=TrainingSplitConfig(stratify_by_domain=True),
        dataset_name="demo-training-dataset-package",
        description="Deterministic split and manifest package for reviewed Grona traces.",
        created_at=DEMO_CREATED_AT,
        metadata={"demo": "training_package", "writes_files": False, "calls_models": False},
    )
    card = DatasetCardDraft.from_package(package)
    native_preview = first_non_empty_preview(package.native_jsonl_by_split(), limit=1)
    alpaca_preview = first_non_empty_preview(package.alpaca_jsonl_by_split(), limit=1)
    return "\n".join(
        (
            "Training dataset package demo",
            "Execution: deterministic offline package only; no model calls, files, APIs, or training.",
            "",
            package.manifest.to_text(),
            "",
            "Split summaries:",
            *(split.to_text() for split in package.splits),
            "",
            "Grona-native JSONL preview by split:",
            native_preview or "none",
            "",
            "Alpaca-like JSONL preview by split:",
            alpaca_preview or "none",
            "",
            "Dataset card draft preview:",
            card.to_markdown(),
        )
    )


def create_training_package_demo_examples() -> tuple[TrainingExample, ...]:
    """Create deterministic reviewed examples for the package demo."""
    domains = ("routing", "documents", "safety")
    capabilities = ("route_trace", "context_review", "safety_review")
    examples: list[TrainingExample] = []
    for index in range(12):
        domain = domains[index % len(domains)]
        capability = capabilities[index % len(capabilities)]
        examples.append(
            TrainingExample(
                instruction=f"Preserve reviewed {domain} trace {index}.",
                input=f"Task {index} for {domain} review.",
                output=f"Reviewed {domain} output {index} keeps provenance and limits explicit.",
                source="reviewed_inference_trace",
                domains=(domain,),
                capabilities=(capability,),
                provenance={
                    "origin": "reviewed_inference_trace",
                    "trace_id": f"trace:package:{index:02d}",
                    "review_id": f"review:package:{index:02d}",
                },
                license="demo-only",
                validation_status="reviewed",
                metadata={"demo_index": index, "writes_files": False},
            )
        )
    return tuple(examples)


def first_non_empty_preview(jsonl_by_split: dict[str, str], limit: int) -> str:
    """Return first JSONL rows from each populated split."""
    lines: list[str] = []
    for split_name, jsonl in jsonl_by_split.items():
        rows = [row for index, row in enumerate(jsonl.splitlines()) if index < limit]
        if rows:
            lines.append(f"[{split_name}]")
            lines.extend(rows)
    return "\n".join(lines)
