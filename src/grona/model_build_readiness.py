"""Model-build readiness consolidation and local handoff planning layer."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps

from .experimental_training import ExperimentalLoRABackend, LoRATrainingSafetyConfig, build_demo_lora_training_inputs
from .feedback import Metadata
from .training import TrainingExample, json_metadata
from .training_artifacts import TrainingArtifactBundle
from .training_backends import TrainingBackend, create_default_training_backend_registry
from .training_dry_run import dedupe_strings
from .training_package import TrainingDatasetPackage
from .training_pipeline_audit import (
    TrainingPipelineAuditor,
    TrainingPipelineReadinessReport,
    TrainingPipelineStageStatus,
    validate_training_backend_contract,
)
from .training_plan import TrainingPlan, create_demo_training_plan_examples

MODEL_BUILD_READINESS_CREATED_AT = "2026-01-01T00:00:00+00:00"
MODEL_BUILD_ENVIRONMENT_STATUSES = ("ready", "warning", "blocked")


@dataclass(frozen=True)
class TrainingHardwareProfile:
    """Explicit user-described hardware profile; no hidden probing is performed."""

    name: str
    cpu_cores: int = 0
    ram_gb: float = 0
    gpu_count: int = 0
    gpu_name: str = ""
    gpu_vram_gb: float = 0
    cuda_available: bool = False
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        cpu_cores: int = 0,
        ram_gb: float = 0,
        gpu_count: int = 0,
        gpu_name: str = "",
        gpu_vram_gb: float = 0,
        cuda_available: bool = False,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not name:
            raise ValueError("training hardware profile name cannot be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "cpu_cores", int(cpu_cores))
        object.__setattr__(self, "ram_gb", float(ram_gb))
        object.__setattr__(self, "gpu_count", int(gpu_count))
        object.__setattr__(self, "gpu_name", gpu_name)
        object.__setattr__(self, "gpu_vram_gb", float(gpu_vram_gb))
        object.__setattr__(self, "cuda_available", bool(cuda_available))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible hardware metadata."""
        return {
            "name": self.name,
            "cpu_cores": self.cpu_cores,
            "ram_gb": self.ram_gb,
            "gpu_count": self.gpu_count,
            "gpu_name": self.gpu_name,
            "gpu_vram_gb": self.gpu_vram_gb,
            "cuda_available": self.cuda_available,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TrainingDependencyProfile:
    """Explicit dependency profile described by the caller without importing packages."""

    installed_packages: tuple[str, ...] = ()
    missing_packages: tuple[str, ...] = ()
    optional_packages: tuple[str, ...] = ()
    python_version: str = ""
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        installed_packages: Sequence[str] = (),
        missing_packages: Sequence[str] = (),
        optional_packages: Sequence[str] = (),
        python_version: str = "",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "installed_packages", tuple(sorted(set(installed_packages))))
        object.__setattr__(self, "missing_packages", tuple(sorted(set(missing_packages))))
        object.__setattr__(self, "optional_packages", tuple(sorted(set(optional_packages))))
        object.__setattr__(self, "python_version", python_version)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible dependency metadata."""
        return {
            "installed_packages": list(self.installed_packages),
            "missing_packages": list(self.missing_packages),
            "optional_packages": list(self.optional_packages),
            "python_version": self.python_version,
            "metadata": self.metadata,
        }

    def has_package(self, package: str) -> bool:
        """Return whether a package is explicitly listed as installed."""
        return package in self.installed_packages and package not in self.missing_packages


@dataclass(frozen=True)
class TrainingEnvironmentProfile:
    """Explicit training target profile combining hardware, dependencies, and notes."""

    name: str
    hardware: TrainingHardwareProfile
    dependencies: TrainingDependencyProfile
    os_label: str = "unspecified"
    notes: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        hardware: TrainingHardwareProfile,
        dependencies: TrainingDependencyProfile | None = None,
        os_label: str = "unspecified",
        notes: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not name:
            raise ValueError("training environment profile name cannot be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "hardware", hardware)
        object.__setattr__(self, "dependencies", dependencies or TrainingDependencyProfile())
        object.__setattr__(self, "os_label", os_label)
        object.__setattr__(self, "notes", tuple(notes))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible environment metadata."""
        return {
            "name": self.name,
            "hardware": self.hardware.to_dict(),
            "dependencies": self.dependencies.to_dict(),
            "os_label": self.os_label,
            "notes": list(self.notes),
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Return stable JSON for this environment profile."""
        return dumps(self.to_dict(), sort_keys=True)


@dataclass(frozen=True)
class TrainingHardwareRequirement:
    """Planning-only hardware and dependency requirement preset."""

    name: str
    min_cpu_cores: int = 0
    min_ram_gb: float = 0
    requires_gpu: bool = False
    min_gpu_vram_gb: float = 0
    required_dependencies: tuple[str, ...] = ()
    optional_dependencies: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        min_cpu_cores: int = 0,
        min_ram_gb: float = 0,
        requires_gpu: bool = False,
        min_gpu_vram_gb: float = 0,
        required_dependencies: Sequence[str] = (),
        optional_dependencies: Sequence[str] = (),
        limitations: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not name:
            raise ValueError("training hardware requirement name cannot be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "min_cpu_cores", int(min_cpu_cores))
        object.__setattr__(self, "min_ram_gb", float(min_ram_gb))
        object.__setattr__(self, "requires_gpu", bool(requires_gpu))
        object.__setattr__(self, "min_gpu_vram_gb", float(min_gpu_vram_gb))
        object.__setattr__(self, "required_dependencies", tuple(required_dependencies))
        object.__setattr__(self, "optional_dependencies", tuple(optional_dependencies))
        object.__setattr__(self, "limitations", tuple(limitations))
        object.__setattr__(self, "metadata", json_metadata(metadata or {"planning_only": True}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible requirement metadata."""
        return {
            "name": self.name,
            "min_cpu_cores": self.min_cpu_cores,
            "min_ram_gb": self.min_ram_gb,
            "requires_gpu": self.requires_gpu,
            "min_gpu_vram_gb": self.min_gpu_vram_gb,
            "required_dependencies": list(self.required_dependencies),
            "optional_dependencies": list(self.optional_dependencies),
            "limitations": list(self.limitations),
            "metadata": self.metadata,
        }

    @classmethod
    def cpu_dry_run(cls) -> TrainingHardwareRequirement:
        """Return conservative CPU dry-run planning requirements."""
        return cls(
            "cpu-dry-run",
            min_cpu_cores=2,
            min_ram_gb=4,
            limitations=("dry-run only", "does not train or load a model"),
        )

    @classmethod
    def small_lora(cls) -> TrainingHardwareRequirement:
        """Return planning metadata for a small future LoRA experiment."""
        return cls(
            "small-lora",
            min_cpu_cores=4,
            min_ram_gb=16,
            requires_gpu=False,
            min_gpu_vram_gb=0,
            required_dependencies=("torch", "transformers", "peft", "accelerate", "datasets"),
            optional_dependencies=("bitsandbytes",),
            limitations=("planning metadata only", "real requirements depend on model and sequence length"),
        )

    @classmethod
    def small_qlora(cls) -> TrainingHardwareRequirement:
        """Return planning metadata for a small future QLoRA experiment."""
        return cls(
            "small-qlora",
            min_cpu_cores=4,
            min_ram_gb=24,
            requires_gpu=True,
            min_gpu_vram_gb=10,
            required_dependencies=("torch", "transformers", "peft", "accelerate", "datasets", "bitsandbytes"),
            limitations=("planning metadata only", "CUDA/GPU compatibility still requires local validation"),
        )

    @classmethod
    def full_finetune_placeholder(cls) -> TrainingHardwareRequirement:
        """Return deliberately conservative placeholder requirements for full fine-tuning."""
        return cls(
            "full-finetune-placeholder",
            min_cpu_cores=8,
            min_ram_gb=64,
            requires_gpu=True,
            min_gpu_vram_gb=24,
            required_dependencies=("torch", "transformers", "accelerate", "datasets"),
            limitations=("placeholder only", "not supported by Grona yet", "not a promise that full fine-tuning will work"),
        )


@dataclass(frozen=True)
class TrainingEnvironmentReadinessReport:
    """Readiness result for one explicit environment profile and requirement preset."""

    ready: bool
    status: str
    profile: TrainingEnvironmentProfile
    requirement: TrainingHardwareRequirement
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    summary: Metadata = field(default_factory=dict)
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        ready: bool,
        status: str,
        profile: TrainingEnvironmentProfile,
        requirement: TrainingHardwareRequirement,
        warnings: Sequence[str] = (),
        blockers: Sequence[str] = (),
        summary: Mapping[str, object] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if status not in MODEL_BUILD_ENVIRONMENT_STATUSES:
            raise ValueError(f"unknown training environment readiness status: {status}")
        object.__setattr__(self, "ready", bool(ready))
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "profile", profile)
        object.__setattr__(self, "requirement", requirement)
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "blockers", tuple(blockers))
        object.__setattr__(self, "summary", json_metadata(summary or {}))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible environment readiness details."""
        return {
            "ready": self.ready,
            "status": self.status,
            "profile": self.profile.to_dict(),
            "requirement": self.requirement.to_dict(),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
            "summary": self.summary,
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return readable environment readiness output."""
        lines = [
            f"Training environment readiness: {self.status}",
            f"Profile: {self.profile.name}",
            f"Requirement: {self.requirement.name}",
            "Warnings:",
            *markdown_or_none(self.warnings),
            "Blockers:",
            *markdown_or_none(self.blockers),
        ]
        return "\n".join(lines)


class TrainingEnvironmentAuditor:
    """Audit explicit environment profiles without probing the local machine."""

    def audit(
        self,
        profile: TrainingEnvironmentProfile,
        requirement: TrainingHardwareRequirement,
    ) -> TrainingEnvironmentReadinessReport:
        """Return environment readiness for a described profile and planning preset."""
        blockers: list[str] = []
        warnings: list[str] = []
        hardware = profile.hardware
        dependencies = profile.dependencies
        if hardware.cpu_cores < requirement.min_cpu_cores:
            blockers.append(f"cpu cores below requirement: {hardware.cpu_cores} < {requirement.min_cpu_cores}")
        if hardware.ram_gb < requirement.min_ram_gb:
            blockers.append(f"RAM below requirement: {hardware.ram_gb}GB < {requirement.min_ram_gb}GB")
        if requirement.requires_gpu and hardware.gpu_count <= 0:
            blockers.append("GPU is required but profile has no GPU")
        if requirement.requires_gpu and not hardware.cuda_available:
            blockers.append("CUDA is required for this planning preset but is not marked available")
        if requirement.min_gpu_vram_gb and hardware.gpu_vram_gb < requirement.min_gpu_vram_gb:
            blockers.append(f"GPU VRAM below requirement: {hardware.gpu_vram_gb}GB < {requirement.min_gpu_vram_gb}GB")
        missing_required = tuple(
            package for package in requirement.required_dependencies if not dependencies.has_package(package)
        )
        blockers.extend(f"required dependency is not listed as installed: {package}" for package in missing_required)
        missing_optional = tuple(
            package for package in requirement.optional_dependencies if not dependencies.has_package(package)
        )
        warnings.extend(f"optional dependency is not listed as installed: {package}" for package in missing_optional)
        warnings.extend(requirement.limitations)
        ready = not blockers
        status = "blocked" if blockers else "warning" if warnings else "ready"
        return TrainingEnvironmentReadinessReport(
            ready=ready,
            status=status,
            profile=profile,
            requirement=requirement,
            warnings=dedupe_strings(warnings),
            blockers=dedupe_strings(blockers),
            summary={
                "profile_name": profile.name,
                "requirement_name": requirement.name,
                "hardware_ready": not any("requirement" in blocker or "VRAM" in blocker or "GPU" in blocker or "RAM" in blocker for blocker in blockers),
                "dependencies_ready": not missing_required,
                "performs_hidden_probe": False,
            },
            metadata={"auditor": "TrainingEnvironmentAuditor", "planning_only": True},
        )


@dataclass(frozen=True)
class LocalTrainingHandoffManifest:
    """Markdown handoff manifest for future local IDE training work."""

    repository_state_summary: str
    required_local_steps: tuple[str, ...]
    optional_dependencies: tuple[str, ...]
    expected_artifact_paths: tuple[str, ...]
    command_previews: tuple[str, ...]
    safety_gates: tuple[str, ...]
    blocked_operations: tuple[str, ...]
    manual_checklist: tuple[str, ...]
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        repository_state_summary: str,
        required_local_steps: Sequence[str] = (),
        optional_dependencies: Sequence[str] = (),
        expected_artifact_paths: Sequence[str] = (),
        command_previews: Sequence[str] = (),
        safety_gates: Sequence[str] = (),
        blocked_operations: Sequence[str] = (),
        manual_checklist: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "repository_state_summary", repository_state_summary)
        object.__setattr__(self, "required_local_steps", tuple(required_local_steps))
        object.__setattr__(self, "optional_dependencies", tuple(optional_dependencies))
        object.__setattr__(self, "expected_artifact_paths", tuple(expected_artifact_paths))
        object.__setattr__(self, "command_previews", tuple(command_previews))
        object.__setattr__(self, "safety_gates", tuple(safety_gates))
        object.__setattr__(self, "blocked_operations", tuple(blocked_operations))
        object.__setattr__(self, "manual_checklist", tuple(manual_checklist))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible handoff metadata."""
        return {
            "repository_state_summary": self.repository_state_summary,
            "required_local_steps": list(self.required_local_steps),
            "optional_dependencies": list(self.optional_dependencies),
            "expected_artifact_paths": list(self.expected_artifact_paths),
            "command_previews": list(self.command_previews),
            "safety_gates": list(self.safety_gates),
            "blocked_operations": list(self.blocked_operations),
            "manual_checklist": list(self.manual_checklist),
            "metadata": self.metadata,
        }

    def to_markdown(self) -> str:
        """Return a deterministic Markdown handoff checklist."""
        lines = [
            "# Local Training Handoff Manifest",
            "",
            "## Repository State",
            self.repository_state_summary,
            "",
            "## Required Local Steps",
            *markdown_or_none(self.required_local_steps),
            "",
            "## Optional Dependencies",
            *markdown_or_none(self.optional_dependencies),
            "",
            "## Expected Artifact Paths",
            *markdown_or_none(self.expected_artifact_paths),
            "",
            "## Safe Command Previews",
            *markdown_or_none(self.command_previews),
            "",
            "## Safety Gates",
            *markdown_or_none(self.safety_gates),
            "",
            "## Blocked Operations",
            *markdown_or_none(self.blocked_operations),
            "",
            "## Manual Checklist",
            *markdown_or_none(self.manual_checklist),
        ]
        return "\n".join(lines)


@dataclass(frozen=True)
class ModelBuildReadinessReport:
    """Consolidated readiness report for local handoff before real model training."""

    ready_for_real_training: bool
    ready_for_local_handoff: bool
    recommended_next_action: str
    pipeline_report: TrainingPipelineReadinessReport
    environment_report: TrainingEnvironmentReadinessReport
    backend_contract_status: TrainingPipelineStageStatus
    experimental_lora_readiness: Mapping[str, object]
    artifact_bundle_summary: Mapping[str, object]
    training_plan_validation: Mapping[str, object]
    handoff_manifest: LocalTrainingHandoffManifest
    blocked_reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    summary: Metadata = field(default_factory=dict)
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        ready_for_real_training: bool,
        ready_for_local_handoff: bool,
        recommended_next_action: str,
        pipeline_report: TrainingPipelineReadinessReport,
        environment_report: TrainingEnvironmentReadinessReport,
        backend_contract_status: TrainingPipelineStageStatus,
        experimental_lora_readiness: Mapping[str, object],
        artifact_bundle_summary: Mapping[str, object],
        training_plan_validation: Mapping[str, object],
        handoff_manifest: LocalTrainingHandoffManifest,
        blocked_reasons: Sequence[str] = (),
        warnings: Sequence[str] = (),
        summary: Mapping[str, object] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "ready_for_real_training", bool(ready_for_real_training))
        object.__setattr__(self, "ready_for_local_handoff", bool(ready_for_local_handoff))
        object.__setattr__(self, "recommended_next_action", recommended_next_action)
        object.__setattr__(self, "pipeline_report", pipeline_report)
        object.__setattr__(self, "environment_report", environment_report)
        object.__setattr__(self, "backend_contract_status", backend_contract_status)
        object.__setattr__(self, "experimental_lora_readiness", json_metadata(experimental_lora_readiness))
        object.__setattr__(self, "artifact_bundle_summary", json_metadata(artifact_bundle_summary))
        object.__setattr__(self, "training_plan_validation", json_metadata(training_plan_validation))
        object.__setattr__(self, "handoff_manifest", handoff_manifest)
        object.__setattr__(self, "blocked_reasons", tuple(blocked_reasons))
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "summary", json_metadata(summary or {}))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible model build readiness data."""
        return {
            "ready_for_real_training": self.ready_for_real_training,
            "ready_for_local_handoff": self.ready_for_local_handoff,
            "recommended_next_action": self.recommended_next_action,
            "pipeline_report": self.pipeline_report.to_dict(),
            "environment_report": self.environment_report.to_dict(),
            "backend_contract_status": self.backend_contract_status.to_dict(),
            "experimental_lora_readiness": self.experimental_lora_readiness,
            "artifact_bundle_summary": self.artifact_bundle_summary,
            "training_plan_validation": self.training_plan_validation,
            "handoff_manifest": self.handoff_manifest.to_dict(),
            "blocked_reasons": list(self.blocked_reasons),
            "warnings": list(self.warnings),
            "summary": self.summary,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Return stable JSON for this report."""
        return dumps(self.to_dict(), sort_keys=True)

    def to_text(self) -> str:
        """Return readable consolidated readiness details."""
        lines = [
            "Model build readiness report",
            f"Ready for real training: {self.ready_for_real_training}",
            f"Ready for local handoff: {self.ready_for_local_handoff}",
            f"Recommended next action: {self.recommended_next_action}",
            "",
            "Pipeline readiness:",
            self.pipeline_report.to_text(),
            "",
            "Environment readiness:",
            self.environment_report.to_text(),
            "",
            "Backend contract:",
            self.backend_contract_status.to_text(),
            "",
            "Blocked reasons:",
            *markdown_or_none(self.blocked_reasons),
            "Warnings:",
            *markdown_or_none(self.warnings),
        ]
        return "\n".join(lines)


class ModelBuildReadinessAuditor:
    """Build one consolidated model-build readiness report without execution."""

    def __init__(
        self,
        pipeline_auditor: TrainingPipelineAuditor | None = None,
        environment_auditor: TrainingEnvironmentAuditor | None = None,
    ) -> None:
        self.pipeline_auditor = pipeline_auditor or TrainingPipelineAuditor()
        self.environment_auditor = environment_auditor or TrainingEnvironmentAuditor()

    def audit(
        self,
        examples: Sequence[TrainingExample] = (),
        package: TrainingDatasetPackage | None = None,
        training_plan: TrainingPlan | None = None,
        artifact_bundle: TrainingArtifactBundle | None = None,
        backend: TrainingBackend | None = None,
        environment_profile: TrainingEnvironmentProfile | None = None,
        environment_requirement: TrainingHardwareRequirement | None = None,
        safety_config: LoRATrainingSafetyConfig | None = None,
    ) -> ModelBuildReadinessReport:
        """Return consolidated model-build readiness without loading or training anything."""
        if package is None or training_plan is None or artifact_bundle is None:
            demo_examples, demo_package, demo_plan, demo_bundle = build_model_build_demo_pipeline_inputs()
            examples = tuple(examples) or demo_examples
            package = package or demo_package
            training_plan = training_plan or demo_plan
            artifact_bundle = artifact_bundle or demo_bundle
        backend = backend or ExperimentalLoRABackend(dependency_finder=lambda _package: None)
        safety = safety_config or LoRATrainingSafetyConfig()
        environment = environment_profile or create_cpu_only_demo_environment()
        requirement = environment_requirement or TrainingHardwareRequirement.cpu_dry_run()
        pipeline_report = self.pipeline_auditor.audit(examples, package, artifact_bundle, training_plan, backend, safety)
        environment_report = self.environment_auditor.audit(environment, requirement)
        backend_status = validate_training_backend_contract(backend, training_plan, artifact_bundle)
        experimental_lora_readiness = build_experimental_lora_readiness(backend, training_plan, artifact_bundle, safety)
        handoff_manifest = build_local_training_handoff_manifest(artifact_bundle, backend, requirement)
        blocked_reasons = collect_model_build_blockers(
            pipeline_report,
            environment_report,
            backend_status,
            experimental_lora_readiness,
        )
        warnings = collect_model_build_warnings(pipeline_report, environment_report, experimental_lora_readiness)
        artifact_summary = artifact_bundle.summary()
        validation = training_plan.validation.to_dict()
        ready_for_local_handoff = local_handoff_ready(pipeline_report, artifact_bundle, training_plan)
        ready_for_real_training = False
        recommended = recommended_next_action(ready_for_local_handoff, environment_report, blocked_reasons)
        return ModelBuildReadinessReport(
            ready_for_real_training=ready_for_real_training,
            ready_for_local_handoff=ready_for_local_handoff,
            recommended_next_action=recommended,
            pipeline_report=pipeline_report,
            environment_report=environment_report,
            backend_contract_status=backend_status,
            experimental_lora_readiness=experimental_lora_readiness,
            artifact_bundle_summary=artifact_summary,
            training_plan_validation=validation,
            handoff_manifest=handoff_manifest,
            blocked_reasons=blocked_reasons,
            warnings=warnings,
            summary={
                "artifact_count": artifact_summary.get("artifact_count", 0),
                "training_plan_valid": validation.get("valid", False),
                "environment_status": environment_report.status,
                "real_training_blocked_by_default": True,
                "local_handoff_ready": ready_for_local_handoff,
            },
            metadata={
                "auditor": "ModelBuildReadinessAuditor",
                "created_at": MODEL_BUILD_READINESS_CREATED_AT,
                "executes_training": False,
                "loads_models": False,
                "performs_network_calls": False,
            },
        )


def build_model_build_demo_pipeline_inputs() -> tuple[tuple[TrainingExample, ...], TrainingDatasetPackage, TrainingPlan, TrainingArtifactBundle]:
    """Build deterministic LoRA-shaped demo inputs for model-build readiness."""
    examples = create_demo_training_plan_examples()
    package, plan, bundle = build_demo_lora_training_inputs()
    return examples, package, plan, bundle


def build_experimental_lora_readiness(
    backend: TrainingBackend,
    training_plan: TrainingPlan,
    artifact_bundle: TrainingArtifactBundle,
    safety_config: LoRATrainingSafetyConfig,
) -> dict[str, object]:
    """Return experimental LoRA readiness metadata when the backend exposes it."""
    prepare = getattr(backend, "prepare_training_job", None)
    if prepare is None:
        return {"checked": False, "reason": "backend does not expose experimental LoRA job preparation"}
    _job, readiness = prepare(training_plan, artifact_bundle, "outputs/experimental-lora", safety_config)
    return {"checked": True, "readiness": readiness.to_dict()}


def build_local_training_handoff_manifest(
    artifact_bundle: TrainingArtifactBundle,
    backend: TrainingBackend,
    requirement: TrainingHardwareRequirement,
) -> LocalTrainingHandoffManifest:
    """Build a deterministic local handoff manifest without writing files."""
    optional_dependencies = tuple(
        dedupe_strings(tuple(getattr(backend, "required_dependencies", ())) + requirement.required_dependencies + requirement.optional_dependencies)
    )
    return LocalTrainingHandoffManifest(
        repository_state_summary="Grona has deterministic training-data packaging, artifact building, dry-run planning, backend boundaries, pipeline audit, and model-build readiness reporting. Real training is still blocked.",
        required_local_steps=(
            "clone the public repository locally",
            "install core development dependencies",
            "run lint and tests before changing training code",
            "run readiness demos before attempting backend implementation",
            "review generated in-memory artifact paths before writing anything locally",
        ),
        optional_dependencies=optional_dependencies,
        expected_artifact_paths=artifact_bundle.artifact_paths(),
        command_previews=(
            "pip install -e .[dev]",
            "pytest",
            "ruff check .",
            "python -m grona --model-build-readiness-demo",
            "python -m grona --training-pipeline-audit-demo",
            "python -m grona --experimental-lora-backend-demo",
            "python -m grona --training-artifact-demo",
        ),
        safety_gates=(
            "real training must require an explicit safety config",
            "model and dataset downloads stay disabled by default",
            "heavy ML dependencies stay optional and future-only",
            "artifact writes must be explicit caller actions",
        ),
        blocked_operations=(
            "model training",
            "model loading",
            "subprocess or shell execution",
            "network calls",
            "downloads or uploads",
            "file writes by default",
        ),
        manual_checklist=(
            "confirm local hardware profile and VRAM honestly",
            "install optional ML dependencies only in a local environment",
            "verify dataset and base model licenses",
            "keep dry-run artifact review before any future real backend call",
            "add local-only tests around any new trainer before enabling execution gates",
        ),
        metadata={"manifest_version": 1, "executes_commands": False},
    )


def model_build_lifecycle_markdown() -> str:
    """Return deterministic Markdown for the full model-build lifecycle."""
    return "\n".join(
        (
            "# Model Build Readiness Lifecycle",
            "",
            "```text",
            "reviewed traces -> training examples -> dataset package -> artifacts -> training plan -> dry-run -> backend boundary -> environment readiness -> local handoff -> future real training",
            "```",
            "",
            "Current status: local handoff can be prepared, but future real training remains blocked by default.",
        )
    )


def create_cpu_only_demo_environment() -> TrainingEnvironmentProfile:
    """Return deterministic CPU-only demo environment metadata."""
    return TrainingEnvironmentProfile(
        "cpu-only-demo",
        TrainingHardwareProfile("cpu-only-demo-hardware", cpu_cores=6, ram_gb=32, metadata={"example": "Ryzen 5 3600 style desktop"}),
        TrainingDependencyProfile(installed_packages=(), python_version="3.12", metadata={"probed": False}),
        os_label="Windows desktop / WSL2-friendly",
        notes=("CPU dry-run and readiness demos only",),
    )


def create_small_gpu_demo_environment() -> TrainingEnvironmentProfile:
    """Return deterministic small GPU planning profile."""
    packages = ("torch", "transformers", "peft", "accelerate", "datasets")
    return TrainingEnvironmentProfile(
        "small-gpu-demo",
        TrainingHardwareProfile("small-gpu-demo-hardware", cpu_cores=8, ram_gb=32, gpu_count=1, gpu_name="planning GPU", gpu_vram_gb=12, cuda_available=True),
        TrainingDependencyProfile(installed_packages=packages, optional_packages=("bitsandbytes",), python_version="3.12"),
        os_label="local Linux/WSL2 planning profile",
        notes=("planning metadata only",),
    )


def create_missing_dependencies_demo_environment() -> TrainingEnvironmentProfile:
    """Return deterministic environment profile with missing optional training dependencies."""
    return TrainingEnvironmentProfile(
        "missing-dependencies-demo",
        TrainingHardwareProfile("missing-dependencies-demo-hardware", cpu_cores=4, ram_gb=16),
        TrainingDependencyProfile(missing_packages=("torch", "transformers", "peft", "accelerate", "datasets", "bitsandbytes"), python_version="3.12"),
        os_label="unspecified local profile",
        notes=("intentionally incomplete dependency profile",),
    )


def create_user_described_local_environment_profile(
    cpu_cores: int,
    ram_gb: float,
    gpu_name: str = "",
    gpu_vram_gb: float = 0,
    installed_packages: Sequence[str] = (),
    os_label: str = "user-described local environment",
) -> TrainingEnvironmentProfile:
    """Return a profile from user-described values without probing the machine."""
    return TrainingEnvironmentProfile(
        "user-described-local-environment",
        TrainingHardwareProfile(
            "user-described-local-hardware",
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            gpu_count=1 if gpu_name else 0,
            gpu_name=gpu_name,
            gpu_vram_gb=gpu_vram_gb,
            cuda_available=bool(gpu_name and gpu_vram_gb),
        ),
        TrainingDependencyProfile(installed_packages=installed_packages),
        os_label=os_label,
        notes=("values are caller-described and not automatically probed",),
    )


def collect_model_build_blockers(
    pipeline_report: TrainingPipelineReadinessReport,
    environment_report: TrainingEnvironmentReadinessReport,
    backend_status: TrainingPipelineStageStatus,
    experimental_lora_readiness: Mapping[str, object],
) -> tuple[str, ...]:
    """Collect blockers across model-build layers."""
    blockers: list[str] = []
    blockers.extend(pipeline_report.blockers)
    blockers.extend(f"environment: {reason}" for reason in environment_report.blockers)
    if backend_status.status == "blocked":
        blockers.extend(f"backend: {reason}" for reason in backend_status.reasons)
    readiness = experimental_lora_readiness.get("readiness")
    if isinstance(readiness, Mapping):
        blockers.extend(f"experimental_lora: {reason}" for reason in readiness.get("blockers", ()))
    blockers.append("real training remains blocked until an explicit local trainer implementation and safety review exist")
    return dedupe_strings(blockers)


def collect_model_build_warnings(
    pipeline_report: TrainingPipelineReadinessReport,
    environment_report: TrainingEnvironmentReadinessReport,
    experimental_lora_readiness: Mapping[str, object],
) -> tuple[str, ...]:
    """Collect warnings across model-build layers."""
    warnings: list[str] = []
    warnings.extend(pipeline_report.warnings)
    warnings.extend(f"environment: {warning}" for warning in environment_report.warnings)
    readiness = experimental_lora_readiness.get("readiness")
    if isinstance(readiness, Mapping):
        warnings.extend(f"experimental_lora: {warning}" for warning in readiness.get("warnings", ()))
    return dedupe_strings(warnings)


def local_handoff_ready(
    pipeline_report: TrainingPipelineReadinessReport,
    artifact_bundle: TrainingArtifactBundle,
    training_plan: TrainingPlan,
) -> bool:
    """Return whether deterministic artifacts and config are complete enough for local handoff."""
    stage_names = {stage.stage: stage.status for stage in pipeline_report.stage_statuses}
    required_ok = all(
        stage_names.get(stage) == "passed"
        for stage in ("reviewed_trace_examples", "training_dataset_package", "training_artifacts", "training_plan", "dry_run_trainer", "provenance", "license", "validation", "execution")
    )
    return required_ok and bool(artifact_bundle.artifacts) and training_plan.validation.valid


def recommended_next_action(
    ready_for_local_handoff: bool,
    environment_report: TrainingEnvironmentReadinessReport,
    blockers: Sequence[str],
) -> str:
    """Return a deterministic next-action hint."""
    if not ready_for_local_handoff:
        return "finish deterministic pipeline artifacts before moving to local development"
    if not environment_report.ready:
        return "move to a local IDE and fill the explicit environment/dependency gaps before trainer work"
    if blockers:
        return "use local IDE handoff for explicit-only trainer implementation; keep real training disabled"
    return "review safety gates before any future explicit trainer implementation"


def markdown_or_none(values: Sequence[str]) -> list[str]:
    """Return Markdown list lines with a none fallback."""
    if not values:
        return ["- none"]
    return [f"- {value}" for value in values]


def build_demo_model_build_readiness_report() -> ModelBuildReadinessReport:
    """Return deterministic model-build readiness demo report."""
    backend = ExperimentalLoRABackend(dependency_finder=lambda _package: None)
    return ModelBuildReadinessAuditor().audit(
        backend=backend,
        environment_profile=create_cpu_only_demo_environment(),
        environment_requirement=TrainingHardwareRequirement.cpu_dry_run(),
        safety_config=LoRATrainingSafetyConfig(),
    )
