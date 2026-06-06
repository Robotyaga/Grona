"""CLI demo for the training pipeline readiness audit layer."""

from __future__ import annotations

from collections.abc import Sequence

from .experimental_training import ExperimentalLoRABackend, LoRATrainingSafetyConfig
from .training_pipeline_audit import (
    TrainingPipelineAuditor,
    TrainingPipelineContract,
    build_demo_training_pipeline_audit_inputs,
    training_lifecycle_markdown,
    validate_training_backend_contract,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Print the deterministic training pipeline audit demo."""
    _ = argv
    print(format_training_pipeline_audit_demo())
    return 0


def format_training_pipeline_audit_demo() -> str:
    """Return deterministic demo output for training pipeline readiness audit."""
    examples, package, plan, bundle = build_demo_training_pipeline_audit_inputs()
    backend = ExperimentalLoRABackend()
    safety = LoRATrainingSafetyConfig()
    auditor = TrainingPipelineAuditor()
    report = auditor.audit(examples, package, bundle, plan, backend, safety)
    backend_contract = validate_training_backend_contract(backend, plan, bundle)
    contract = TrainingPipelineContract()

    lines = [
        "Training pipeline audit demo",
        "Execution: audit only; no model loading, no training, no files, no APIs, no subprocesses.",
        "",
        "Pipeline readiness report:",
        report.to_text(),
        "",
        "Backend contract validation:",
        backend_contract.to_text(),
        "",
        "Training pipeline contract:",
        contract.to_text(),
        "",
        "Lifecycle summary:",
        training_lifecycle_markdown(),
        "",
        "Real training status:",
        "not executed, not implemented, blocked by default",
    ]
    return "\n".join(lines)
