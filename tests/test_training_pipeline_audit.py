import sys

from grona import (
    ExperimentalLoRABackend,
    LoRATrainingSafetyConfig,
    TrainingArtifactBundle,
    TrainingPipelineAuditor,
    TrainingPipelineContract,
    TrainingPipelineReadinessReport,
    TrainingPipelineStageStatus,
    TrainingSplitConfig,
    build_demo_training_pipeline_audit_inputs,
    build_training_dataset_package,
    create_default_training_backend_registry,
    create_demo_training_plan_examples,
    training_lifecycle_markdown,
    validate_training_backend_contract,
)
from grona.entrypoint import main
from grona.training_artifacts import TrainingArtifactBuilder
from grona.training_dry_run import build_demo_training_dry_run_inputs
from grona.training_plan import build_demo_training_plan


HEAVY_MODULES = {"torch", "transformers", "peft", "bitsandbytes", "datasets", "accelerate"}


def test_training_pipeline_readiness_report_creation() -> None:
    stage = TrainingPipelineStageStatus("execution", "passed", ("blocked by default",))
    report = TrainingPipelineReadinessReport(
        ready=False,
        stage_statuses=(stage,),
        warnings=("demo warning",),
        blockers=("demo blocker",),
        metadata={"unit": True},
    )

    data = report.to_dict()

    assert data["ready"] is False
    assert data["stage_statuses"][0]["stage"] == "execution"
    assert report.stage("execution") == stage
    assert "demo blocker" in report.to_text()


def test_training_pipeline_contract_creation_and_serialization() -> None:
    contract = TrainingPipelineContract()
    data = contract.to_dict()

    assert "TrainingPlan" in data["required_inputs"]
    assert "data/train.jsonl" in data["required_artifact_paths"]
    assert "model training" in data["forbidden_default_behavior"]
    assert "Training pipeline contract" in contract.to_text()
    assert "future_real_training_requirements" in contract.to_json()


def test_training_pipeline_auditor_complete_demo_pipeline_is_blocked_only_by_future_execution() -> None:
    examples, package, plan, bundle = build_demo_training_pipeline_audit_inputs()
    backend = create_default_training_backend_registry().get("dry-run")
    report = TrainingPipelineAuditor().audit(examples, package, bundle, plan, backend, LoRATrainingSafetyConfig())

    assert report.ready is False
    assert report.stage("training_dataset_package").status == "passed"
    assert report.stage("training_artifacts").status == "passed"
    assert report.stage("training_plan").status == "passed"
    assert report.stage("execution").status == "passed"
    assert report.stage("backend").status == "blocked"
    assert any("backend readiness claims ready" in blocker for blocker in report.blockers)


def test_auditor_blocks_missing_train_split() -> None:
    examples = create_demo_training_plan_examples()
    package = build_training_dataset_package(
        examples,
        split_config=TrainingSplitConfig(train_ratio=0, validation_ratio=1, test_ratio=0, min_examples_per_split=0),
    )
    plan = build_demo_training_plan(package)
    bundle = TrainingArtifactBuilder().build(package, plan)
    report = TrainingPipelineAuditor().audit(examples, package, bundle, plan, None, LoRATrainingSafetyConfig())

    assert report.stage("training_dataset_package").status == "blocked"
    assert any("no train examples" in blocker for blocker in report.blockers)


def test_auditor_blocks_missing_required_artifact() -> None:
    examples, package, plan, bundle = build_demo_training_pipeline_audit_inputs()
    reduced_bundle = TrainingArtifactBundle(
        "missing-artifact-bundle",
        tuple(artifact for artifact in bundle.artifacts if artifact.path != "docs/model_card.md"),
    )

    report = TrainingPipelineAuditor().audit(examples, package, reduced_bundle, plan, None, LoRATrainingSafetyConfig())

    assert report.stage("training_artifacts").status == "blocked"
    assert any("docs/model_card.md" in blocker for blocker in report.blockers)


def test_auditor_warns_on_missing_validation_and_test_splits_for_tiny_dataset() -> None:
    examples = create_demo_training_plan_examples()[:1]
    package = build_training_dataset_package(
        examples,
        split_config=TrainingSplitConfig(train_ratio=1, validation_ratio=0, test_ratio=0, min_examples_per_split=0),
    )
    plan = build_demo_training_plan(package)
    bundle = TrainingArtifactBuilder().build(package, plan)
    report = TrainingPipelineAuditor().audit(examples, package, bundle, plan, None, LoRATrainingSafetyConfig())

    assert report.stage("training_dataset_package").status == "warning"
    assert any("validation split is empty" in warning for warning in report.warnings)
    assert any("test split is empty" in warning for warning in report.warnings)


def test_auditor_detects_unsupported_backend_adapter_type() -> None:
    _package, qlora_plan, qlora_bundle = build_demo_training_dry_run_inputs()
    backend = ExperimentalLoRABackend(dependency_finder=lambda _package: None)
    report = TrainingPipelineAuditor().audit((), None, qlora_bundle, qlora_plan, backend, LoRATrainingSafetyConfig())

    assert report.stage("backend").status == "blocked"
    assert any("rejects the training plan adapter config" in blocker for blocker in report.blockers)


def test_auditor_confirms_execution_blocked_by_default() -> None:
    report = TrainingPipelineAuditor().audit(safety_config=LoRATrainingSafetyConfig())

    assert report.stage("execution").status == "passed"
    assert "training execution remains blocked by default" in report.stage("execution").reasons


def test_auditor_checks_provenance_and_license_metadata_presence() -> None:
    examples, package, plan, bundle = build_demo_training_pipeline_audit_inputs()
    report = TrainingPipelineAuditor().audit(examples, package, bundle, plan, None, LoRATrainingSafetyConfig())

    assert report.stage("provenance").status == "passed"
    assert report.stage("license").status == "passed"


def test_validate_training_backend_contract_works_for_placeholder_backend() -> None:
    _package, plan, bundle = build_demo_training_pipeline_audit_inputs()
    backend = create_default_training_backend_registry().get("lora-cli-placeholder")

    status = validate_training_backend_contract(backend, plan, bundle)

    assert status.stage == "backend"
    assert status.status == "blocked"
    assert any("readiness" in key for key in status.metadata)


def test_validate_training_backend_contract_works_for_experimental_lora_backend_default_path() -> None:
    _package, plan, bundle = build_demo_training_pipeline_audit_inputs()
    backend = ExperimentalLoRABackend(dependency_finder=lambda _package: None)

    status = validate_training_backend_contract(backend, plan, bundle)

    assert status.stage == "backend"
    assert status.status == "blocked"
    assert status.metadata["supports_training_plan"] is True
    assert any("missing optional LoRA dependency" in reason for reason in status.reasons)


def test_training_lifecycle_markdown_is_deterministic() -> None:
    text = training_lifecycle_markdown()

    assert "reviewed traces -> examples -> dataset package" in text
    assert "future real training remains blocked" in text


def test_cli_training_pipeline_audit_demo_behavior(capsys) -> None:
    assert main(["--training-pipeline-audit-demo"]) == 0

    output = capsys.readouterr().out
    assert "Training pipeline audit demo" in output
    assert "Pipeline readiness report" in output
    assert "Training pipeline contract" in output
    assert "not executed, not implemented" in output


def test_normal_import_still_does_not_require_heavy_ml_dependencies() -> None:
    assert HEAVY_MODULES.isdisjoint(sys.modules)
