import sys

from grona.entrypoint import main
from grona.experimental_training import (
    EXPERIMENTAL_LORA_CONFIRMATION_TOKEN,
    ExperimentalLoRABackend,
    LoRATrainingJob,
    LoRATrainingSafetyConfig,
    build_demo_lora_training_inputs,
    detect_lora_dependency_availability,
)
from grona.training_dry_run import build_demo_training_dry_run_inputs


HEAVY_MODULES = {"torch", "transformers", "peft", "bitsandbytes", "datasets", "accelerate"}


def missing_dependency_finder(_package: str) -> object | None:
    return None


def present_dependency_finder(package: str) -> object | None:
    if package in {"torch", "transformers", "peft", "accelerate", "datasets"}:
        return object()
    return None


def test_experimental_lora_backend_creation() -> None:
    backend = ExperimentalLoRABackend(dependency_finder=missing_dependency_finder)

    assert backend.name == "experimental-lora-backend"
    assert backend.backend_type == "experimental_lora_backend_skeleton"
    assert "lora" in backend.capabilities
    assert backend.required_dependencies == ("torch", "transformers", "peft", "accelerate", "datasets")
    assert backend.metadata.metadata["trains_model"] is False


def test_experimental_lora_backend_supports_lora_config() -> None:
    _package, plan, _bundle = build_demo_lora_training_inputs()
    backend = ExperimentalLoRABackend(dependency_finder=missing_dependency_finder)

    assert backend.supports(plan.config) is True


def test_experimental_lora_backend_rejects_unsupported_adapter_type() -> None:
    _package, qlora_plan, _bundle = build_demo_training_dry_run_inputs()
    backend = ExperimentalLoRABackend(dependency_finder=missing_dependency_finder)

    assert backend.supports(qlora_plan.config) is False


def test_dependency_detection_uses_finder_without_importing_heavy_packages() -> None:
    before = set(sys.modules)
    calls: list[str] = []

    def finder(package: str) -> object | None:
        calls.append(package)
        return None

    report = detect_lora_dependency_availability(finder)
    after = set(sys.modules)

    assert calls == ["torch", "transformers", "peft", "accelerate", "datasets", "bitsandbytes"]
    assert report.available is False
    assert report.missing_dependencies == ("torch", "transformers", "peft", "accelerate", "datasets")
    assert HEAVY_MODULES.isdisjoint(after - before)
    assert report.metadata["imports_packages"] is False


def test_lora_training_job_serialization() -> None:
    job = LoRATrainingJob(
        job_id="job:unit",
        created_at="2026-01-01T00:00:00+00:00",
        run_name="unit",
        base_model={"model_id": "demo/model"},
        adapter_config={"adapter_type": "lora"},
        dataset_paths={"train": "out/data/train.jsonl"},
        output_dir="out",
        training_args={"epochs": 1},
        warnings=("preview only",),
        metadata={"trains_model": False},
    )

    data = job.to_dict()

    assert data["job_id"] == "job:unit"
    assert data["dataset_paths"] == {"train": "out/data/train.jsonl"}
    assert "preview only" in job.to_text()
    assert "job:unit" in job.to_json()


def test_lora_training_safety_config_defaults_are_conservative() -> None:
    safety = LoRATrainingSafetyConfig()

    assert safety.allow_training_execution is False
    assert safety.allow_model_download is False
    assert safety.allow_dataset_download is False
    assert safety.allow_overwrite_output is False
    assert safety.require_explicit_confirmation is True
    assert safety.to_dict()["allow_training_execution"] is False


def test_readiness_report_blocks_when_dependencies_missing_and_execution_disallowed() -> None:
    _package, plan, bundle = build_demo_lora_training_inputs()
    backend = ExperimentalLoRABackend(dependency_finder=missing_dependency_finder)
    job, readiness = backend.prepare_training_job(plan, bundle, "outputs/unit", LoRATrainingSafetyConfig())

    assert job.job_id == "lora-training-job:demo-experimental-lora-backend-skeleton"
    assert readiness.ready is False
    assert readiness.dependency_report.available is False
    assert "training execution is disabled by default" in readiness.blockers
    assert any("missing optional LoRA dependency: torch" in blocker for blocker in readiness.blockers)
    assert "real LoRA training loop is not implemented in this skeleton" in readiness.blockers


def test_prepare_training_job_creates_deterministic_job_preview() -> None:
    _package, plan, bundle = build_demo_lora_training_inputs()
    backend = ExperimentalLoRABackend(dependency_finder=present_dependency_finder)
    safety = LoRATrainingSafetyConfig(
        allow_training_execution=True,
        allow_model_download=True,
        allow_dataset_download=True,
        require_explicit_confirmation=False,
    )

    first_job, first_readiness = backend.prepare_training_job(plan, bundle, "outputs/unit", safety)
    second_job, second_readiness = backend.prepare_training_job(plan, bundle, "outputs/unit", safety)

    assert first_job.to_dict() == second_job.to_dict()
    assert first_readiness.dependency_report.available is True
    assert first_job.dataset_paths["train"] == "outputs/unit/data/train.jsonl"
    assert first_readiness.ready is False
    assert "real LoRA training loop is not implemented in this skeleton" in first_readiness.blockers


def test_run_training_refuses_by_default() -> None:
    _package, plan, bundle = build_demo_lora_training_inputs()
    backend = ExperimentalLoRABackend(dependency_finder=present_dependency_finder)

    try:
        backend.run_training(plan, bundle, "outputs/unit", LoRATrainingSafetyConfig())
    except RuntimeError as exc:
        assert "execution is disabled" in str(exc)
    else:
        raise AssertionError("experimental LoRA backend should refuse default execution")


def test_run_training_requires_confirmation_when_execution_flag_is_set() -> None:
    _package, plan, bundle = build_demo_lora_training_inputs()
    backend = ExperimentalLoRABackend(dependency_finder=present_dependency_finder)
    safety = LoRATrainingSafetyConfig(
        allow_training_execution=True,
        allow_model_download=True,
        allow_dataset_download=True,
    )

    try:
        backend.run_training(plan, bundle, "outputs/unit", safety)
    except RuntimeError as exc:
        assert "confirmation token" in str(exc)
    else:
        raise AssertionError("experimental LoRA backend should require confirmation")


def test_run_training_remains_not_implemented_even_with_explicit_gates() -> None:
    _package, plan, bundle = build_demo_lora_training_inputs()
    backend = ExperimentalLoRABackend(dependency_finder=present_dependency_finder)
    safety = LoRATrainingSafetyConfig(
        allow_training_execution=True,
        allow_model_download=True,
        allow_dataset_download=True,
    )

    try:
        backend.run_training(
            plan,
            bundle,
            "outputs/unit",
            safety,
            confirmation=EXPERIMENTAL_LORA_CONFIRMATION_TOKEN,
        )
    except NotImplementedError as exc:
        assert "does not implement a real LoRA training loop" in str(exc)
    else:
        raise AssertionError("experimental LoRA backend should not implement real training")


def test_cli_experimental_lora_backend_demo_behavior(capsys) -> None:
    assert main(["--experimental-lora-backend-demo"]) == 0

    output = capsys.readouterr().out
    assert "Experimental LoRA backend skeleton demo" in output
    assert "LoRA training job preview" in output
    assert "not implemented, not executed" in output
    assert "no training" in output


def test_normal_import_does_not_require_heavy_ml_dependencies() -> None:
    assert HEAVY_MODULES.isdisjoint(sys.modules)
