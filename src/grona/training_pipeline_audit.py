"""Training pipeline contract hardening and readiness audit layer."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps

from .experimental_training import LoRATrainingSafetyConfig
from .feedback import Metadata
from .training import TrainingExample, json_metadata
from .training_artifacts import TrainingArtifactBundle, TrainingArtifactBuilder
from .training_backends import TrainingBackend, TrainingBackendDependencyReport
from .training_dry_run import DRY_RUN_REQUIRED_ARTIFACTS, dedupe_strings
from .training_package import TrainingDatasetPackage, build_training_dataset_package
from .training_plan import TrainingPlan, build_demo_training_plan, create_demo_training_plan_examples

TRAINING_PIPELINE_STAGE_NAMES = (
    "reviewed_trace_examples",
    "training_dataset_package",
    "training_artifacts",
    "training_plan",
    "dry_run_trainer",
    "backend",
    "safety",
    "provenance",
    "license",
    "validation",
    "execution",
)
TRAINING_PIPELINE_STAGE_STATUSES = ("passed", "warning", "blocked", "not_checked")
TRAINING_PIPELINE_REQUIRED_ARTIFACTS = (
    "data/train.jsonl",
    "config/training_config.json",
    "manifests/training_export_manifest.json",
    "docs/dataset_card.md",
    "docs/model_card.md",
)


@dataclass(frozen=True)
class TrainingPipelineStageStatus:
    """One deterministic stage status in the training-preparation audit."""

    stage: str
    status: str
    reasons: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        stage: str,
        status: str,
        reasons: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if stage not in TRAINING_PIPELINE_STAGE_NAMES:
            raise ValueError(f"unknown training pipeline audit stage: {stage}")
        if status not in TRAINING_PIPELINE_STAGE_STATUSES:
            raise ValueError(f"unknown training pipeline audit status: {status}")
        object.__setattr__(self, "stage", stage)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "reasons", tuple(reasons))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible stage status."""
        return {
            "stage": self.stage,
            "status": self.status,
            "reasons": list(self.reasons),
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return readable stage status."""
        lines = [f"{self.stage}: {self.status}"]
        lines.extend(f"- {reason}" for reason in self.reasons)
        return "\n".join(lines)


@dataclass(frozen=True)
class TrainingPipelineReadinessReport:
    """Readiness report for the full deterministic training-preparation pipeline."""

    ready: bool
    stage_statuses: tuple[TrainingPipelineStageStatus, ...]
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)
    summary: dict[str, object] = field(default_factory=dict)

    def __init__(
        self,
        ready: bool,
        stage_statuses: Sequence[TrainingPipelineStageStatus],
        warnings: Sequence[str] = (),
        blockers: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
        summary: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "ready", ready)
        object.__setattr__(self, "stage_statuses", tuple(stage_statuses))
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "blockers", tuple(blockers))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))
        object.__setattr__(self, "summary", json_metadata(summary or build_summary(stage_statuses)))

    def stage(self, name: str) -> TrainingPipelineStageStatus | None:
        """Return one stage status by name."""
        for status in self.stage_statuses:
            if status.stage == name:
                return status
        return None

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible readiness report."""
        return {
            "ready": self.ready,
            "stage_statuses": [stage.to_dict() for stage in self.stage_statuses],
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
            "metadata": self.metadata,
            "summary": self.summary,
        }

    def to_json(self) -> str:
        """Return stable JSON for the readiness report."""
        return dumps(self.to_dict(), sort_keys=True)

    def to_text(self) -> str:
        """Return readable training pipeline readiness details."""
        lines = [
            f"Training pipeline readiness: {'ready' if self.ready else 'blocked'}",
            "Stage statuses:",
        ]
        lines.extend(f"- {stage.stage}: {stage.status}" for stage in self.stage_statuses)
        lines.append("Warnings:")
        lines.extend(markdown_or_none(self.warnings))
        lines.append("Blockers:")
        lines.extend(markdown_or_none(self.blockers))
        lines.append("Summary:")
        lines.extend(f"- {key}: {value}" for key, value in self.summary.items())
        return "\n".join(lines)


@dataclass(frozen=True)
class TrainingPipelineContract:
    """Explicit contract for future training backend readiness."""

    required_inputs: tuple[str, ...]
    required_artifact_paths: tuple[str, ...]
    required_metadata_fields: tuple[str, ...]
    required_backend_behavior: tuple[str, ...]
    forbidden_default_behavior: tuple[str, ...]
    future_real_training_requirements: tuple[str, ...]
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        required_inputs: Sequence[str] = (
            "reviewed training examples",
            "TrainingDatasetPackage",
            "TrainingPlan",
            "TrainingArtifactBundle",
            "TrainingBackend",
            "explicit safety config",
        ),
        required_artifact_paths: Sequence[str] = TRAINING_PIPELINE_REQUIRED_ARTIFACTS,
        required_metadata_fields: Sequence[str] = (
            "provenance",
            "license",
            "validation_status",
            "dataset_manifest",
            "split_counts",
        ),
        required_backend_behavior: Sequence[str] = (
            "declare name and backend_type",
            "declare capabilities and required artifacts",
            "support or reject adapter config explicitly",
            "return dependency report without heavy imports",
            "return readiness report without execution",
        ),
        forbidden_default_behavior: Sequence[str] = (
            "model training",
            "model loading",
            "subprocess execution",
            "shell execution",
            "network calls",
            "downloads or uploads",
            "file writes by default",
            "heavy ML imports at module import time",
        ),
        future_real_training_requirements: Sequence[str] = (
            "explicit execution contract",
            "dependency isolation",
            "artifact output policy",
            "model and dataset license review",
            "evaluation and rollback policy",
            "hardware assumptions and safety review",
        ),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "required_inputs", tuple(required_inputs))
        object.__setattr__(self, "required_artifact_paths", tuple(required_artifact_paths))
        object.__setattr__(self, "required_metadata_fields", tuple(required_metadata_fields))
        object.__setattr__(self, "required_backend_behavior", tuple(required_backend_behavior))
        object.__setattr__(self, "forbidden_default_behavior", tuple(forbidden_default_behavior))
        object.__setattr__(self, "future_real_training_requirements", tuple(future_real_training_requirements))
        object.__setattr__(self, "metadata", json_metadata(metadata or {"contract_version": 1}))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible contract description."""
        return {
            "required_inputs": list(self.required_inputs),
            "required_artifact_paths": list(self.required_artifact_paths),
            "required_metadata_fields": list(self.required_metadata_fields),
            "required_backend_behavior": list(self.required_backend_behavior),
            "forbidden_default_behavior": list(self.forbidden_default_behavior),
            "future_real_training_requirements": list(self.future_real_training_requirements),
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Return stable JSON for the contract."""
        return dumps(self.to_dict(), sort_keys=True)

    def to_text(self) -> str:
        """Return readable contract summary."""
        lines = ["Training pipeline contract", "Required inputs:"]
        lines.extend(markdown_or_none(self.required_inputs))
        lines.append("Required artifacts:")
        lines.extend(markdown_or_none(self.required_artifact_paths))
        lines.append("Required backend behavior:")
        lines.extend(markdown_or_none(self.required_backend_behavior))
        lines.append("Forbidden default behavior:")
        lines.extend(markdown_or_none(self.forbidden_default_behavior))
        lines.append("Future real-training requirements:")
        lines.extend(markdown_or_none(self.future_real_training_requirements))
        return "\n".join(lines)


class TrainingPipelineAuditor:
    """Audit the deterministic training-preparation pipeline without training anything."""

    def __init__(self, contract: TrainingPipelineContract | None = None) -> None:
        self.contract = contract or TrainingPipelineContract()

    def audit(
        self,
        examples: Sequence[TrainingExample] = (),
        package: TrainingDatasetPackage | None = None,
        artifact_bundle: TrainingArtifactBundle | None = None,
        training_plan: TrainingPlan | None = None,
        backend: TrainingBackend | None = None,
        safety_config: LoRATrainingSafetyConfig | None = None,
    ) -> TrainingPipelineReadinessReport:
        """Return a full training-preparation readiness report without execution."""
        stage_statuses = (
            audit_examples_stage(examples),
            audit_package_stage(package),
            audit_artifact_stage(artifact_bundle, self.contract.required_artifact_paths),
            audit_plan_stage(training_plan, package),
            audit_dry_run_stage(training_plan, artifact_bundle),
            audit_backend_stage(backend, training_plan, artifact_bundle),
            audit_safety_stage(safety_config),
            audit_provenance_stage(examples, package),
            audit_license_stage(package, training_plan),
            audit_validation_stage(examples, package, training_plan),
            audit_execution_stage(safety_config),
        )
        warnings = collect_reasons(stage_statuses, "warning")
        blockers = collect_reasons(stage_statuses, "blocked")
        return TrainingPipelineReadinessReport(
            ready=not blockers,
            stage_statuses=stage_statuses,
            warnings=warnings,
            blockers=blockers,
            metadata={
                "auditor": "TrainingPipelineAuditor",
                "executes_training": False,
                "contract": self.contract.to_dict(),
            },
        )


def validate_training_backend_contract(
    backend: TrainingBackend | None,
    training_plan: TrainingPlan | None,
    artifact_bundle: TrainingArtifactBundle | None,
) -> TrainingPipelineStageStatus:
    """Validate one backend contract surface without raising for ordinary blockers."""
    reasons: list[str] = []
    metadata: dict[str, object] = {"executes_training": False}
    if backend is None:
        return TrainingPipelineStageStatus("backend", "not_checked", ("backend is not provided",), metadata)
    name = getattr(backend, "name", "")
    backend_type = getattr(backend, "backend_type", "")
    capabilities = tuple(getattr(backend, "capabilities", ()))
    required_artifacts = tuple(getattr(backend, "required_artifacts", ()))
    metadata.update(
        {
            "backend_name": name,
            "backend_type": backend_type,
            "capabilities": list(capabilities),
            "required_artifacts": list(required_artifacts),
        }
    )
    if not name:
        reasons.append("backend name is missing")
    if not backend_type:
        reasons.append("backend_type is missing")
    if not capabilities:
        reasons.append("backend capabilities are missing")
    if not required_artifacts:
        reasons.append("backend required artifacts are missing")
    dependency_report = backend.check_dependencies()
    metadata["dependency_report"] = dependency_report.to_dict()
    if not isinstance(dependency_report, TrainingBackendDependencyReport):
        reasons.append("backend dependency report has unexpected type")
    if training_plan is not None:
        supported = backend.supports(training_plan.config)
        metadata["supports_training_plan"] = supported
        if not supported:
            reasons.append("backend explicitly rejects the training plan adapter config")
    if artifact_bundle is not None:
        missing = tuple(path for path in required_artifacts if artifact_bundle.get_artifact(path) is None)
        metadata["missing_backend_artifacts"] = list(missing)
        reasons.extend(f"backend required artifact missing: {path}" for path in missing)
    if training_plan is not None and artifact_bundle is not None:
        readiness = backend.check_readiness(training_plan, artifact_bundle)
        metadata["readiness"] = readiness.to_dict()
        if getattr(readiness, "ready", False):
            reasons.append("backend readiness claims ready without explicit execution safety confirmation")
    status = "blocked" if reasons else "passed"
    return TrainingPipelineStageStatus("backend", status, dedupe_strings(reasons), metadata)


def training_lifecycle_markdown() -> str:
    """Return deterministic Markdown summary of the training-preparation lifecycle."""
    return "\n".join(
        (
            "# Training Preparation Lifecycle",
            "",
            "```text",
            "reviewed traces -> examples -> dataset package -> artifact bundle -> training plan -> dry-run -> backend readiness -> future real training",
            "```",
            "",
            "Current status: future real training remains blocked by default. The lifecycle is inspectable, deterministic, offline, and does not execute training commands.",
        )
    )


def audit_examples_stage(examples: Sequence[TrainingExample]) -> TrainingPipelineStageStatus:
    """Audit reviewed trace training examples."""
    if not examples:
        return TrainingPipelineStageStatus("reviewed_trace_examples", "not_checked", ("training examples were not provided",))
    reasons: list[str] = []
    warnings: list[str] = []
    for index, example in enumerate(examples):
        if not example.provenance:
            reasons.append(f"example {index} is missing provenance")
        if not example.license or example.license == "unknown":
            reasons.append(f"example {index} is missing license")
        if example.validation_status in {"raw", "rejected", "unreviewed"}:
            reasons.append(f"example {index} is not training-ready: {example.validation_status}")
    if len(examples) < 10:
        warnings.append("training example set is tiny")
    status = "blocked" if reasons else "warning" if warnings else "passed"
    return TrainingPipelineStageStatus(
        "reviewed_trace_examples",
        status,
        dedupe_strings(reasons + warnings),
        {"example_count": len(examples)},
    )


def audit_package_stage(package: TrainingDatasetPackage | None) -> TrainingPipelineStageStatus:
    """Audit dataset package compatibility."""
    if package is None:
        return TrainingPipelineStageStatus("training_dataset_package", "not_checked", ("training dataset package is not provided",))
    reasons: list[str] = []
    warnings: list[str] = []
    train_count = int(package.manifest.split_counts.get("train", 0))
    validation_count = int(package.manifest.split_counts.get("validation", 0))
    test_count = int(package.manifest.split_counts.get("test", 0))
    if train_count <= 0:
        reasons.append("training dataset package has no train examples")
    if package.manifest.total_examples <= 0:
        reasons.append("training export manifest has no examples")
    if validation_count <= 0:
        warnings.append("validation split is empty")
    if test_count <= 0:
        warnings.append("test split is empty")
    status = "blocked" if reasons else "warning" if warnings else "passed"
    return TrainingPipelineStageStatus(
        "training_dataset_package",
        status,
        dedupe_strings(reasons + warnings),
        {
            "dataset_name": package.dataset.name,
            "total_examples": package.manifest.total_examples,
            "split_counts": package.manifest.split_counts,
        },
    )


def audit_artifact_stage(
    artifact_bundle: TrainingArtifactBundle | None,
    required_paths: Sequence[str],
) -> TrainingPipelineStageStatus:
    """Audit artifact bundle required paths."""
    if artifact_bundle is None:
        return TrainingPipelineStageStatus("training_artifacts", "not_checked", ("training artifact bundle is not provided",))
    missing = tuple(path for path in required_paths if artifact_bundle.get_artifact(path) is None)
    reasons = tuple(f"required artifact is missing: {path}" for path in missing)
    return TrainingPipelineStageStatus(
        "training_artifacts",
        "blocked" if reasons else "passed",
        reasons,
        {"artifact_count": len(artifact_bundle.artifacts), "artifact_paths": list(artifact_bundle.artifact_paths())},
    )


def audit_plan_stage(
    training_plan: TrainingPlan | None,
    package: TrainingDatasetPackage | None,
) -> TrainingPipelineStageStatus:
    """Audit training plan and package compatibility."""
    if training_plan is None:
        return TrainingPipelineStageStatus("training_plan", "not_checked", ("training plan is not provided",))
    reasons: list[str] = []
    warnings: list[str] = list(training_plan.validation.warnings)
    if not training_plan.validation.valid:
        reasons.append("training plan validation is not valid")
    if package is not None:
        if training_plan.config.dataset_manifest.dataset_name != package.manifest.dataset_name:
            reasons.append("training plan dataset name does not match package manifest")
        if training_plan.config.dataset_manifest.split_counts != package.manifest.split_counts:
            reasons.append("training plan split counts do not match package manifest")
    if training_plan.model_card_draft is None:
        reasons.append("model card draft is missing")
    status = "blocked" if reasons else "warning" if warnings else "passed"
    return TrainingPipelineStageStatus(
        "training_plan",
        status,
        dedupe_strings(reasons + warnings),
        {
            "run_name": training_plan.config.run_name,
            "adapter_type": training_plan.config.adapter.adapter_type,
            "validation_valid": training_plan.validation.valid,
        },
    )


def audit_dry_run_stage(
    training_plan: TrainingPlan | None,
    artifact_bundle: TrainingArtifactBundle | None,
) -> TrainingPipelineStageStatus:
    """Audit dry-run trainer compatibility inputs."""
    if training_plan is None or artifact_bundle is None:
        return TrainingPipelineStageStatus("dry_run_trainer", "not_checked", ("training plan or artifact bundle is not provided",))
    missing = tuple(path for path in DRY_RUN_REQUIRED_ARTIFACTS if artifact_bundle.get_artifact(path) is None)
    reasons = tuple(f"dry-run required artifact is missing: {path}" for path in missing)
    return TrainingPipelineStageStatus(
        "dry_run_trainer",
        "blocked" if reasons else "passed",
        reasons,
        {"required_artifacts": list(DRY_RUN_REQUIRED_ARTIFACTS), "missing": list(missing)},
    )


def audit_backend_stage(
    backend: TrainingBackend | None,
    training_plan: TrainingPlan | None,
    artifact_bundle: TrainingArtifactBundle | None,
) -> TrainingPipelineStageStatus:
    """Audit backend contract behavior."""
    return validate_training_backend_contract(backend, training_plan, artifact_bundle)


def audit_safety_stage(safety_config: LoRATrainingSafetyConfig | None) -> TrainingPipelineStageStatus:
    """Audit safety flags for default execution blocking."""
    if safety_config is None:
        return TrainingPipelineStageStatus("safety", "not_checked", ("safety config is not provided",))
    reasons: list[str] = []
    warnings: list[str] = []
    if safety_config.allow_training_execution:
        reasons.append("training execution is allowed; audit expects execution blocked by default")
    if safety_config.allow_model_download:
        reasons.append("model downloads are allowed")
    if safety_config.allow_dataset_download:
        reasons.append("dataset downloads are allowed")
    if not safety_config.require_explicit_confirmation:
        warnings.append("explicit confirmation is not required")
    status = "blocked" if reasons else "warning" if warnings else "passed"
    return TrainingPipelineStageStatus("safety", status, dedupe_strings(reasons + warnings), safety_config.to_dict())


def audit_provenance_stage(
    examples: Sequence[TrainingExample],
    package: TrainingDatasetPackage | None,
) -> TrainingPipelineStageStatus:
    """Audit provenance preservation."""
    reasons: list[str] = []
    if examples and any(not example.provenance for example in examples):
        reasons.append("one or more examples are missing provenance")
    if package is not None:
        for split in package.splits:
            for example in split.examples:
                if not example.provenance:
                    reasons.append(f"package split {split.name} contains example without provenance")
    if not examples and package is None:
        return TrainingPipelineStageStatus("provenance", "not_checked", ("no examples or package provided",))
    return TrainingPipelineStageStatus("provenance", "blocked" if reasons else "passed", dedupe_strings(reasons))


def audit_license_stage(
    package: TrainingDatasetPackage | None,
    training_plan: TrainingPlan | None,
) -> TrainingPipelineStageStatus:
    """Audit license metadata preservation."""
    if package is None and training_plan is None:
        return TrainingPipelineStageStatus("license", "not_checked", ("package and training plan are not provided",))
    reasons: list[str] = []
    if package is not None and not package.manifest.license_summary:
        reasons.append("training export manifest license summary is missing")
    if training_plan is not None:
        if not training_plan.config.base_model.license or training_plan.config.base_model.license == "unknown":
            reasons.append("base model license is missing")
        if not training_plan.config.dataset_manifest.license_summary:
            reasons.append("training config dataset license summary is missing")
    return TrainingPipelineStageStatus("license", "blocked" if reasons else "passed", dedupe_strings(reasons))


def audit_validation_stage(
    examples: Sequence[TrainingExample],
    package: TrainingDatasetPackage | None,
    training_plan: TrainingPlan | None,
) -> TrainingPipelineStageStatus:
    """Audit validation/review readiness."""
    if not examples and package is None and training_plan is None:
        return TrainingPipelineStageStatus("validation", "not_checked", ("no validation inputs were provided",))
    reasons: list[str] = []
    bad_statuses = {"raw", "rejected", "unreviewed"}
    for example in examples:
        if example.validation_status in bad_statuses:
            reasons.append(f"example validation status is not training-ready: {example.validation_status}")
    if package is not None:
        for split in package.splits:
            for example in split.examples:
                if example.validation_status in bad_statuses:
                    reasons.append(f"package split {split.name} has non-ready example: {example.validation_status}")
    if training_plan is not None and not training_plan.validation.valid:
        reasons.append("training plan validation is invalid")
    return TrainingPipelineStageStatus("validation", "blocked" if reasons else "passed", dedupe_strings(reasons))


def audit_execution_stage(safety_config: LoRATrainingSafetyConfig | None) -> TrainingPipelineStageStatus:
    """Audit execution remains blocked before real training exists."""
    if safety_config is None:
        return TrainingPipelineStageStatus("execution", "not_checked", ("safety config is not provided",))
    reasons: list[str] = []
    if safety_config.allow_training_execution:
        reasons.append("training execution is enabled")
    if safety_config.allow_model_download:
        reasons.append("model download is enabled")
    if safety_config.allow_dataset_download:
        reasons.append("dataset download is enabled")
    status = "blocked" if reasons else "passed"
    ok_reason = ("training execution remains blocked by default",) if status == "passed" else ()
    return TrainingPipelineStageStatus("execution", status, dedupe_strings(reasons) or ok_reason)


def build_demo_training_pipeline_audit_inputs() -> tuple[
    tuple[TrainingExample, ...],
    TrainingDatasetPackage,
    TrainingPlan,
    TrainingArtifactBundle,
]:
    """Build deterministic demo audit inputs without writing files or training."""
    examples = create_demo_training_plan_examples()
    package = build_training_dataset_package(
        examples,
        dataset_name="demo-training-pipeline-audit-package",
        description="Reviewed examples for a deterministic training pipeline audit demo.",
        metadata={"demo": "training_pipeline_audit", "trains_model": False},
    )
    plan = build_demo_training_plan(package)
    bundle = TrainingArtifactBuilder().build(package, plan, name="demo-training-pipeline-audit-bundle")
    return examples, package, plan, bundle


def build_summary(stage_statuses: Sequence[TrainingPipelineStageStatus]) -> dict[str, object]:
    """Return compact status counts and readiness hints."""
    counts = {status: 0 for status in TRAINING_PIPELINE_STAGE_STATUSES}
    for stage in stage_statuses:
        counts[stage.status] += 1
    return {
        "stage_count": len(tuple(stage_statuses)),
        "passed": counts["passed"],
        "warning": counts["warning"],
        "blocked": counts["blocked"],
        "not_checked": counts["not_checked"],
        "real_training_ready": False,
    }


def collect_reasons(stage_statuses: Sequence[TrainingPipelineStageStatus], status: str) -> tuple[str, ...]:
    """Collect reasons for a status across all stages."""
    return dedupe_strings(
        f"{stage.stage}: {reason}"
        for stage in stage_statuses
        if stage.status == status
        for reason in stage.reasons
    )


def markdown_or_none(values: Sequence[str]) -> list[str]:
    """Return Markdown list lines with a none fallback."""
    if not values:
        return ["- none"]
    return [f"- {value}" for value in values]
