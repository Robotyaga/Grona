"""CLI demo for deterministic in-memory training data export."""

from __future__ import annotations

from collections.abc import Sequence

from .growth import KnowledgeSeed, KnowledgeSource
from .training import TrainingDataExporter

DEMO_CREATED_AT = "2026-01-01T00:00:00+00:00"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the deterministic training export demo."""
    _ = argv
    print(format_training_export_demo())
    return 0


def format_training_export_demo() -> str:
    """Return deterministic demo output for the training exporter."""
    exporter = TrainingDataExporter()
    examples = exporter.from_knowledge_seeds(create_training_export_demo_seeds())
    dataset = exporter.build_dataset(
        name="demo-training-export",
        description="Deterministic in-memory export of validated Grona knowledge seeds.",
        examples=examples,
        created_at=DEMO_CREATED_AT,
        metadata={"demo": True, "writes_files": False, "calls_models": False},
    )
    native_preview = first_lines(dataset.to_native_jsonl(exporter.config.include_metadata), 2)
    alpaca_preview = first_lines(dataset.to_alpaca_jsonl(), 2)
    return "\n".join(
        (
            "TrainingDataExporter demo",
            "Execution: deterministic offline export only; no model calls, downloads, or files.",
            "",
            dataset.to_text(),
            "",
            "Grona-native JSONL preview:",
            native_preview or "none",
            "",
            "Alpaca-like JSONL preview:",
            alpaca_preview or "none",
        )
    )


def create_training_export_demo_seeds() -> tuple[KnowledgeSeed, ...]:
    """Create deterministic validated and raw seeds for the export demo."""
    source = KnowledgeSource(
        id="source:training-demo",
        source_type="user_note",
        name="Training export demo notes",
        reliability=0.92,
        metadata={"license": "demo-only"},
    )
    donor_source = KnowledgeSource(
        id="source:training-demo-donor",
        source_type="donor_model",
        name="Unreviewed donor demo proposal",
        reliability=0.45,
        metadata={"license": "demo-only"},
    )
    return (
        KnowledgeSeed(
            id="seed:training-routing",
            content=(
                "Routing examples should preserve selected modules, skipped modules, "
                "confidence, and visible provenance before future training use."
            ),
            source=source,
            domains=("routing",),
            keywords=("routing", "modules", "confidence", "provenance"),
            confidence=0.9,
            status="validated",
            metadata={"reviewed_by": "demo"},
        ),
        KnowledgeSeed(
            id="seed:training-growth",
            content=(
                "Growth Lab export examples should keep validation status, source metadata, "
                "license information, and review decisions attached."
            ),
            source=source,
            domains=("growth",),
            keywords=("growth", "validation", "license", "review"),
            confidence=0.88,
            status="validated",
            metadata={"reviewed_by": "demo"},
        ),
        KnowledgeSeed(
            id="seed:raw-donor-skipped",
            content="Raw donor model output remains untrusted until review.",
            source=donor_source,
            domains=("general",),
            keywords=("donor", "review"),
            confidence=0.55,
            status="new",
            metadata={"origin": "donor_model_proposal"},
        ),
    )


def first_lines(text: str, limit: int) -> str:
    """Return the first JSONL lines for compact previews."""
    return "\n".join(line for index, line in enumerate(text.splitlines()) if index < limit)
