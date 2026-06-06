"""Optional training backend boundary for future explicit trainer plugins."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from .feedback import Metadata
from .training import json_metadata
from .training_artifacts import TrainingArtifactBundle
from .training_dry_run import (
    DRY_RUN_OPTIONAL_ARTIFACTS,
    DRY_RUN_REQUIRED_ARTIFACTS,
    DryRunTrainer,
    DryRunTrainerConfig,
    TrainerBackendSpec,
    TrainingExecutionPlan,
    TrainingReadinessReport,
    create_dry_run_backend_spec,
    create_lora_cli_placeholder_backend_spec,
    create_qlora_cli_placeholder_backend_spec,
    dedupe_strings,
)
from .training_plan import TrainingPlan, TrainingRunConfig


class TrainingBackendCapability:
    """Stable capability labels for optional training backend metadata."""

    LORA = "lora"
    QLORA = "qlora"
    FULL_FINETUNE = "full_finetune"
    DRY_RUN = "dry_run"
    COMMAND_PREVIEW = "command_preview"
    QUANTIZATION = "quantization"
    GPU_REQUIRED = "gpu_required"
    CPU_POSSIBLE = "cpu_possible"

    ALL = (
        LORA,
        QLORA,
        FULL_FINETUNE,
        DRY_RUN,
        COMMAND_PREVIEW,
        QUANTIZATION,
        GPU_REQUIRED,
        CPU_POSSIBLE,
    )


@dataclass(frozen=True)
class TrainingBackendMetadata:
    """Descriptive optional backend metadata without loading or installing anything."""

    backend_name: str
    package_name: str = ""
    optional_extra: str = ""
    install_hint: str = ""
    supported_adapter_types: tuple[str, ...] = ()
    supported_quantization_modes: tuple[str, ...] = ()
    supported_artifact_formats: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        backend_name: str,
        package_name: str = "",
        optional_extra: str = "",
        install_hint: str = "",
        supported_adapter_types: Sequence[str] = (),
        supported_quantization_modes: Sequence[str] = (),
        supported_artifact_formats: Sequence[str] = (),
        limitations: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not backend_name:
            raise ValueError("training backend metadata backend_name cannot be empty")
        object.__setattr__(self, "backend_name", backend_name)
        object.__setattr__(self, "package_name", package_name)
        object.__setattr__(self, "optional_extra", optional_extra)
        object.__setattr__(self, "install_hint", install_hint)
        object.__setattr__(self, "supported_adapter_types", tuple(supported_adapter_types))
        object.__setattr__(self, "supported_quantization_modes", tuple(supported_quantization_modes))
        object.__setattr__(self, "supported_artifact_formats", tuple(supported_artifact_formats))
        object.__setattr__(self, "limitations", tuple(limitations))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible backend metadata."""
        return {
            "backend_name": self.backend_name,
            "package_name": self.package_name,
            "optional_extra": self.optional_extra,
            "install_hint": self.install_hint,
            "supported_adapter_types": list(self.supported_adapter_types),
            "supported_quantization_modes": list(self.supported_quantization_modes),
            "supported_artifact_formats": list(self.supported_artifact_formats),
            "limitations": list(self.limitations),
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return readable optional backend metadata."""
        return "\n".join(
            (
                f"Backend metadata: {self.backend_name}",
                f"Package: {self.package_name or 'none'}",
                f"Optional extra: {self.optional_extra or 'none'}",
                f"Install hint: {self.install_hint or 'not provided'}",
                f"Adapter types: {', '.join(self.supported_adapter_types) or 'none'}",
                f"Quantization modes: {', '.join(self.supported_quantization_modes) or 'none'}",
                f"Artifact formats: {', '.join(self.supported_artifact_formats) or 'none'}",
                "Limitations:",
                *markdown_or_none(self.limitations),
            )
        )


@dataclass(frozen=True)
class TrainingBackendDependencyReport:
    """Static dependency readiness report for an optional backend."""

    backend_name: str
    available: bool
    missing_dependencies: tuple[str, ...] = ()
    optional_dependencies: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        backend_name: str,
        available: bool,
        missing_dependencies: Sequence[str] = (),
        optional_dependencies: Sequence[str] = (),
        warnings: Sequence[str] = (),
        blockers: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not backend_name:
            raise ValueError("training backend dependency report backend_name cannot be empty")
        object.__setattr__(self, "backend_name", backend_name)
        object.__setattr__(self, "available", available)
        object.__setattr__(self, "missing_dependencies", tuple(missing_dependencies))
        object.__setattr__(self, "optional_dependencies", tuple(optional_dependencies))
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "blockers", tuple(blockers))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible dependency report."""
        return {
            "backend_name": self.backend_name,
            "available": self.available,
            "missing_dependencies": list(self.missing_dependencies),
            "optional_dependencies": list(self.optional_dependencies),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return readable dependency status."""
        return "\n".join(
            (
                f"Dependency report: {self.backend_name}",
                f"Available: {self.available}",
                f"Missing dependencies: {', '.join(self.missing_dependencies) or 'none'}",
                f"Optional dependencies: {', '.join(self.optional_dependencies) or 'none'}",
                "Warnings:",
                *markdown_or_none(self.warnings),
                "Blockers:",
                *markdown_or_none(self.blockers),
            )
        )


class TrainingBackend(Protocol):
    """Protocol for future optional training backends."""

    @property
    def name(self) -> str:
        """Return the stable backend name."""

    @property
    def backend_type(self) -> str:
        """Return the backend implementation type label."""

    @property
    def capabilities(self) -> tuple[str, ...]:
        """Return backend capability labels."""

    @property
    def required_artifacts(self) -> tuple[str, ...]:
        """Return artifact paths this backend expects."""

    @property
    def required_dependencies(self) -> tuple[str, ...]:
        """Return descriptive dependency names this backend would need."""

    def supports(self, config: TrainingRunConfig) -> bool:
        """Return whether this backend supports the given training config."""

    def check_readiness(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        config: DryRunTrainerConfig | None = None,
    ) -> TrainingReadinessReport:
        """Return readiness details without execution."""

    def build_execution_plan(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        config: DryRunTrainerConfig | None = None,
    ) -> TrainingExecutionPlan:
        """Return a dry-run execution plan without execution."""

    def check_dependencies(self) -> TrainingBackendDependencyReport:
        """Return static dependency status without importing packages."""


class PlaceholderTrainingBackend:
    """Safe placeholder backend that delegates to DryRunTrainer and never executes commands."""

    def __init__(
        self,
        spec: TrainerBackendSpec,
        capabilities: Sequence[str],
        metadata: TrainingBackendMetadata | None = None,
        dependency_report: TrainingBackendDependencyReport | None = None,
        required_artifacts: Sequence[str] = DRY_RUN_REQUIRED_ARTIFACTS,
    ) -> None:
        self._spec = spec
        self._capabilities = tuple(capabilities)
        self._metadata = metadata or metadata_from_spec(spec)
        self._dependency_report = dependency_report or dependency_report_from_spec(spec)
        self._required_artifacts = tuple(required_artifacts)

    @property
    def name(self) -> str:
        """Return the stable backend name."""
        return self._spec.name

    @property
    def backend_type(self) -> str:
        """Return the backend type label."""
        return self._spec.backend_type

    @property
    def capabilities(self) -> tuple[str, ...]:
        """Return deterministic backend capabilities."""
        return self._capabilities

    @property
    def required_artifacts(self) -> tuple[str, ...]:
        """Return required artifact paths."""
        return self._required_artifacts

    @property
    def required_dependencies(self) -> tuple[str, ...]:
        """Return descriptive dependency names."""
        return self._spec.required_python_packages

    @property
    def metadata(self) -> TrainingBackendMetadata:
        """Return optional backend metadata."""
        return self._metadata

    @property
    def spec(self) -> TrainerBackendSpec:
        """Return the dry-run trainer backend spec."""
        return self._spec

    def supports(self, config: TrainingRunConfig) -> bool:
        """Return whether the placeholder supports this config shape."""
        adapter_type = config.adapter.adapter_type
        if self._spec.supported_adapter_types and adapter_type not in self._spec.supported_adapter_types:
            return False
        if config.adapter.quantization != "none" and not self._spec.supports_quantization:
            return False
        return True

    def check_dependencies(self) -> TrainingBackendDependencyReport:
        """Return static dependency status without imports or environment probing."""
        return self._dependency_report

    def check_readiness(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        config: DryRunTrainerConfig | None = None,
    ) -> TrainingReadinessReport:
        """Return readiness details without training or command execution."""
        execution_plan = self.build_execution_plan(training_plan, artifact_bundle, config)
        return execution_plan.readiness

    def build_execution_plan(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        config: DryRunTrainerConfig | None = None,
    ) -> TrainingExecutionPlan:
        """Build a dry-run execution plan and include placeholder dependency blockers."""
        dry_run_config = config or DryRunTrainerConfig(backend_name=self.name)
        execution_plan = DryRunTrainer().create_execution_plan(
            training_plan,
            artifact_bundle,
            self._spec,
            dry_run_config,
        )
        dependency_report = self.check_dependencies()
        blockers = list(execution_plan.blockers)
        warnings = list(execution_plan.warnings)
        blockers.extend(dependency_report.blockers)
        warnings.extend(dependency_report.warnings)
        if not self.supports(training_plan.config):
            blockers.append(f"backend {self.name} does not support this training config")
        if not blockers:
            return execution_plan
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
                "dependency_report": dependency_report.to_dict(),
                "placeholder_backend": True,
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
                "dependency_report": dependency_report.to_dict(),
                "placeholder_backend": True,
                "executes_commands": False,
            },
        )

    def to_text(self) -> str:
        """Return readable backend summary."""
        return "\n".join(
            (
                f"Training backend: {self.name}",
                f"Type: {self.backend_type}",
                f"Capabilities: {', '.join(self.capabilities) or 'none'}",
                f"Required artifacts: {', '.join(self.required_artifacts) or 'none'}",
                f"Required dependencies: {', '.join(self.required_dependencies) or 'none'}",
                "Execution: placeholder only; no commands are executed.",
            )
        )


class TrainingBackendRegistry:
    """Deterministic registry for explicitly registered training backends."""

    def __init__(self, backends: Sequence[TrainingBackend] = ()) -> None:
        self._backends: dict[str, TrainingBackend] = {}
        for backend in backends:
            self.register(backend)

    def register(self, backend: TrainingBackend) -> None:
        """Register one backend by name."""
        if not backend.name:
            raise ValueError("training backend name cannot be empty")
        if backend.name in self._backends:
            raise ValueError(f"training backend already registered: {backend.name}")
        self._backends[backend.name] = backend

    def list_backends(self) -> tuple[TrainingBackend, ...]:
        """Return backends in deterministic name order."""
        return tuple(self._backends[name] for name in sorted(self._backends))

    def get(self, name: str) -> TrainingBackend:
        """Return a backend by name, raising KeyError when absent."""
        return self._backends[name]

    def find_by_adapter_type(self, adapter_type: str) -> tuple[TrainingBackend, ...]:
        """Return backends whose metadata supports an adapter type."""
        return tuple(
            backend
            for backend in self.list_backends()
            if adapter_type in supported_adapter_types_for_backend(backend)
        )

    def find_by_capability(self, capability: str) -> tuple[TrainingBackend, ...]:
        """Return backends with the requested capability label."""
        return tuple(backend for backend in self.list_backends() if capability in backend.capabilities)


def create_placeholder_training_backend(
    spec: TrainerBackendSpec,
    capabilities: Sequence[str],
    dependency_report: TrainingBackendDependencyReport | None = None,
) -> PlaceholderTrainingBackend:
    """Create a safe placeholder backend from a descriptive backend spec."""
    return PlaceholderTrainingBackend(
        spec,
        capabilities,
        metadata_from_spec(spec),
        dependency_report,
        DRY_RUN_REQUIRED_ARTIFACTS,
    )


def create_default_training_backend_registry() -> TrainingBackendRegistry:
    """Create deterministic placeholder backends for demos and tests."""
    registry = TrainingBackendRegistry()
    registry.register(create_dry_run_placeholder_backend())
    registry.register(create_lora_placeholder_backend())
    registry.register(create_qlora_placeholder_backend())
    return registry


def create_dry_run_placeholder_backend() -> PlaceholderTrainingBackend:
    """Return the default dry-run placeholder backend."""
    return create_placeholder_training_backend(
        create_dry_run_backend_spec(),
        (
            TrainingBackendCapability.DRY_RUN,
            TrainingBackendCapability.COMMAND_PREVIEW,
            TrainingBackendCapability.LORA,
            TrainingBackendCapability.QLORA,
            TrainingBackendCapability.QUANTIZATION,
            TrainingBackendCapability.CPU_POSSIBLE,
        ),
        TrainingBackendDependencyReport(
            "dry-run",
            True,
            warnings=("dry-run backend is a placeholder and does not train",),
            metadata={"static_check_only": True, "imports_packages": False},
        ),
    )


def create_lora_placeholder_backend() -> PlaceholderTrainingBackend:
    """Return a LoRA placeholder backend with static missing dependency blockers."""
    spec = create_lora_cli_placeholder_backend_spec()
    return create_placeholder_training_backend(
        spec,
        (
            TrainingBackendCapability.LORA,
            TrainingBackendCapability.COMMAND_PREVIEW,
            TrainingBackendCapability.CPU_POSSIBLE,
        ),
    )


def create_qlora_placeholder_backend() -> PlaceholderTrainingBackend:
    """Return a QLoRA placeholder backend with static missing dependency blockers."""
    spec = create_qlora_cli_placeholder_backend_spec()
    return create_placeholder_training_backend(
        spec,
        (
            TrainingBackendCapability.QLORA,
            TrainingBackendCapability.COMMAND_PREVIEW,
            TrainingBackendCapability.QUANTIZATION,
            TrainingBackendCapability.GPU_REQUIRED,
        ),
    )


def metadata_from_spec(spec: TrainerBackendSpec) -> TrainingBackendMetadata:
    """Return optional backend metadata derived from a dry-run backend spec."""
    extra = "training" if spec.required_python_packages else ""
    return TrainingBackendMetadata(
        backend_name=spec.name,
        package_name="grona",
        optional_extra=extra,
        install_hint="pip install grona[training]" if extra else "core package only",
        supported_adapter_types=spec.supported_adapter_types,
        supported_quantization_modes=("4bit-placeholder",) if spec.supports_quantization else ("none",),
        supported_artifact_formats=("jsonl", "json", "markdown", "text"),
        limitations=(
            "placeholder only",
            "no actual training",
            "no subprocess execution",
            "no package imports or environment probing",
            "no guarantee that future command previews are runnable",
        ),
        metadata={"from_trainer_backend_spec": True, **spec.metadata},
    )


def dependency_report_from_spec(spec: TrainerBackendSpec) -> TrainingBackendDependencyReport:
    """Return a static dependency report without importing optional packages."""
    missing = tuple(spec.required_python_packages)
    blockers = tuple(
        f"missing optional backend dependency: {dependency}" for dependency in missing
    )
    warnings = ["dependency report is static; no package imports or environment probing are performed"]
    if spec.required_commands:
        warnings.append("command requirements are descriptive only and are not checked")
    return TrainingBackendDependencyReport(
        spec.name,
        available=not missing,
        missing_dependencies=missing,
        optional_dependencies=missing,
        warnings=warnings,
        blockers=blockers,
        metadata={"static_check_only": True, "imports_packages": False},
    )


def supported_adapter_types_for_backend(backend: TrainingBackend) -> tuple[str, ...]:
    """Return supported adapter types from backend metadata when available."""
    metadata = getattr(backend, "metadata", None)
    if isinstance(metadata, TrainingBackendMetadata):
        return metadata.supported_adapter_types
    spec = getattr(backend, "spec", None)
    if isinstance(spec, TrainerBackendSpec):
        return spec.supported_adapter_types
    return ()


def markdown_or_none(values: Sequence[str]) -> list[str]:
    """Return Markdown list lines with a none fallback."""
    if not values:
        return ["- none"]
    return [f"- {value}" for value in values]


def all_training_backend_capabilities() -> tuple[str, ...]:
    """Return all known training backend capability labels."""
    return TrainingBackendCapability.ALL


def required_training_artifacts() -> tuple[str, ...]:
    """Return the artifact paths current placeholder backends can inspect."""
    return tuple(DRY_RUN_REQUIRED_ARTIFACTS + DRY_RUN_OPTIONAL_ARTIFACTS)
