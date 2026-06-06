"""Deterministic example for the training pipeline readiness audit layer.

This example does not train a model, load a model, write files, call APIs,
execute subprocesses, or import heavy ML packages.
"""

from grona.experimental_training import ExperimentalLoRABackend, LoRATrainingSafetyConfig
from grona.training_pipeline_audit import (
    TrainingPipelineAuditor,
    TrainingPipelineContract,
    build_demo_training_pipeline_audit_inputs,
    training_lifecycle_markdown,
    validate_training_backend_contract,
)


def main() -> None:
    """Print audit report, backend contract validation, and contract summary."""
    examples, package, plan, bundle = build_demo_training_pipeline_audit_inputs()
    backend = ExperimentalLoRABackend()
    safety = LoRATrainingSafetyConfig()
    report = TrainingPipelineAuditor().audit(examples, package, bundle, plan, backend, safety)
    backend_contract = validate_training_backend_contract(backend, plan, bundle)

    print("Training pipeline audit example")
    print("Execution: audit only; no real training is performed.")
    print()
    print(report.to_text())
    print()
    print(backend_contract.to_text())
    print()
    print(TrainingPipelineContract().to_text())
    print()
    print(training_lifecycle_markdown())


if __name__ == "__main__":
    main()
