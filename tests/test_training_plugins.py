import sys

from grona import (
    FutureLoRABackendStub,
    FutureQLoRABackendStub,
    OptionalDependencySpec,
    OptionalTrainingDependencyReport,
    TrainingBackendCapability,
    TrainingBackendDesignReport,
    build_optional_training_backend_design_report,
    create_optional_training_backend_registry,
    optional_training_dependency_specs,
    optional_training_required_artifacts,
)
from grona.entrypoint import main
from grona.training_dry_run import build_demo_training_dry_run_inputs


def test_optional_dependency_spec_creation() -> None:
    dependency = OptionalDependencySpec(
        "torch",
        "torch",
        "future tensor runtime",
        ("lora",),
        "future plugin only",
        metadata={"heavy_dependency": True},
    )

    data = dependency.to_dict()

    assert data["name"] == "torch"
    assert data["package"] == "torch"
    assert data["required_for"] == ["lora"]
    assert data["metadata"] == {"heavy_dependency": True}
    assert "future tensor runtime" in dependency.to_text()


def test_optional_training_dependency_report_creation() -> None:
    dependency = OptionalDependencySpec(
        "peft",
        "peft",
        "future adapter runtime",
        ("lora", "qlora"),
        "future plugin only",
    )
    report = OptionalTrainingDependencyReport(
        available=False,
        missing=(dependency,),
        warnings=("metadata only",),
        install_hints=("future plugin only",),
    )
    backend_report = report.to_backend_dependency_report("unit-backend")

    assert report.to_dict()["available"] is False
    assert report.missing == (dependency,)
    assert backend_report.available is False
    assert backend_report.missing_dependencies == ("peft",)
    assert "metadata only" in report.to_text()


def test_future_lora_backend_stub_capabilities_and_readiness() -> None:
    _package, plan, bundle = build_demo_training_dry_run_inputs()
    backend = FutureLoRABackendStub()

    execution_plan = backend.build_execution_plan(plan, bundle)

    assert backend.name == "future-lora-backend-stub"
    assert TrainingBackendCapability.LORA in backend.capabilities
    assert backend.supports(plan.config) is False
    assert execution_plan.blocked is True
    assert "backend future-lora-backend-stub does not support this training config" in execution_plan.blockers
    assert any("not implemented" in blocker for blocker in execution_plan.blockers)


def test_future_qlora_backend_stub_capabilities_and_readiness() -> None:
    _package, plan, bundle = build_demo_training_dry_run_inputs()
    backend = FutureQLoRABackendStub()

    execution_plan = backend.build_execution_plan(plan, bundle)

    assert backend.name == "future-qlora-backend-stub"
    assert TrainingBackendCapability.QLORA in backend.capabilities
    assert TrainingBackendCapability.QUANTIZATION in backend.capabilities
    assert backend.supports(plan.config) is True
    assert execution_plan.blocked is True
    assert execution_plan.readiness.ready is False
    assert any("optional training plugin dependency" in blocker for blocker in execution_plan.blockers)
    assert any("not implemented" in blocker for blocker in execution_plan.blockers)


def test_future_backend_stubs_refuse_real_training_execution() -> None:
    backend = FutureLoRABackendStub()

    try:
        backend.run_training()
    except NotImplementedError as exc:
        assert "real training is not implemented" in str(exc)
    else:
        raise AssertionError("future training backend stub should refuse execution")


def test_optional_training_backend_registry_ordering() -> None:
    registry = create_optional_training_backend_registry()

    assert tuple(backend.name for backend in registry.list_backends()) == (
        "dry-run",
        "future-lora-backend-stub",
        "future-qlora-backend-stub",
    )
    assert tuple(backend.name for backend in registry.find_by_adapter_type("qlora")) == (
        "dry-run",
        "future-qlora-backend-stub",
    )


def test_training_backend_design_report_includes_missing_dependencies() -> None:
    registry = create_optional_training_backend_registry()
    report = build_optional_training_backend_design_report(registry)
    data = report.to_dict()
    packages = {dependency["package"] for dependency in data["optional_dependencies"]}

    assert isinstance(report, TrainingBackendDesignReport)
    assert "future-lora-backend-stub" in report.future_backend_names
    assert "future-qlora-backend-stub" in report.future_backend_names
    assert {"torch", "transformers", "peft", "accelerate", "bitsandbytes", "datasets"}.issubset(packages)
    assert "real_training_execution" in report.missing_capabilities
    assert "real LoRA training is not implemented" in report.to_text()


def test_optional_training_dependency_specs_are_deterministic() -> None:
    first = optional_training_dependency_specs()
    second = optional_training_dependency_specs()

    assert first == second
    assert tuple(dependency.package for dependency in first) == (
        "torch",
        "transformers",
        "peft",
        "accelerate",
        "bitsandbytes",
        "datasets",
    )


def test_optional_training_required_artifacts_match_training_bundle_surface() -> None:
    artifacts = optional_training_required_artifacts()

    assert "config/training_config.json" in artifacts
    assert "data/train.jsonl" in artifacts
    assert "README.md" in artifacts


def test_no_heavy_dependency_imports_required() -> None:
    heavy_modules = {"torch", "transformers", "peft", "bitsandbytes", "datasets", "accelerate"}

    assert heavy_modules.isdisjoint(sys.modules)


def test_cli_optional_training_backend_demo_behavior(capsys) -> None:
    assert main(["--optional-training-backend-demo"]) == 0

    output = capsys.readouterr().out
    assert "Optional training backend plugin scaffold demo" in output
    assert "future-lora-backend-stub" in output
    assert "future-qlora-backend-stub" in output
    assert "real training is not implemented" in output
    assert "No model loading" in output
    assert "Command preview is not executed" in output
