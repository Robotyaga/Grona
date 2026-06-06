from json import loads

from grona import (
    DryRunTrainer,
    DryRunTrainerConfig,
    TrainerBackendSpec,
    TrainingArtifactBundle,
    TrainingArtifactBuilder,
    TrainingExecutionPlan,
    TrainingReadinessReport,
    TrainingSplitConfig,
    build_demo_training_plan,
    build_training_dataset_package,
    create_dry_run_backend_spec,
    create_lora_cli_placeholder_backend_spec,
    create_qlora_cli_placeholder_backend_spec,
)
from grona.entrypoint import main
from grona.training_dry_run import (
    build_demo_training_dry_run_inputs,
    build_training_command_preview,
    command_preview_text,
)
from grona.training_plan import create_demo_training_plan_examples


def test_trainer_backend_spec_creation() -> None:
    backend = TrainerBackendSpec(
        "unit-backend",
        "custom_placeholder",
        "Unit test backend only.",
        required_commands=("python",),
        required_python_packages=("torch",),
        supported_adapter_types=("lora",),
        supports_quantization=False,
        metadata={"unit": True},
    )

    data = backend.to_dict()

    assert data["name"] == "unit-backend"
    assert data["backend_type"] == "custom_placeholder"
    assert data["required_commands"] == ["python"]
    assert "Trainer backend: unit-backend" in backend.to_text()


def test_training_execution_plan_serialization() -> None:
    _package, plan, bundle = build_demo_training_dry_run_inputs()
    execution_plan = DryRunTrainer().create_execution_plan(
        plan,
        bundle,
        create_dry_run_backend_spec(),
    )

    data = execution_plan.to_dict()
    json_data = loads(execution_plan.to_json())

    assert isinstance(execution_plan, TrainingExecutionPlan)
    assert data["blocked"] is False
    assert json_data["readiness"]["ready"] is True
    assert "Command preview" in execution_plan.to_text()


def test_dry_run_trainer_config_defaults_are_conservative() -> None:
    config = DryRunTrainerConfig()

    assert config.backend_name == "dry-run"
    assert config.allow_missing_optional_artifacts is False
    assert config.require_validation_passed is True
    assert config.require_non_empty_train_split is True
    assert config.require_model_license is True
    assert config.require_dataset_manifest is True


def test_dry_run_trainer_produces_plan_for_valid_demo_package() -> None:
    _package, plan, bundle = build_demo_training_dry_run_inputs()

    execution_plan = DryRunTrainer().create_execution_plan(plan, bundle)

    assert execution_plan.blocked is False
    assert execution_plan.readiness.ready is True
    assert execution_plan.readiness.train_examples_count > 0
    assert "dry-run only; no training command will be executed" in execution_plan.warnings


def test_dry_run_trainer_blocks_when_train_split_empty() -> None:
    package = build_training_dataset_package(
        (),
        split_config=TrainingSplitConfig(),
        dataset_name="empty-package",
        description="Empty package for blocked dry-run tests.",
    )
    plan = build_demo_training_plan(package)
    bundle = TrainingArtifactBuilder().build(package, plan)

    execution_plan = DryRunTrainer().create_execution_plan(plan, bundle)

    assert execution_plan.blocked is True
    assert "train split is empty" in execution_plan.blockers
    assert execution_plan.readiness.train_examples_count == 0


def test_dry_run_trainer_blocks_when_validation_failed_and_required() -> None:
    package = build_training_dataset_package(
        (),
        dataset_name="invalid-package",
        description="Invalid package for validation blocked dry-run tests.",
    )
    plan = build_demo_training_plan(package)
    bundle = TrainingArtifactBuilder().build(package, plan)

    execution_plan = DryRunTrainer().create_execution_plan(
        plan,
        bundle,
        create_dry_run_backend_spec(),
        DryRunTrainerConfig(require_validation_passed=True),
    )

    assert execution_plan.blocked is True
    assert "training run config validation did not pass" in execution_plan.blockers
    assert execution_plan.readiness.training_config_valid is False


def test_dry_run_trainer_detects_missing_required_artifacts() -> None:
    _package, plan, bundle = build_demo_training_dry_run_inputs()
    incomplete_bundle = TrainingArtifactBundle(
        "incomplete-bundle",
        tuple(artifact for artifact in bundle.artifacts if artifact.path != "data/train.jsonl"),
    )

    execution_plan = DryRunTrainer().create_execution_plan(plan, incomplete_bundle)

    assert execution_plan.blocked is True
    assert "missing required artifact: data/train.jsonl" in execution_plan.blockers
    assert execution_plan.readiness.required_artifacts_present is False


def test_backend_presets_are_deterministic() -> None:
    first = create_qlora_cli_placeholder_backend_spec()
    second = create_qlora_cli_placeholder_backend_spec()
    dry_run = create_dry_run_backend_spec()
    lora = create_lora_cli_placeholder_backend_spec()

    assert first.to_dict() == second.to_dict()
    assert dry_run.backend_type == "dry_run"
    assert lora.supported_adapter_types == ("lora",)
    assert first.supports_quantization is True


def test_command_preview_includes_expected_artifact_paths() -> None:
    _package, plan, _bundle = build_demo_training_dry_run_inputs()
    preview = build_training_command_preview(plan, create_dry_run_backend_spec())
    preview_text = command_preview_text(preview)

    assert "config/training_config.json" in preview
    assert "data/train.jsonl" in preview
    assert "data/validation.jsonl" in preview
    assert "outputs/demo-training-plan-config-only" in preview
    assert "grona_train_placeholder" in preview_text
    assert "--dry-run-placeholder-not-implemented" in preview


def test_training_readiness_report_creation() -> None:
    report = TrainingReadinessReport(
        ready=False,
        warnings=("review warning",),
        blockers=("blocked for test",),
        artifact_count=3,
        required_artifacts_present=False,
        training_config_valid=False,
        train_examples_count=0,
    )

    data = report.to_dict()

    assert data["ready"] is False
    assert data["artifact_count"] == 3
    assert "blocked for test" in report.to_text()


def test_cli_training_dry_run_demo_behavior(capsys) -> None:
    assert main(["--training-dry-run-demo"]) == 0

    output = capsys.readouterr().out
    assert "Training dry-run trainer demo" in output
    assert "dry-run only" in output
    assert "Readiness report" in output
    assert "Command preview" in output
    assert "grona_train_placeholder" in output
