from grona import (
    AdapterTrainingSpec,
    PlaceholderTrainingBackend,
    TrainingBackendCapability,
    TrainingBackendDependencyReport,
    TrainingBackendMetadata,
    TrainingBackendRegistry,
    TrainingReadinessReport,
    TrainerBackendSpec,
    create_default_training_backend_registry,
    create_dry_run_placeholder_backend,
    create_lora_placeholder_backend,
    create_placeholder_training_backend,
    create_qlora_placeholder_backend,
)
from grona.entrypoint import main
from grona.training_backends import all_training_backend_capabilities, required_training_artifacts
from grona.training_dry_run import build_demo_training_dry_run_inputs
from grona.training_plan import TrainingRunConfig


def test_training_backend_capability_labels_are_stable() -> None:
    capabilities = all_training_backend_capabilities()

    assert TrainingBackendCapability.LORA == "lora"
    assert TrainingBackendCapability.QLORA == "qlora"
    assert TrainingBackendCapability.DRY_RUN in capabilities
    assert TrainingBackendCapability.COMMAND_PREVIEW in capabilities
    assert len(capabilities) == len(set(capabilities))


def test_training_backend_registry_register_list_get_and_find() -> None:
    registry = TrainingBackendRegistry()
    qlora = create_qlora_placeholder_backend()
    dry_run = create_dry_run_placeholder_backend()
    lora = create_lora_placeholder_backend()

    registry.register(qlora)
    registry.register(dry_run)
    registry.register(lora)

    names = tuple(backend.name for backend in registry.list_backends())
    assert names == ("dry-run", "lora-cli-placeholder", "qlora-cli-placeholder")
    assert registry.get("dry-run") is dry_run
    assert tuple(backend.name for backend in registry.find_by_adapter_type("lora")) == (
        "dry-run",
        "lora-cli-placeholder",
    )
    assert tuple(
        backend.name
        for backend in registry.find_by_capability(TrainingBackendCapability.QUANTIZATION)
    ) == ("dry-run", "qlora-cli-placeholder")


def test_training_backend_registry_rejects_duplicate_names() -> None:
    registry = TrainingBackendRegistry((create_dry_run_placeholder_backend(),))

    try:
        registry.register(create_dry_run_placeholder_backend())
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("duplicate training backend registration should fail")


def test_placeholder_backend_supports_demo_config() -> None:
    _package, plan, _bundle = build_demo_training_dry_run_inputs()
    backend = create_dry_run_placeholder_backend()

    assert backend.supports(plan.config) is True
    assert backend.name == "dry-run"
    assert backend.backend_type == "dry_run"
    assert TrainingBackendCapability.COMMAND_PREVIEW in backend.capabilities


def test_placeholder_backend_refuses_unsupported_adapter_type() -> None:
    _package, plan, bundle = build_demo_training_dry_run_inputs()
    unsupported_config = TrainingRunConfig(
        run_name=plan.config.run_name,
        base_model=plan.config.base_model,
        adapter=AdapterTrainingSpec(adapter_type="unsupported_adapter"),
        dataset_manifest=plan.config.dataset_manifest,
        dataset_package_summary=plan.config.dataset_package_summary,
        safety_notes=plan.config.safety_notes,
        output_policy=plan.config.output_policy,
    )
    unsupported_plan = type(plan)(
        unsupported_config,
        plan.validation,
        plan.dataset_card,
        plan.model_card_draft,
        plan.created_at,
        plan.metadata,
    )
    backend = create_dry_run_placeholder_backend()

    execution_plan = backend.build_execution_plan(unsupported_plan, bundle)

    assert backend.supports(unsupported_config) is False
    assert execution_plan.blocked is True
    assert "backend dry-run does not support this training config" in execution_plan.blockers


def test_dependency_report_creation_is_static() -> None:
    report = TrainingBackendDependencyReport(
        "unit-backend",
        available=False,
        missing_dependencies=("torch",),
        optional_dependencies=("peft",),
        warnings=("static only",),
        blockers=("missing optional backend dependency: torch",),
    )

    data = report.to_dict()

    assert data["backend_name"] == "unit-backend"
    assert data["available"] is False
    assert "torch" in data["missing_dependencies"]
    assert "static only" in report.to_text()


def test_backend_metadata_creation() -> None:
    metadata = TrainingBackendMetadata(
        "unit-backend",
        package_name="grona-unit",
        optional_extra="training",
        install_hint="pip install grona[training]",
        supported_adapter_types=("lora",),
        supported_quantization_modes=("none",),
        supported_artifact_formats=("jsonl",),
        limitations=("placeholder only",),
    )

    data = metadata.to_dict()

    assert data["backend_name"] == "unit-backend"
    assert data["optional_extra"] == "training"
    assert "placeholder only" in metadata.to_text()


def test_default_training_backend_registry_contains_placeholders() -> None:
    registry = create_default_training_backend_registry()

    assert tuple(backend.name for backend in registry.list_backends()) == (
        "dry-run",
        "lora-cli-placeholder",
        "qlora-cli-placeholder",
    )
    assert registry.get("lora-cli-placeholder").check_dependencies().available is False
    assert registry.get("qlora-cli-placeholder").check_dependencies().missing_dependencies == (
        "torch",
        "transformers",
        "peft",
        "bitsandbytes",
    )


def test_placeholder_execution_plan_is_created_but_not_executed() -> None:
    _package, plan, bundle = build_demo_training_dry_run_inputs()
    backend = create_dry_run_placeholder_backend()

    execution_plan = backend.build_execution_plan(plan, bundle)

    assert execution_plan.blocked is False
    assert execution_plan.readiness.ready is True
    assert execution_plan.metadata["executes_commands"] is False
    assert "--dry-run-placeholder-not-implemented" in execution_plan.command_preview


def test_lora_placeholder_dependency_blockers_are_visible() -> None:
    _package, plan, bundle = build_demo_training_dry_run_inputs()
    backend = create_lora_placeholder_backend()

    execution_plan = backend.build_execution_plan(plan, bundle)

    assert execution_plan.blocked is True
    assert any("missing optional backend dependency" in blocker for blocker in execution_plan.blockers)
    assert execution_plan.readiness.ready is False
    assert isinstance(execution_plan.readiness, TrainingReadinessReport)


def test_create_placeholder_training_backend_from_spec() -> None:
    spec = TrainerBackendSpec(
        "unit-placeholder",
        "unit_placeholder",
        "Unit placeholder backend.",
        supported_adapter_types=("lora",),
    )

    backend = create_placeholder_training_backend(
        spec,
        (TrainingBackendCapability.LORA, TrainingBackendCapability.COMMAND_PREVIEW),
    )

    assert isinstance(backend, PlaceholderTrainingBackend)
    assert backend.name == "unit-placeholder"
    assert backend.metadata.supported_adapter_types == ("lora",)


def test_required_training_artifacts_include_current_bundle_paths() -> None:
    artifacts = required_training_artifacts()

    assert "config/training_config.json" in artifacts
    assert "data/train.jsonl" in artifacts
    assert "manifests/training_export_manifest.json" in artifacts
    assert "README.md" in artifacts


def test_cli_training_backend_demo_behavior(capsys) -> None:
    assert main(["--training-backend-demo"]) == 0

    output = capsys.readouterr().out
    assert "Training backend boundary demo" in output
    assert "Registered backends" in output
    assert "dry-run" in output
    assert "lora-cli-placeholder" in output
    assert "qlora-cli-placeholder" in output
    assert "Command preview" in output
    assert "Dependency report" in output
