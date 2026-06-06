"""Experimental LoRA backend skeleton that prepares guarded job descriptions only."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from importlib.util import find_spec
from json import dumps

from ..feedback import Metadata
from ..training import json_metadata
from ..training_artifacts import TrainingArtifactBuilder, TrainingArtifactBundle
from ..training_backends import (
    TrainingBackendCapability,
    TrainingBackendDependencyReport,
    TrainingBackendMetadata,
)
from ..training_dry_run import (
    DRY_RUN_REQUIRED_ARTIFACTS,
    DryRunTrainerConfig,
    TrainingReadinessReport,
    dedupe_strings,
)
from ..training_package import DatasetCardDraft, TrainingDatasetPackage, build_training_dataset_package
from ..training_plan import (
    AdapterTrainingSpec,
    BaseModelSpec,
    ModelCardDraft,
    TrainingPlan,
    TrainingRunConfig,
    TrainingRunValidator,
    build_demo_training_plan,
    create_demo_training_plan_examples,
    dataset_summary_from_manifest,
)
from ..training_plugins import (
    OptionalDependencySpec,
    optional_dependency_accelerate,
    optional_dependency_bitsandbytes,
    optional_dependency_datasets,
    optional_dependency_peft,
    optional_dependency_torch,
    optional_dependency_transformers,
)

EXPERIMENTAL_LORA_BACKEND_NAME = "experimental-lora-backend"
EXPERIMENTAL_LORA_CREATED_AT = "2026-01-01T00:00:00+00:00"
EXPERIMENTAL_LORA_CONFIRMATION_TOKEN = "I_UNDERSTAND_GRONA_EXPERIMENTAL_LORA_TRAINING_IS_NOT_IMPLEMENTED"
LORA_REQUIRED_DEPENDENCIES = ("torch", "transformers", "peft", "accelerate", "datasets")
LORA_OPTIONAL_DEPENDENCIES = ("bitsandbytes",)


@dataclass(frozen=True)
class LoRATrainingSafetyConfig:
    """Conservative safety gates for an experimental LoRA backend skeleton."""

    allow_training_execution: bool = False
    allow_model_download: bool = False
    allow_dataset_download: bool = False
    allow_overwrite_output: bool = False
    require_explicit_confirmation: bool = True
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        allow_training_execution: bool = False,
        allow_model_download: bool = False,
        allow_dataset_download: bool = False,
        allow_overwrite_output: bool = False,
        require_explicit_confirmation: bool = True,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "allow_training_execution", allow_training_execution)
        object.__setattr__(self, "allow_model_download", allow_model_download)
        object.__setattr__(self, "allow_dataset_download", allow_dataset_download)
        object.__setattr__(self, "allow_overwrite_output", allow_overwrite_output)
        object.__setattr__(self, "require_explicit_confirmation", require_explicit_confirmation)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible safety settings."""
        return {
            "allow_training_execution": self.allow_training_execution,
            "allow_model_download": self.allow_model_download,
            "allow_dataset_download": self.allow_dataset_download,
            "allow_overwrite_output": self.allow_overwrite_output,
            "require_explicit_confirmation": self.require_explicit_confirmation,
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return readable safety settings."""
        return "\n".join(
            (
                "LoRA training safety config",
                f"Allow training execution: {self.allow_training_execution}",
                f"Allow model download: {self.allow_model_download}",
                f"Allow dataset download: {self.allow_dataset_download}",
                f"Allow overwrite output: {self.allow_overwrite_output}",
                f"Require explicit confirmation: {self.require_explicit_confirmation}",
            )
        )


@dataclass(frozen=True)
class LoRATrainingJob:
    """Structured LoRA job description only; no model training is performed."""

    job_id: str
    created_at: str
    run_name: str
    base_model: dict[str, object]
    adapter_config: dict[str, object]
    dataset_paths: dict[str, str]
    output_dir: str
    training_args: dict[str, object]
    warnings: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        job_id: str,
        created_at: str,
        run_name: str,
        base_model: Mapping[str, object],
        adapter_config: Mapping[str, object],
        dataset_paths: Mapping[str, str],
        output_dir: str,
        training_args: Mapping[str, object],
        warnings: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not job_id:
            raise ValueError("LoRA training job_id cannot be empty")
        if not run_name:
            raise ValueError("LoRA training run_name cannot be empty")
        if not output_dir:
            raise ValueError("LoRA training output_dir cannot be empty")
        object.__setattr__(self, "job_id", job_id)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "run_name", run_name)
        object.__setattr__(self, "base_model", json_metadata(base_model))
        object.__setattr__(self, "adapter_config", json_metadata(adapter_config))
        object.__setattr__(self, "dataset_paths", dict(sorted(dataset_paths.items())))
        object.__setattr__(self, "output_dir", output_dir)
        object.__setattr__(self, "training_args", json_metadata(training_args))
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible job description."""
        return {
            "job_id": self.job_id,
            "created_at": self.created_at,
            "run_name": self.run_name,
            "base_model": self.base_model,
            "adapter_config": self.adapter_config,
            "dataset_paths": self.dataset_paths,
            "output_dir": self.output_dir,
            "training_args": self.training_args,
            "warnings": list(self.warnings),
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Return stable JSON for the job description."""
        return dumps(self.to_dict(), sort_keys=True)

    def to_text(self) -> str:
        """Return a readable job preview."""
        lines = [
            f"LoRA training job preview: {self.job_id}",
            f"Created at: {self.created_at}",
            f"Run name: {self.run_name}",
            f"Base model: {self.base_model.get('model_id', 'unknown')}",
            f"Adapter type: {self.adapter_config.get('adapter_type', 'unknown')}",
            f"Output dir: {self.output_dir}",
            "Dataset paths:",
        ]
        lines.extend(f"- {name}: {path}" for name, path in self.dataset_paths.items())
        lines.append("Warnings:")
        lines.extend(markdown_or_none(self.warnings))
        return "\n".join(lines)


@dataclass(frozen=True)
class LoRATrainingReadinessReport:
    """Readiness report for the experimental LoRA skeleton."""

    ready: bool
    dependency_report: TrainingBackendDependencyReport
    artifact_report: dict[str, object]
    config_report: dict[str, object]
    safety_report: dict[str, object]
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        ready: bool,
        dependency_report: TrainingBackendDependencyReport,
        artifact_report: Mapping[str, object],
        config_report: Mapping[str, object],
        safety_report: Mapping[str, object],
        warnings: Sequence[str] = (),
        blockers: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "ready", ready)
        object.__setattr__(self, "dependency_report", dependency_report)
        object.__setattr__(self, "artifact_report", json_metadata(artifact_report))
        object.__setattr__(self, "config_report", json_metadata(config_report))
        object.__setattr__(self, "safety_report", json_metadata(safety_report))
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "blockers", tuple(blockers))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible readiness details."""
        return {
            "ready": self.ready,
            "dependency_report": self.dependency_report.to_dict(),
            "artifact_report": self.artifact_report,
            "config_report": self.config_report,
            "safety_report": self.safety_report,
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return readable LoRA readiness details."""
        lines = [
            f"Experimental LoRA readiness: {'ready' if self.ready else 'blocked'}",
            "Dependency report:",
            self.dependency_report.to_text(),
            "Artifact report:",
            compact_dict_text(self.artifact_report),
            "Config report:",
            compact_dict_text(self.config_report),
            "Safety report:",
            compact_dict_text(self.safety_report),
            "Warnings:",
        ]
        lines.extend(markdown_or_none(self.warnings))
        lines.append("Blockers:")
        lines.extend(markdown_or_none(self.blockers))
        return "\n".join(lines)


DependencyFinder = Callable[[str], object | None]


class ExperimentalLoRABackend:
    """Experimental LoRA backend skeleton. It prepares jobs and refuses execution."""

    name = EXPERIMENTAL_LORA_BACKEND_NAME
    backend_type = "experimental_lora_backend_skeleton"
    capabilities = (
        TrainingBackendCapability.LORA,
        TrainingBackendCapability.COMMAND_PREVIEW,
        TrainingBackendCapability.CPU_POSSIBLE,
    )
    required_artifacts = DRY_RUN_REQUIRED_ARTIFACTS
    optional_dependencies = (
        optional_dependency_torch(),
        optional_dependency_transformers(),
        optional_dependency_peft(),
        optional_dependency_accelerate(),
        optional_dependency_datasets(),
        optional_dependency_bitsandbytes(),
    )

    def __init__(self, dependency_finder: DependencyFinder | None = None) -> None:
        self._dependency_finder = dependency_finder or find_spec

    @property
    def required_dependencies(self) -> tuple[str, ...]:
        """Return required package names for a future real LoRA implementation."""
        return LORA_REQUIRED_DEPENDENCIES

    @property
    def metadata(self) -> TrainingBackendMetadata:
        """Return metadata for the experimental backend skeleton."""
        return TrainingBackendMetadata(
            backend_name=self.name,
            package_name="grona-experimental-lora-placeholder",
            optional_extra="training",
            install_hint="pip install grona[training] for future local experiments; CI does not install this extra",
            supported_adapter_types=("lora",),
            supported_quantization_modes=("none",),
            supported_artifact_formats=("jsonl", "json", "markdown", "text"),
            limitations=(
                "experimental skeleton only",
                "no training loop",
                "no model loading",
                "no subprocess or shell execution",
                "no downloads or uploads",
                "no CI coverage for real ML stack",
            ),
            metadata={"experimental": True, "executes_commands": False, "trains_model": False},
        )

    def supports(self, config: TrainingRunConfig) -> bool:
        """Return whether the config is LoRA-shaped and unquantized."""
        return config.adapter.adapter_type == "lora" and config.adapter.quantization == "none"

    def check_dependencies(self) -> TrainingBackendDependencyReport:
        """Check optional dependency availability with find_spec, without importing packages."""
        return detect_lora_dependency_availability(self._dependency_finder)

    def check_readiness(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        config: DryRunTrainerConfig | None = None,
    ) -> TrainingReadinessReport:
        """Return compatibility readiness using the existing TrainingBackend protocol shape."""
        _ = config
        safety = LoRATrainingSafetyConfig()
        _job, readiness = self.prepare_training_job(training_plan, artifact_bundle, "outputs/experimental-lora", safety)
        return TrainingReadinessReport(
            ready=readiness.ready,
            warnings=readiness.warnings,
            blockers=readiness.blockers,
            artifact_count=int(readiness.artifact_report.get("artifact_count", 0)),
            required_artifacts_present=bool(readiness.artifact_report.get("required_artifacts_present", False)),
            training_config_valid=bool(readiness.config_report.get("training_config_valid", False)),
            train_examples_count=int(readiness.config_report.get("train_examples_count", 0)),
            metadata={"experimental_lora_readiness": readiness.to_dict()},
        )

    def build_execution_plan(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        config: DryRunTrainerConfig | None = None,
    ) -> TrainingReadinessReport:
        """Return readiness metadata only; this backend has no executable plan yet."""
        return self.check_readiness(training_plan, artifact_bundle, config)

    def prepare_training_job(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        output_dir: str,
        safety_config: LoRATrainingSafetyConfig | None = None,
    ) -> tuple[LoRATrainingJob, LoRATrainingReadinessReport]:
        """Build a guarded LoRA job preview and readiness report without training."""
        safety = safety_config or LoRATrainingSafetyConfig()
        dependency_report = self.check_dependencies()
        artifact_report = build_artifact_report(artifact_bundle, self.required_artifacts)
        config_report = build_config_report(training_plan, self.supports(training_plan.config))
        safety_report = build_safety_report(safety)
        warnings = list(training_plan.validation.warnings)
        warnings.append("experimental LoRA backend skeleton does not execute training")
        blockers: list[str] = []
        blockers.extend(dependency_report.blockers)
        blockers.extend(str(error) for error in config_report.get("errors", ()))
        blockers.extend(str(blocker) for blocker in artifact_report.get("blockers", ()))
        blockers.extend(str(blocker) for blocker in safety_report.get("blockers", ()))
        if not output_dir:
            blockers.append("output_dir must be explicit")
        blockers.append("real LoRA training loop is not implemented in this skeleton")

        job = LoRATrainingJob(
            job_id=f"lora-training-job:{training_plan.config.run_name}",
            created_at=EXPERIMENTAL_LORA_CREATED_AT,
            run_name=training_plan.config.run_name,
            base_model=training_plan.config.base_model.to_dict(),
            adapter_config=training_plan.config.adapter.to_dict(),
            dataset_paths=dataset_paths_for_output_dir(output_dir),
            output_dir=output_dir,
            training_args=training_args_from_config(training_plan.config),
            warnings=dedupe_strings(warnings),
            metadata={"experimental": True, "trains_model": False, "executes_commands": False},
        )
        readiness = LoRATrainingReadinessReport(
            ready=False,
            dependency_report=dependency_report,
            artifact_report=artifact_report,
            config_report=config_report,
            safety_report=safety_report,
            warnings=dedupe_strings(warnings),
            blockers=dedupe_strings(blockers),
            metadata={"backend_name": self.name, "job_id": job.job_id, "experimental": True},
        )
        return job, readiness

    def run_training(
        self,
        training_plan: TrainingPlan,
        artifact_bundle: TrainingArtifactBundle,
        output_dir: str,
        safety_config: LoRATrainingSafetyConfig | None = None,
        confirmation: str = "",
    ) -> dict[str, object]:
        """Refuse execution unless explicit gates are passed, then still report not implemented."""
        safety = safety_config or LoRATrainingSafetyConfig()
        job, readiness = self.prepare_training_job(training_plan, artifact_bundle, output_dir, safety)
        if not safety.allow_training_execution:
            raise RuntimeError("experimental LoRA training execution is disabled by safety config")
        if safety.require_explicit_confirmation and confirmation != EXPERIMENTAL_LORA_CONFIRMATION_TOKEN:
            raise RuntimeError("explicit experimental LoRA confirmation token is required")
        if not readiness.dependency_report.available:
            raise RuntimeError("experimental LoRA dependencies are not available")
        if not readiness.artifact_report.get("required_artifacts_present", False):
            raise RuntimeError("required training artifacts are missing")
        raise NotImplementedError(
            f"{self.name} is guarded and does not implement a real LoRA training loop yet for {job.job_id}"
        )

    def to_text(self) -> str:
        """Return readable backend summary."""
        return "\n".join(
            (
                f"Experimental training backend: {self.name}",
                f"Type: {self.backend_type}",
                f"Capabilities: {', '.join(self.capabilities)}",
                f"Required dependencies: {', '.join(self.required_dependencies)}",
                "Execution: guarded skeleton only; no training loop is implemented.",
            )
        )


def detect_lora_dependency_availability(
    dependency_finder: DependencyFinder | None = None,
) -> TrainingBackendDependencyReport:
    """Detect optional LoRA dependency availability with find_spec only."""
    finder = dependency_finder or find_spec
    checked = tuple(LORA_REQUIRED_DEPENDENCIES + LORA_OPTIONAL_DEPENDENCIES)
    present = tuple(package for package in checked if finder(package) is not None)
    missing_required = tuple(package for package in LORA_REQUIRED_DEPENDENCIES if package not in present)
    missing_optional = tuple(package for package in LORA_OPTIONAL_DEPENDENCIES if package not in present)
    blockers = tuple(f"missing optional LoRA dependency: {package}" for package in missing_required)
    warnings = ["dependency detection uses importlib.util.find_spec and does not import heavy packages"]
    if missing_optional:
        warnings.append(f"optional dependency not found: {', '.join(missing_optional)}")
    return TrainingBackendDependencyReport(
        EXPERIMENTAL_LORA_BACKEND_NAME,
        available=not missing_required,
        missing_dependencies=missing_required,
        optional_dependencies=checked,
        warnings=warnings,
        blockers=blockers,
        metadata={
            "detection_method": "importlib.util.find_spec",
            "imports_packages": False,
            "present_dependencies": list(present),
            "missing_optional_dependencies": list(missing_optional),
        },
    )


def build_artifact_report(
    artifact_bundle: TrainingArtifactBundle,
    required_artifacts: Sequence[str],
) -> dict[str, object]:
    """Return artifact readiness metadata for a LoRA job preview."""
    paths = artifact_bundle.artifact_paths()
    missing = tuple(path for path in required_artifacts if artifact_bundle.get_artifact(path) is None)
    blockers = tuple(f"missing required artifact: {path}" for path in missing)
    return {
        "artifact_count": len(paths),
        "artifact_paths": list(paths),
        "required_artifacts": list(required_artifacts),
        "missing_required_artifacts": list(missing),
        "required_artifacts_present": not missing,
        "blockers": list(blockers),
    }


def build_config_report(training_plan: TrainingPlan, supported: bool) -> dict[str, object]:
    """Return config readiness metadata for a LoRA job preview."""
    errors = list(training_plan.validation.errors)
    if not training_plan.validation.valid:
        errors.append("training plan validation did not pass")
    if not supported:
        errors.append("experimental LoRA backend supports only adapter_type='lora' with quantization='none'")
    train_examples = int(training_plan.config.dataset_manifest.split_counts.get("train", 0))
    return {
        "training_config_valid": training_plan.validation.valid,
        "backend_supports_config": supported,
        "adapter_type": training_plan.config.adapter.adapter_type,
        "quantization": training_plan.config.adapter.quantization,
        "train_examples_count": train_examples,
        "warnings": list(training_plan.validation.warnings),
        "errors": dedupe_strings(errors),
    }


def build_safety_report(safety_config: LoRATrainingSafetyConfig) -> dict[str, object]:
    """Return safety blockers for the conservative LoRA execution gate."""
    blockers: list[str] = []
    if not safety_config.allow_training_execution:
        blockers.append("training execution is disabled by default")
    if not safety_config.allow_model_download:
        blockers.append("model downloads are disabled")
    if not safety_config.allow_dataset_download:
        blockers.append("dataset downloads are disabled")
    if safety_config.require_explicit_confirmation:
        blockers.append("explicit confirmation token is required before any future execution")
    return {
        **safety_config.to_dict(),
        "blockers": blockers,
    }


def dataset_paths_for_output_dir(output_dir: str) -> dict[str, str]:
    """Return planned dataset artifact paths under an explicit output directory."""
    base = output_dir.rstrip("/\\") or "outputs/experimental-lora"
    return {
        "train": f"{base}/data/train.jsonl",
        "validation": f"{base}/data/validation.jsonl",
        "test": f"{base}/data/test.jsonl",
        "config": f"{base}/config/training_config.json",
    }


def training_args_from_config(config: TrainingRunConfig) -> dict[str, object]:
    """Return stable training argument metadata from a config-only plan."""
    return {
        "epochs": config.epochs,
        "learning_rate": config.learning_rate,
        "batch_size": config.batch_size,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "max_sequence_length": config.max_sequence_length,
        "seed": config.seed,
        "evaluation_plan": config.evaluation_plan,
    }


def build_demo_lora_training_inputs() -> tuple[TrainingDatasetPackage, TrainingPlan, TrainingArtifactBundle]:
    """Build deterministic LoRA-shaped demo inputs without writing files or training."""
    package = build_training_dataset_package(
        create_demo_training_plan_examples(),
        dataset_name="demo-experimental-lora-package",
        description="Reviewed examples for an experimental LoRA backend skeleton demo.",
        metadata={"demo": "experimental_lora_backend", "config_only": True},
    )
    base_plan = build_demo_training_plan(package)
    base_model = BaseModelSpec(
        name=base_plan.config.base_model.name,
        provider=base_plan.config.base_model.provider,
        model_id=base_plan.config.base_model.model_id,
        parameter_count=base_plan.config.base_model.parameter_count,
        context_length=base_plan.config.base_model.context_length,
        license=base_plan.config.base_model.license,
        intended_use="future experimental LoRA adapter skeleton planning",
        metadata={"loads_model": False, "downloads_model": False},
    )
    adapter = AdapterTrainingSpec(
        adapter_type="lora",
        rank=8,
        alpha=16,
        dropout=0.05,
        target_modules=("q_proj", "v_proj"),
        quantization="none",
        metadata={"experimental_lora_backend": True, "training_loop": "not_implemented"},
    )
    config = TrainingRunConfig(
        run_name="demo-experimental-lora-backend-skeleton",
        base_model=base_model,
        adapter=adapter,
        dataset_manifest=package.manifest,
        dataset_package_summary=dataset_summary_from_manifest(package.manifest),
        epochs=1,
        learning_rate=0.0002,
        batch_size=1,
        gradient_accumulation_steps=4,
        max_sequence_length=2048,
        seed=42,
        evaluation_plan="future deterministic holdout review; no real evaluation yet",
        safety_notes=(
            "Experimental LoRA backend skeleton does not execute training.",
            "Reviewed examples remain candidates, not guaranteed high-quality training data.",
        ),
        output_policy="no artifacts are written and no training runs by default",
        metadata={"experimental_lora_backend": True, "trains_model": False},
    )
    validation = TrainingRunValidator().validate(config)
    model_card = ModelCardDraft(
        model_name=f"{base_model.name} + experimental LoRA skeleton",
        base_model=base_model,
        adapter_type=adapter.adapter_type,
        dataset_summary=dataset_summary_from_manifest(package.manifest),
        intended_use="Configuration review for a future guarded LoRA backend.",
        limitations=(
            "No model has been trained.",
            "ExperimentalLoRABackend has no training loop.",
            "No real evaluation has been run.",
        ),
        safety_notes=config.safety_notes,
        evaluation_plan=config.evaluation_plan,
        metadata={"demo": "experimental_lora_backend"},
    )
    plan = TrainingPlan(
        config=config,
        validation=validation,
        dataset_card=DatasetCardDraft.from_package(package),
        model_card_draft=model_card,
        created_at=EXPERIMENTAL_LORA_CREATED_AT,
        metadata={"demo": "experimental_lora_backend", "config_only": True},
    )
    bundle = TrainingArtifactBuilder().build(package, plan, name="demo-experimental-lora-artifact-bundle")
    return package, plan, bundle


def compact_dict_text(data: Mapping[str, object]) -> str:
    """Return compact key/value lines for debug output."""
    if not data:
        return "- none"
    return "\n".join(f"- {key}: {value}" for key, value in data.items())


def markdown_or_none(values: Sequence[str]) -> list[str]:
    """Return Markdown list lines with a none fallback."""
    if not values:
        return ["- none"]
    return [f"- {value}" for value in values]
