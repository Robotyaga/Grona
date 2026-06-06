"""CLI demo for model-build readiness and local handoff planning."""

from __future__ import annotations

from collections.abc import Sequence

from .model_build_readiness import (
    build_demo_model_build_readiness_report,
    create_missing_dependencies_demo_environment,
    model_build_lifecycle_markdown,
)
from .model_build_readiness import TrainingEnvironmentAuditor, TrainingHardwareRequirement


def main(argv: Sequence[str] | None = None) -> int:
    """Print deterministic model-build readiness demo output."""
    _ = argv
    print(format_model_build_readiness_demo())
    return 0


def format_model_build_readiness_demo() -> str:
    """Return deterministic model-build readiness demo output."""
    report = build_demo_model_build_readiness_report()
    qlora_environment = create_missing_dependencies_demo_environment()
    qlora_requirement = TrainingHardwareRequirement.small_qlora()
    qlora_report = TrainingEnvironmentAuditor().audit(qlora_environment, qlora_requirement)
    lines = [
        "Model build readiness demo",
        "Execution: readiness audit only; no model loading, no training, no files, no APIs, no subprocesses.",
        "",
        "Consolidated readiness:",
        report.to_text(),
        "",
        "Artifact summary:",
        compact_mapping(report.artifact_bundle_summary),
        "",
        "Training plan validation:",
        compact_mapping(report.training_plan_validation),
        "",
        "Environment readiness example for missing QLoRA dependencies:",
        qlora_report.to_text(),
        "",
        "Local handoff checklist:",
        report.handoff_manifest.to_markdown(),
        "",
        "Lifecycle summary:",
        model_build_lifecycle_markdown(),
        "",
        "Real training status:",
        "not executed, not implemented, blocked by default",
    ]
    return "\n".join(lines)


def compact_mapping(data: object) -> str:
    """Return readable key/value lines for compact demo sections."""
    if not isinstance(data, dict) or not data:
        return "- none"
    return "\n".join(f"- {key}: {value}" for key, value in data.items())
