import sys

from grona import (
    ExperimentalLoRABackend,
    LocalTrainingHandoffManifest,
    LoRATrainingSafetyConfig,
    ModelBuildReadinessAuditor,
    ModelBuildReadinessReport,
    TrainingDependencyProfile,
    TrainingEnvironmentAuditor,
    TrainingEnvironmentProfile,
    TrainingEnvironmentReadinessReport,
    TrainingHardwareProfile,
    TrainingHardwareRequirement,
    build_demo_model_build_readiness_report,
    build_model_build_demo_pipeline_inputs,
    create_cpu_only_demo_environment,
    create_missing_dependencies_demo_environment,
    create_small_gpu_demo_environment,
    create_user_described_local_environment_profile,
    model_build_lifecycle_markdown,
)
from grona.entrypoint import main
from grona.model_build_readiness import build_local_training_handoff_manifest


HEAVY_MODULES = {"torch", "transformers", "peft", "bitsandbytes", "datasets", "accelerate"}


def test_training_hardware_profile_creation() -> None:
    profile = TrainingHardwareProfile("desktop", cpu_cores=6, ram_gb=32, gpu_name="RTX 3080", gpu_count=1, gpu_vram_gb=10, cuda_available=True)

    data = profile.to_dict()

    assert data["name"] == "desktop"
    assert data["cpu_cores"] == 6
    assert data["gpu_vram_gb"] == 10.0


def test_training_dependency_profile_creation() -> None:
    profile = TrainingDependencyProfile(installed_packages=("torch", "torch"), missing_packages=("peft",), optional_packages=("bitsandbytes",), python_version="3.12")

    assert profile.installed_packages == ("torch",)
    assert profile.has_package("torch") is True
    assert profile.has_package("peft") is False
    assert profile.to_dict()["python_version"] == "3.12"


def test_training_environment_profile_serialization() -> None:
    profile = create_user_described_local_environment_profile(6, 32, gpu_name="RTX 3080", gpu_vram_gb=10, installed_packages=("torch",))

    data = profile.to_dict()

    assert data["name"] == "user-described-local-environment"
    assert data["hardware"]["gpu_count"] == 1
    assert "user-described" in profile.to_json()


def test_training_hardware_requirement_presets() -> None:
    cpu = TrainingHardwareRequirement.cpu_dry_run()
    lora = TrainingHardwareRequirement.small_lora()
    qlora = TrainingHardwareRequirement.small_qlora()
    full = TrainingHardwareRequirement.full_finetune_placeholder()

    assert cpu.requires_gpu is False
    assert "torch" in lora.required_dependencies
    assert qlora.requires_gpu is True
    assert full.min_gpu_vram_gb >= 24


def test_training_environment_auditor_blocks_missing_dependencies() -> None:
    report = TrainingEnvironmentAuditor().audit(
        create_missing_dependencies_demo_environment(),
        TrainingHardwareRequirement.small_lora(),
    )

    assert report.ready is False
    assert report.status == "blocked"
    assert any("torch" in blocker for blocker in report.blockers)


def test_training_environment_auditor_supports_cpu_dry_run_profile() -> None:
    report = TrainingEnvironmentAuditor().audit(
        create_cpu_only_demo_environment(),
        TrainingHardwareRequirement.cpu_dry_run(),
    )

    assert isinstance(report, TrainingEnvironmentReadinessReport)
    assert report.ready is True
    assert report.status == "warning"
    assert "dry-run only" in report.warnings


def test_training_environment_auditor_blocks_qlora_when_vram_and_dependencies_missing() -> None:
    report = TrainingEnvironmentAuditor().audit(
        create_missing_dependencies_demo_environment(),
        TrainingHardwareRequirement.small_qlora(),
    )

    assert report.ready is False
    assert any("GPU" in blocker for blocker in report.blockers)
    assert any("bitsandbytes" in blocker for blocker in report.blockers)


def test_small_gpu_demo_can_satisfy_small_lora_planning_requirement() -> None:
    report = TrainingEnvironmentAuditor().audit(
        create_small_gpu_demo_environment(),
        TrainingHardwareRequirement.small_lora(),
    )

    assert report.ready is True
    assert report.status in {"ready", "warning"}


def test_model_build_readiness_report_creation() -> None:
    environment = TrainingEnvironmentAuditor().audit(
        create_cpu_only_demo_environment(),
        TrainingHardwareRequirement.cpu_dry_run(),
    )
    demo = build_demo_model_build_readiness_report()
    report = ModelBuildReadinessReport(
        ready_for_real_training=False,
        ready_for_local_handoff=True,
        recommended_next_action="continue local handoff",
        pipeline_report=demo.pipeline_report,
        environment_report=environment,
        backend_contract_status=demo.backend_contract_status,
        experimental_lora_readiness=demo.experimental_lora_readiness,
        artifact_bundle_summary=demo.artifact_bundle_summary,
        training_plan_validation=demo.training_plan_validation,
        handoff_manifest=demo.handoff_manifest,
    )

    assert report.ready_for_real_training is False
    assert report.ready_for_local_handoff is True
    assert "ModelBuildReadinessReport" not in report.to_json()


def test_model_build_readiness_auditor_produces_deterministic_report() -> None:
    report_a = build_demo_model_build_readiness_report()
    report_b = build_demo_model_build_readiness_report()

    assert report_a.to_json() == report_b.to_json()
    assert report_a.ready_for_real_training is False
    assert report_a.ready_for_local_handoff is True
    assert report_a.summary["real_training_blocked_by_default"] is True


def test_real_training_readiness_remains_false_by_default() -> None:
    examples, package, plan, bundle = build_model_build_demo_pipeline_inputs()
    report = ModelBuildReadinessAuditor().audit(
        examples,
        package,
        plan,
        bundle,
        ExperimentalLoRABackend(dependency_finder=lambda _package: None),
        create_cpu_only_demo_environment(),
        TrainingHardwareRequirement.cpu_dry_run(),
        LoRATrainingSafetyConfig(),
    )

    assert report.ready_for_real_training is False
    assert any("real training remains blocked" in reason for reason in report.blocked_reasons)


def test_local_handoff_readiness_can_be_true_for_deterministic_demo_pipeline() -> None:
    report = build_demo_model_build_readiness_report()

    assert report.ready_for_local_handoff is True
    assert "local" in report.recommended_next_action


def test_local_training_handoff_manifest_markdown_output() -> None:
    _examples, _package, _plan, bundle = build_model_build_demo_pipeline_inputs()
    manifest = build_local_training_handoff_manifest(
        bundle,
        ExperimentalLoRABackend(dependency_finder=lambda _package: None),
        TrainingHardwareRequirement.cpu_dry_run(),
    )

    assert isinstance(manifest, LocalTrainingHandoffManifest)
    markdown = manifest.to_markdown()
    assert "Local Training Handoff Manifest" in markdown
    assert "python -m grona --model-build-readiness-demo" in markdown
    assert "model training" in markdown


def test_model_build_lifecycle_summary_helper_output() -> None:
    text = model_build_lifecycle_markdown()

    assert "reviewed traces -> training examples" in text
    assert "local handoff -> future real training" in text


def test_cli_model_build_readiness_demo_behavior(capsys) -> None:
    assert main(["--model-build-readiness-demo"]) == 0

    output = capsys.readouterr().out
    assert "Model build readiness demo" in output
    assert "Consolidated readiness" in output
    assert "Local handoff checklist" in output
    assert "not executed, not implemented" in output


def test_normal_import_still_does_not_require_heavy_ml_dependencies_for_model_build_readiness() -> None:
    assert HEAVY_MODULES.isdisjoint(sys.modules)
