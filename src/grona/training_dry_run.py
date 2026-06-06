"""Dry-run trainer interface foundation for future explicit training backends."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps

from .feedback import Metadata
from .training import json_metadata
from .training_artifacts import (
    TrainingArtifactBundle,
    TrainingArtifactBuilder,
)
from .training_package import TrainingDatasetPackage, build_training_dataset_package
from .training_plan import TrainingPlan, build_demo_training_plan, create_demo_training_plan_examples

DEFAULT_DRY_RUN_CREATED_AT = "2026-01-01T00:00:00+00:00"
DEFAULT_DRY_RUN_PLAN_ID = "training-dry-run:demo-training-plan-config-only:dry-run"
DRY_RUN_REQUIRED_ARTIFACTS = (
    "config/training_config.json",
    "data/train.jsonl",
    "manifests/training_export_manifest.json",
)
DRY_RUN_OPTIONAL_ARTIFACTS = (
    "data/validation.jsonl",
    "data/test.jsonl",
    "manifests/dataset_manifest.json",
    "docs/dataset_card.md",
    "docs/model_card.md",
    "docs/safety_notes.md",
    "README.md",
)
TRAINING_PLACEHOLDER_MODULE = "grona_train_placeholder"


@dataclass(frozen=True)
class TrainerBackendSpec:
    """Specification for a future trainer backend, without probing or executing it."""

    name: str
    backend_type: str
    description: str
    required_commands: tuple[str, ...] = ()
    required_python_packages: tuple[str, ...] = ()
    supported_adapter_types: tuple[str, ...] = ()
    supports_quantization: bool = False
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        backend_type: str,
        description: str,
        required_commands: Sequence[str] = (),
        required_python_packages: Sequence[str] = (),
        supported_adapter_types: Sequence[str] = (),
        supports_quantization: bool = False,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not name:
            raise ValueError("trainer backend name cannot be empty")
        if not backend_type:
            raise ValueError("trainer backend type cannot be empty")
        if not description:
            raise ValueError("trainer backend description cannot be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "backend_type", backend_type)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "required_commands", tuple(required_commands))
        object.__setattr__(self, "required_python_packages", tuple(required_python_packages))
        object.__setattr__(self, "supported_adapter_types", tuple(supported_adapter_types))
        object.__setattr__(self, "supports_quantization", supports_quantization)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible backend metadata."""
        return {
            "name": self.name,
            "backend_type": self.backend_type,
            "description": self.description,
            "required_commands": list(self.required_commands),
            "required_python_packages": list(self.required_python_packages),
            "supported_adapter_types": list(self.supported_adapter_types),
            "supports_quantization": self.supports_quantization,
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return a readable backend summary."""
        return "\n".join(
            (
                f"Trainer backend: {self.name}",
                f"Type: {self.backend_type}",
                self.description,
                f"Commands: {', '.join(self.required_commands) or 'none'}",
                f"Python packages: {', '.join(self.required_python_packages) or 'none'}",
                f"Adapter types: {', '.join(self.supported_adapter_types) or 'none'}",
                f"Supports quantization: {self.supports_quantization}",
            )
        )


@dataclass(frozen=True)
class DryRunTrainerConfig:
    """Conservative validation switches for dry-run training plans."""

    backend_name: str = "dry-run"
    allow_missing_optional_artifacts: bool = False
    require_validation_passed: bool = True
    require_non_empty_train_split: bool = True
    require_model_license: bool = True
    require_dataset_manifest: bool = True
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        backend_name: str = "dry-run",
        allow_missing_optional_artifacts: bool = False,
        require_validation_passed: bool = True,
        require_non_empty_train_split: bool = True,
        require_model_license: bool = True,
        require_dataset_manifest: bool = True,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not backend_name:
            raise ValueError("dry-run trainer backend_name cannot be empty")
        object.__setattr__(self, "backend_name", backend_name)
        object.__setattr__(self, "allow_missing_optional_artifacts", allow_missing_optional_artifacts)
        object.__setattr__(self, "require_validation_passed", require_validation_passed)
        object.__setattr__(self, "require_non_empty_train_split", require_non_empty_train_split)
        object.__setattr__(self, "require_model_license", require_model_license)
        object.__setattr__(self, "require_dataset_manifest", require_dataset_manifest)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible config metadata."""
        return {
            "backend_name": self.backend_name,
            "allow_missing_optional_artifacts": self.allow_missing_optional_artifacts,
            "require_validation_passed": self.require_validation_passed,
            "require_non_empty_train_split": self.require_non_empty_train_split,
            "require_model_license": self.require_model_license,
            "require_dataset_manifest": self.require_dataset_manifest,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TrainingReadinessReport:
    """Readiness result for a dry-run training plan preview."""

    ready: bool
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    artifact_count: int = 0
    required_artifacts_present: bool = False
    training_config_valid: bool = False
    train_examples_count: int = 0
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        ready: bool,
        warnings: Sequence[str] = (),
        blockers: Sequence[str] = (),
        artifact_count: int = 0,
        required_artifacts_present: bool = False,
        training_config_valid: bool = False,
        train_examples_count: int = 0,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "ready", ready)
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "blockers", tuple(blockers))
        object.__setattr__(self, "artifact_count", artifact_count)
        object.__setattr__(self, "required_artifacts_present", required_artifacts_present)
        object.__setattr__(self, "training_config_valid", training_config_valid)
        object.__setattr__(self, "train_examples_count", train_examples_count)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible readiness metadata."""
        return {
            "ready": self.ready,
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
            "artifact_count": self.artifact_count,
            "required_artifacts_present": self.required_artifacts_present,
            "training_config_valid": self.training_config_valid,
            "train_examples_count": self.train_examples_count,
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return readable readiness details."""
        lines = [
            f"Training readiness: {'ready' if self.ready else 'blocked'}",
            f"Artifacts: {self.artifact_count}",
            f"Required artifacts present: {self.required_artifacts_present}",
            f"Training config valid: {self.training_config_valid}",
            f"Train examples: {self.train_examples_count}",
            "Warnings:",
        ]
        lines.extend(markdown_or_none(self.warnings))
        lines.append("Blockers:")
        lines.extend(markdown_or_none(self.blockers))
        return "\n".join(lines)


@dataclass(frozen=True)
class TrainingExecutionPlan:
    """Deterministic dry-run execution plan. Command previews are never executed."""

    plan_id: str
    created_at: str
    training_run_config: dict[str, object]
    artifact_bundle_summary: dict[str, object]
    backend: TrainerBackendSpec
    command_preview: tuple[str, ...]
    environment_notes: tuple[str, ...]
    warnings: tuple[str, ...]
    blocked: bool
    blockers: tuple[str, ...]
    readiness: TrainingReadinessReport
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        plan_id: str,
        created_at: str,
        training_run_config: Mapping[str, object],
        artifact_bundle_summary: Mapping[str, object],
        backend: TrainerBackendSpec,
        command_preview: Sequence[str],
        environment_notes: Sequence[str],
        warnings: Sequence[str],
        blocked: bool,
        blockers: Sequence[str],
        readiness: TrainingReadinessReport,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not plan_id:
            raise ValueError("training execution plan_id cannot be empty")
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "training_run_config", json_metadata(training_run_config))
        object.__setattr__(self, "artifact_bundle_summary", json_metadata(artifact_bundle_summary))
        object.__setattr__(self, "backend", backend)
        object.__setattr__(self, "command_preview", tuple(command_preview))
        object.__setattr__(self, "environment_notes", tuple(environment_notes))
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "blocked", blocked)
        object.__setattr__(self, "blockers", tuple(blockers))
        object.__setattr__(self, "readiness", readiness)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible execution plan."""
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "training_run_config": self.training_run_config,
            "artifact_bundle_summary": self.artifact_bundle_summary,
            "backend": self.backend.to_dict(),
            "command_preview": list(self.command_preview),
            "environment_notes": list(self.environment_notes),
            "warnings": list(self.warnings),
            "blocked": self.blocked,
            "blockers": list(self.blockers),
            "readiness": self.readiness.to_dict(),
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Return stable JSON for the execution plan."""
        return dumps(self.to_dict(), sort_keys=True)

    def to_text(self) -> str:
        """Return a readable dry-run execution plan preview."""
        return "\n\n".join(
            (
                f"Training execution plan: {self.plan_id}",
                f"Created at: {self.created_at}",
                "Execution: dry-run only; command preview is not executed.",
                self.backend.to_text(),
                self.readiness.to_text(),
                "Command preview:\n" + command_preview_text(self.command_preview),
            )
        )


class DryRunTrainer:
    """Validate artifacts and produce command previews without training anything."""

    def create_execution_plan(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        backend: TrainerBackendSpec | None = None,
        config: DryRunTrainerConfig | None = None,
        created_at: str = DEFAULT_DRY_RUN_CREATED_AT,
    ) -> TrainingExecutionPlan:
        """Return a dry-run execution plan without subprocess, filesystem, or network access."""
        backend_spec = backend or create_dry_run_backend_spec()
        dry_run_config = config or DryRunTrainerConfig(backend_name=backend_spec.name)
        warnings, blockers = self._validate(training_plan, artifact_bundle, backend_spec, dry_run_config)
        readiness = TrainingReadinessReport(
            ready=not blockers,
            warnings=warnings,
            blockers=blockers,
            artifact_count=len(artifact_bundle.artifacts),
            required_artifacts_present=not any(blocker.startswith("missing required artifact") for blocker in blockers),
            training_config_valid=training_plan.validation.valid,
            train_examples_count=train_examples_count(training_plan),
            metadata={"config": dry_run_config.to_dict(), "dry_run_only": True},
        )
        run_name = str(training_plan.config.run_name)
        plan_id = f"training-dry-run:{run_name}:{backend_spec.name}"
        return TrainingExecutionPlan(
            plan_id=plan_id,
            created_at=created_at,
            training_run_config=training_plan.config.to_dict(),
            artifact_bundle_summary=artifact_bundle.summary(),
            backend=backend_spec,
            command_preview=build_training_command_preview(training_plan, backend_spec),
            environment_notes=environment_notes_for_backend(backend_spec),
            warnings=warnings,
            blocked=bool(blockers),
            blockers=blockers,
            readiness=readiness,
            metadata={"trainer": "DryRunTrainer", "dry_run_only": True},
        )

    def _validate(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        backend: TrainerBackendSpec,
        config: DryRunTrainerConfig,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        warnings = list(training_plan.validation.warnings)
        warnings.append("dry-run only; no training command will be executed")
        blockers: list[str] = []
        artifact_paths = set(artifact_bundle.artifact_paths())
        required = list(DRY_RUN_REQUIRED_ARTIFACTS)
        if config.require_dataset_manifest:
            required.append("manifests/dataset_manifest.json")
        if not config.allow_missing_optional_artifacts:
            required.extend(path for path in DRY_RUN_OPTIONAL_ARTIFACTS if path not in required)
        for path in required:
            if path not in artifact_paths:
                blockers.append(f"missing required artifact: {path}")
        if config.require_validation_passed and not training_plan.validation.valid:
            blockers.append("training run config validation did not pass")
        count = train_examples_count(training_plan)
        if config.require_non_empty_train_split and count <= 0:
            blockers.append("train split is empty")
        if config.require_model_license and missing_license(str(training_plan.config.base_model.license)):
            blockers.append("base model license is missing")
        adapter_type = training_plan.config.adapter.adapter_type
        if backend.supported_adapter_types and adapter_type not in backend.supported_adapter_types:
            blockers.append(f"backend {backend.name} does not support adapter type: {adapter_type}")
        if training_plan.config.adapter.quantization != "none" and not backend.supports_quantization:
            blockers.append(f"backend {backend.name} does not support quantization previews")
        if backend.required_commands:
            warnings.append("backend command requirements are descriptive only and are not checked")
        if backend.required_python_packages:
            warnings.append("backend package requirements are descriptive only and are not imported")
        return dedupe_strings(warnings), dedupe_strings(blockers)


def create_dry_run_backend_spec() -> TrainerBackendSpec:
    """Return the deterministic default dry-run backend specification."""
    return TrainerBackendSpec(
        name="dry-run",
        backend_type="dry_run",
        description="Default in-memory dry-run backend. It never executes commands or trains models.",
        supported_adapter_types=("lora", "qlora", "full_finetune_placeholder"),
        supports_quantization=True,
        metadata={"executes_commands": False, "trains_model": False},
    )


def create_lora_cli_placeholder_backend_spec() -> TrainerBackendSpec:
    """Return a placeholder LoRA CLI backend specification for future review."""
    return TrainerBackendSpec(
        name="lora-cli-placeholder",
        backend_type="lora_cli_placeholder",
        description="Placeholder for a future explicit LoRA CLI runner. Not implemented.",
        required_commands=("python",),
        required_python_packages=("torch", "transformers", "peft"),
        supported_adapter_types=("lora",),
        supports_quantization=False,
        metadata={"placeholder": True, "executes_commands": False, "trains_model": False},
    )


def create_qlora_cli_placeholder_backend_spec() -> TrainerBackendSpec:
    """Return a placeholder QLoRA CLI backend specification for future review."""
    return TrainerBackendSpec(
        name="qlora-cli-placeholder",
        backend_type="qlora_cli_placeholder",
        description="Placeholder for a future explicit QLoRA CLI runner. Not implemented.",
        required_commands=("python",),
        required_python_packages=("torch", "transformers", "peft", "bitsandbytes"),
        supported_adapter_types=("qlora",),
        supports_quantization=True,
        metadata={"placeholder": True, "executes_commands": False, "trains_model": False},
    )


def build_training_command_preview(
    training_plan: TrainingPlan,
    backend: TrainerBackendSpec,
) -> tuple[str, ...]:
    """Return deterministic placeholder arguments for a future trainer command."""
    return (
        "python",
        "-m",
        TRAINING_PLACEHOLDER_MODULE,
        "--backend",
        backend.name,
        "--config",
        "config/training_config.json",
        "--train",
        "data/train.jsonl",
        "--validation",
        "data/validation.jsonl",
        "--test",
        "data/test.jsonl",
        "--output-dir",
        f"outputs/{training_plan.config.run_name}",
        "--dry-run-placeholder-not-implemented",
    )


def build_demo_training_execution_plan() -> TrainingExecutionPlan:
    """Build the deterministic dry-run trainer demo plan."""
    package = build_training_dataset_package(
        create_demo_training_plan_examples(),
        dataset_name="demo-training-dry-run-package",
        description="Reviewed examples for a dry-run trainer interface demo.",
        metadata={"demo": "training_dry_run", "config_only": True},
    )
    plan = build_demo_training_plan(package)
    bundle = TrainingArtifactBuilder().build(package, plan, name="demo-training-dry-run-bundle")
    return DryRunTrainer().create_execution_plan(
        plan,
        bundle,
        create_dry_run_backend_spec(),
        DryRunTrainerConfig(backend_name="dry-run"),
    )


def build_demo_training_dry_run_inputs() -> tuple[TrainingDatasetPackage, TrainingPlan, TrainingArtifactBundle]:
    """Return deterministic demo inputs for examples and tests."""
    package = build_training_dataset_package(
        create_demo_training_plan_examples(),
        dataset_name="demo-training-dry-run-package",
        description="Reviewed examples for a dry-run trainer interface demo.",
        metadata={"demo": "training_dry_run", "config_only": True},
    )
    plan = build_demo_training_plan(package)
    bundle = TrainingArtifactBuilder().build(package, plan, name="demo-training-dry-run-bundle")
    return package, plan, bundle


def environment_notes_for_backend(backend: TrainerBackendSpec) -> tuple[str, ...]:
    """Return notes that make backend requirements explicit without checking them."""
    notes = [
        "No environment probing is performed by the dry-run trainer.",
        "No subprocess is spawned and no command is executed.",
        "Command preview is a placeholder for future explicit trainer integration.",
    ]
    if backend.required_commands:
        notes.append(f"Future command requirements: {', '.join(backend.required_commands)}")
    if backend.required_python_packages:
        notes.append(f"Future package requirements: {', '.join(backend.required_python_packages)}")
    return tuple(notes)


def train_examples_count(training_plan: TrainingPlan) -> int:
    """Return train split example count from a training plan manifest."""
    return int(training_plan.config.dataset_manifest.split_counts.get("train", 0))


def missing_license(value: str) -> bool:
    """Return whether a license string is absent or unknown."""
    return not value or value == "unknown"


def command_preview_text(command_preview: Sequence[str]) -> str:
    """Return shell-like readable command preview without implying execution."""
    return " ".join(command_preview)


def markdown_or_none(values: Sequence[str]) -> list[str]:
    """Return list lines for readable text output."""
    if not values:
        return ["- none"]
    return [f"- {value}" for value in values]


def dedupe_strings(values: Sequence[str]) -> tuple[str, ...]:
    """Return strings in first-seen order without duplicates."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)
