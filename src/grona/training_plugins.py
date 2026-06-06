"""Optional real-training plugin scaffold with safe future backend stubs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .feedback import Metadata
from .training import json_metadata
from .training_artifacts import TrainingArtifactBundle
from .training_backends import (
    TrainingBackendCapability,
    TrainingBackendDependencyReport,
    TrainingBackendMetadata,
    TrainingBackendRegistry,
    create_dry_run_placeholder_backend,
    required_training_artifacts,
)
from .training_dry_run import (
    DRY_RUN_REQUIRED_ARTIFACTS,
    DryRunTrainer,
    DryRunTrainerConfig,
    TrainerBackendSpec,
    TrainingExecutionPlan,
    TrainingReadinessReport,
    dedupe_strings,
)
from .training_plan import TrainingPlan, TrainingRunConfig

OPTIONAL_TRAINING_PLUGIN_STATUS = "not_installed_not_implemented"
OPTIONAL_TRAINING_CREATED_AT = "2026-01-01T00:00:00+00:00"


@dataclass(frozen=True)
class OptionalDependencySpec:
    """Metadata-only description of a future optional training dependency."""

    name: str
    package: str
    purpose: str
    required_for: tuple[str, ...]
    install_hint: str
    is_required: bool = True
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        package: str,
        purpose: str,
        required_for: Sequence[str],
        install_hint: str,
        is_required: bool = True,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not name:
            raise ValueError("optional dependency name cannot be empty")
        if not package:
            raise ValueError("optional dependency package cannot be empty")
        if not purpose:
            raise ValueError("optional dependency purpose cannot be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "package", package)
        object.__setattr__(self, "purpose", purpose)
        object.__setattr__(self, "required_for", tuple(required_for))
        object.__setattr__(self, "install_hint", install_hint)
        object.__setattr__(self, "is_required", is_required)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible dependency spec."""
        return {
            "name": self.name,
            "package": self.package,
            "purpose": self.purpose,
            "required_for": list(self.required_for),
            "install_hint": self.install_hint,
            "is_required": self.is_required,
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return readable dependency metadata."""
        return "\n".join(
            (
                f"Optional dependency: {self.name}",
                f"Package: {self.package}",
                f"Purpose: {self.purpose}",
                f"Required for: {', '.join(self.required_for) or 'none'}",
                f"Install hint: {self.install_hint}",
                f"Required: {self.is_required}",
            )
        )


@dataclass(frozen=True)
class OptionalTrainingDependencyReport:
    """Metadata-only dependency report for optional training plugins."""

    available: bool
    missing: tuple[OptionalDependencySpec, ...] = ()
    present: tuple[OptionalDependencySpec, ...] = ()
    warnings: tuple[str, ...] = ()
    install_hints: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        available: bool,
        missing: Sequence[OptionalDependencySpec] = (),
        present: Sequence[OptionalDependencySpec] = (),
        warnings: Sequence[str] = (),
        install_hints: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "available", available)
        object.__setattr__(self, "missing", tuple(missing))
        object.__setattr__(self, "present", tuple(present))
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "install_hints", tuple(install_hints))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_backend_dependency_report(self, backend_name: str) -> TrainingBackendDependencyReport:
        """Convert the optional plugin report to the existing backend report contract."""
        missing_packages = tuple(dependency.package for dependency in self.missing)
        blockers = tuple(
            f"optional training plugin dependency is not installed: {dependency.package}"
            for dependency in self.missing
            if dependency.is_required
        )
        return TrainingBackendDependencyReport(
            backend_name,
            available=self.available,
            missing_dependencies=missing_packages,
            optional_dependencies=tuple(dependency.package for dependency in self.missing + self.present),
            warnings=self.warnings,
            blockers=blockers,
            metadata={"optional_training_dependency_report": self.to_dict()},
        )

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible dependency report."""
        return {
            "available": self.available,
            "missing": [dependency.to_dict() for dependency in self.missing],
            "present": [dependency.to_dict() for dependency in self.present],
            "warnings": list(self.warnings),
            "install_hints": list(self.install_hints),
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return readable dependency report details."""
        lines = [
            f"Optional training dependencies available: {self.available}",
            "Missing:",
        ]
        lines.extend(f"- {dependency.package}: {dependency.purpose}" for dependency in self.missing)
        if not self.missing:
            lines.append("- none")
        lines.append("Present:")
        lines.extend(f"- {dependency.package}" for dependency in self.present)
        if not self.present:
            lines.append("- none")
        lines.append("Install hints:")
        lines.extend(markdown_or_none(self.install_hints))
        lines.append("Warnings:")
        lines.extend(markdown_or_none(self.warnings))
        return "\n".join(lines)


class FutureTrainingBackendStub:
    """Base stub for future real training plugins. It never executes training."""

    name = "future-training-stub"
    backend_type = "future_training_stub"
    adapter_type = "unknown"
    quantization_modes: tuple[str, ...] = ("none",)
    capabilities: tuple[str, ...] = (TrainingBackendCapability.COMMAND_PREVIEW,)
    required_artifacts: tuple[str, ...] = DRY_RUN_REQUIRED_ARTIFACTS
    optional_dependencies: tuple[OptionalDependencySpec, ...] = ()
    limitations: tuple[str, ...] = (
        "not installed",
        "not implemented",
        "no real training",
        "no subprocess execution",
        "no model loading",
    )

    @property
    def required_dependencies(self) -> tuple[str, ...]:
        """Return future optional dependency package names."""
        return tuple(dependency.package for dependency in self.optional_dependencies)

    @property
    def metadata(self) -> TrainingBackendMetadata:
        """Return backend metadata for registry adapter lookup."""
        return TrainingBackendMetadata(
            backend_name=self.name,
            package_name="grona-training-plugin-placeholder",
            optional_extra="training",
            install_hint="future only; no real training extra is published yet",
            supported_adapter_types=(self.adapter_type,),
            supported_quantization_modes=self.quantization_modes,
            supported_artifact_formats=("jsonl", "json", "markdown", "text"),
            limitations=self.limitations,
            metadata={"plugin_status": OPTIONAL_TRAINING_PLUGIN_STATUS},
        )

    @property
    def spec(self) -> TrainerBackendSpec:
        """Return a descriptive dry-run backend spec for execution previews."""
        return TrainerBackendSpec(
            self.name,
            self.backend_type,
            f"Future {self.adapter_type} backend stub. Real training is not implemented.",
            required_python_packages=self.required_dependencies,
            supported_adapter_types=(self.adapter_type,),
            supports_quantization=TrainingBackendCapability.QUANTIZATION in self.capabilities,
            metadata={
                "plugin_status": OPTIONAL_TRAINING_PLUGIN_STATUS,
                "executes_commands": False,
                "trains_model": False,
            },
        )

    def supports(self, config: TrainingRunConfig) -> bool:
        """Return whether this future stub matches the adapter config shape."""
        if config.adapter.adapter_type != self.adapter_type:
            return False
        if config.adapter.quantization != "none" and config.adapter.quantization not in self.quantization_modes:
            return False
        return True

    def check_optional_dependencies(self) -> OptionalTrainingDependencyReport:
        """Return metadata-only dependency report without imports or probing."""
        return OptionalTrainingDependencyReport(
            available=False,
            missing=self.optional_dependencies,
            warnings=(
                "metadata-only dependency report; no packages are imported",
                "real training plugin is not installed or implemented",
            ),
            install_hints=dedupe_strings(tuple(dep.install_hint for dep in self.optional_dependencies)),
            metadata={"plugin_status": OPTIONAL_TRAINING_PLUGIN_STATUS, "imports_packages": False},
        )

    def check_dependencies(self) -> TrainingBackendDependencyReport:
        """Return backend dependency report without imports."""
        return self.check_optional_dependencies().to_backend_dependency_report(self.name)

    def check_readiness(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        config: DryRunTrainerConfig | None = None,
    ) -> TrainingReadinessReport:
        """Return readiness details showing this backend is not implemented."""
        return self.build_execution_plan(training_plan, artifact_bundle, config).readiness

    def build_execution_plan(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        config: DryRunTrainerConfig | None = None,
    ) -> TrainingExecutionPlan:
        """Build a blocked dry-run plan for a not-implemented future backend."""
        dry_run_config = config or DryRunTrainerConfig(backend_name=self.name)
        execution_plan = DryRunTrainer().create_execution_plan(
            training_plan,
            artifact_bundle,
            self.spec,
            dry_run_config,
        )
        dependency_report = self.check_dependencies()
        blockers = list(execution_plan.blockers)
        blockers.extend(dependency_report.blockers)
        blockers.append(f"backend {self.name} is a future stub; real training is not implemented")
        if not self.supports(training_plan.config):
            blockers.append(f"backend {self.name} does not support this training config")
        warnings = list(execution_plan.warnings)
        warnings.extend(dependency_report.warnings)
        warnings.append("no training command will be executed")
        readiness = TrainingReadinessReport(
            ready=False,
            warnings=dedupe_strings(warnings),
            blockers=dedupe_strings(blockers),
            artifact_count=execution_plan.readiness.artifact_count,
            required_artifacts_present=execution_plan.readiness.required_artifacts_present,
            training_config_valid=execution_plan.readiness.training_config_valid,
            train_examples_count=execution_plan.readiness.train_examples_count,
            metadata={
                **execution_plan.readiness.metadata,
                "optional_dependency_report": self.check_optional_dependencies().to_dict(),
                "plugin_status": OPTIONAL_TRAINING_PLUGIN_STATUS,
            },
        )
        return TrainingExecutionPlan(
            plan_id=execution_plan.plan_id,
            created_at=execution_plan.created_at,
            training_run_config=execution_plan.training_run_config,
            artifact_bundle_summary=execution_plan.artifact_bundle_summary,
            backend=execution_plan.backend,
            command_preview=execution_plan.command_preview,
            environment_notes=execution_plan.environment_notes,
            warnings=dedupe_strings(warnings),
            blocked=True,
            blockers=dedupe_strings(blockers),
            readiness=readiness,
            metadata={
                **execution_plan.metadata,
                "plugin_status": OPTIONAL_TRAINING_PLUGIN_STATUS,
                "executes_commands": False,
                "trains_model": False,
                "not_implemented": True,
            },
        )

    def run_training(self, *args: object, **kwargs: object) -> None:
        """Refuse real training execution explicitly."""
        _ = (args, kwargs)
        raise NotImplementedError(f"{self.name} is a stub; real training is not implemented")

    def to_text(self) -> str:
        """Return readable future backend stub summary."""
        return "\n".join(
            (
                f"Future training backend stub: {self.name}",
                f"Adapter type: {self.adapter_type}",
                f"Capabilities: {', '.join(self.capabilities) or 'none'}",
                f"Dependencies: {', '.join(self.required_dependencies) or 'none'}",
                "Status: not installed, not implemented, no training execution.",
            )
        )


class FutureLoRABackendStub(FutureTrainingBackendStub):
    """Future LoRA backend stub. It does not implement real LoRA training."""

    name = "future-lora-backend-stub"
    backend_type = "future_lora_backend_stub"
    adapter_type = "lora"
    quantization_modes = ("none",)
    capabilities = (
        TrainingBackendCapability.LORA,
        TrainingBackendCapability.COMMAND_PREVIEW,
        TrainingBackendCapability.CPU_POSSIBLE,
    )
    optional_dependencies = (
        optional_dependency_torch(),
        optional_dependency_transformers(),
        optional_dependency_peft(),
        optional_dependency_accelerate(),
        optional_dependency_datasets(),
    )
    limitations = (
        "LoRA training is not implemented",
        "no torch/transformers/peft imports",
        "no model loading",
        "no subprocess execution",
    )


class FutureQLoRABackendStub(FutureTrainingBackendStub):
    """Future QLoRA backend stub. It does not implement real QLoRA training."""

    name = "future-qlora-backend-stub"
    backend_type = "future_qlora_backend_stub"
    adapter_type = "qlora"
    quantization_modes = ("4bit-placeholder", "8bit-placeholder")
    capabilities = (
        TrainingBackendCapability.QLORA,
        TrainingBackendCapability.QUANTIZATION,
        TrainingBackendCapability.COMMAND_PREVIEW,
        TrainingBackendCapability.GPU_REQUIRED,
    )
    optional_dependencies = (
        optional_dependency_torch(),
        optional_dependency_transformers(),
        optional_dependency_peft(),
        optional_dependency_accelerate(),
        optional_dependency_bitsandbytes(),
        optional_dependency_datasets(),
    )
    limitations = (
        "QLoRA training is not implemented",
        "quantization support is planned metadata only",
        "no bitsandbytes import",
        "no GPU or hardware probing",
        "no model loading",
    )


@dataclass(frozen=True)
class TrainingBackendDesignReport:
    """Design/readiness summary for the optional training plugin scaffold."""

    backend_names: tuple[str, ...]
    future_backend_names: tuple[str, ...]
    optional_dependencies: tuple[OptionalDependencySpec, ...]
    missing_capabilities: tuple[str, ...]
    limitations: tuple[str, ...]
    next_steps: tuple[str, ...]
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        backend_names: Sequence[str],
        future_backend_names: Sequence[str],
        optional_dependencies: Sequence[OptionalDependencySpec],
        missing_capabilities: Sequence[str],
        limitations: Sequence[str],
        next_steps: Sequence[str],
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "backend_names", tuple(backend_names))
        object.__setattr__(self, "future_backend_names", tuple(future_backend_names))
        object.__setattr__(self, "optional_dependencies", tuple(optional_dependencies))
        object.__setattr__(self, "missing_capabilities", tuple(missing_capabilities))
        object.__setattr__(self, "limitations", tuple(limitations))
        object.__setattr__(self, "next_steps", tuple(next_steps))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible design report."""
        return {
            "backend_names": list(self.backend_names),
            "future_backend_names": list(self.future_backend_names),
            "optional_dependencies": [dependency.to_dict() for dependency in self.optional_dependencies],
            "missing_capabilities": list(self.missing_capabilities),
            "limitations": list(self.limitations),
            "next_steps": list(self.next_steps),
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return readable design report details."""
        lines = [
            "Optional training backend design report",
            f"Registered backends: {', '.join(self.backend_names) or 'none'}",
            f"Future backend stubs: {', '.join(self.future_backend_names) or 'none'}",
            "Optional dependencies:",
        ]
        lines.extend(f"- {dependency.package}: {dependency.purpose}" for dependency in self.optional_dependencies)
        if not self.optional_dependencies:
            lines.append("- none")
        lines.append("Missing capabilities:")
        lines.extend(markdown_or_none(self.missing_capabilities))
        lines.append("Limitations:")
        lines.extend(markdown_or_none(self.limitations))
        lines.append("Next steps:")
        lines.extend(markdown_or_none(self.next_steps))
        return "\n".join(lines)


def create_optional_training_backend_registry() -> TrainingBackendRegistry:
    """Return deterministic registry with dry-run placeholder and future training stubs."""
    registry = TrainingBackendRegistry()
    registry.register(create_dry_run_placeholder_backend())
    registry.register(FutureLoRABackendStub())
    registry.register(FutureQLoRABackendStub())
    return registry


def build_optional_training_backend_design_report(
    registry: TrainingBackendRegistry | None = None,
) -> TrainingBackendDesignReport:
    """Build a deterministic design report for future optional training plugins."""
    backend_registry = registry or create_optional_training_backend_registry()
    backends = backend_registry.list_backends()
    future_backends = tuple(
        backend for backend in backends if isinstance(backend, FutureTrainingBackendStub)
    )
    dependencies = dedupe_dependency_specs(
        dependency
        for backend in future_backends
        for dependency in backend.optional_dependencies
    )
    return TrainingBackendDesignReport(
        backend_names=tuple(backend.name for backend in backends),
        future_backend_names=tuple(backend.name for backend in future_backends),
        optional_dependencies=dependencies,
        missing_capabilities=("real_training_execution", "model_loading", "artifact_upload"),
        limitations=(
            "real LoRA training is not implemented",
            "real QLoRA training is not implemented",
            "heavy ML dependencies are metadata only and not installed",
            "no subprocess, shell, network, upload, or hardware probing",
            "no plugin auto-discovery from installed packages",
        ),
        next_steps=(
            "define an explicit opt-in runner contract before execution",
            "add safe dependency probing only behind a caller-controlled flag",
            "review model, dataset, artifact, and evaluation policy before real training",
            "keep heavy dependencies outside Grona core",
        ),
        metadata={"plugin_status": OPTIONAL_TRAINING_PLUGIN_STATUS},
    )


def optional_training_dependency_specs() -> tuple[OptionalDependencySpec, ...]:
    """Return all known future optional training dependency metadata."""
    return dedupe_dependency_specs(
        (
            optional_dependency_torch(),
            optional_dependency_transformers(),
            optional_dependency_peft(),
            optional_dependency_accelerate(),
            optional_dependency_bitsandbytes(),
            optional_dependency_datasets(),
        )
    )


def optional_dependency_torch() -> OptionalDependencySpec:
    """Return metadata for the future torch dependency."""
    return OptionalDependencySpec(
        "torch",
        "torch",
        "future tensor runtime and model training substrate",
        ("lora", "qlora"),
        "future only: install an explicit training plugin, not Grona core",
        metadata={"heavy_dependency": True},
    )


def optional_dependency_transformers() -> OptionalDependencySpec:
    """Return metadata for the future transformers dependency."""
    return OptionalDependencySpec(
        "transformers",
        "transformers",
        "future model and tokenizer integration",
        ("lora", "qlora"),
        "future only: install an explicit training plugin, not Grona core",
        metadata={"heavy_dependency": True},
    )


def optional_dependency_peft() -> OptionalDependencySpec:
    """Return metadata for the future peft dependency."""
    return OptionalDependencySpec(
        "peft",
        "peft",
        "future LoRA adapter implementation",
        ("lora", "qlora"),
        "future only: install an explicit training plugin, not Grona core",
        metadata={"heavy_dependency": True},
    )


def optional_dependency_accelerate() -> OptionalDependencySpec:
    """Return metadata for the future accelerate dependency."""
    return OptionalDependencySpec(
        "accelerate",
        "accelerate",
        "future training device orchestration",
        ("lora", "qlora"),
        "future only: install an explicit training plugin, not Grona core",
        metadata={"heavy_dependency": True},
    )


def optional_dependency_bitsandbytes() -> OptionalDependencySpec:
    """Return metadata for the future bitsandbytes dependency."""
    return OptionalDependencySpec(
        "bitsandbytes",
        "bitsandbytes",
        "future quantized QLoRA optimizer/runtime support",
        ("qlora",),
        "future only: install an explicit QLoRA plugin, not Grona core",
        metadata={"heavy_dependency": True, "platform_sensitive": True},
    )


def optional_dependency_datasets() -> OptionalDependencySpec:
    """Return metadata for the future datasets dependency."""
    return OptionalDependencySpec(
        "datasets",
        "datasets",
        "future large dataset adapter support",
        ("lora", "qlora"),
        "future only: install an explicit training plugin, not Grona core",
        metadata={"heavy_dependency": True},
    )


def dedupe_dependency_specs(
    dependencies: Sequence[OptionalDependencySpec] | object,
) -> tuple[OptionalDependencySpec, ...]:
    """Return dependency specs de-duplicated by package in first-seen order."""
    seen: set[str] = set()
    result: list[OptionalDependencySpec] = []
    for dependency in dependencies:  # type: ignore[operator]
        if dependency.package not in seen:
            seen.add(dependency.package)
            result.append(dependency)
    return tuple(result)


def markdown_or_none(values: Sequence[str]) -> list[str]:
    """Return Markdown list lines with a none fallback."""
    if not values:
        return ["- none"]
    return [f"- {value}" for value in values]


def optional_training_required_artifacts() -> tuple[str, ...]:
    """Return artifact paths future training stubs expect to inspect."""
    return required_training_artifacts()
