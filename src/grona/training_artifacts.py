"""Training artifact bundle and conservative export writer foundation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps
from pathlib import Path, PurePosixPath

from .feedback import Metadata
from .training import json_metadata
from .training_package import TRAINING_SPLIT_NAMES, TrainingDatasetPackage, build_training_dataset_package
from .training_plan import TrainingPlan, build_demo_training_plan, create_demo_training_plan_examples

DEFAULT_ARTIFACT_BUNDLE_CREATED_AT = "2026-01-01T00:00:00+00:00"
DEFAULT_ARTIFACT_BUNDLE_NAME = "training-artifact-bundle"
TRAINING_ARTIFACT_PATHS = (
    "data/train.jsonl",
    "data/validation.jsonl",
    "data/test.jsonl",
    "config/training_config.json",
    "manifests/dataset_manifest.json",
    "manifests/training_export_manifest.json",
    "docs/dataset_card.md",
    "docs/model_card.md",
    "docs/safety_notes.md",
    "README.md",
)


@dataclass(frozen=True)
class TrainingArtifact:
    """One deterministic text artifact prepared in memory, without writing files."""

    path: str
    content: str
    content_type: str = "text/plain"
    description: str = ""
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        path: str,
        content: str,
        content_type: str = "text/plain",
        description: str = "",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "path", normalize_artifact_path(path))
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "content_type", content_type or "text/plain")
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def byte_count(self) -> int:
        """Return the UTF-8 byte count of the artifact content."""
        return len(self.content.encode("utf-8"))

    def line_count(self) -> int:
        """Return a simple text line count, treating empty content as zero lines."""
        if not self.content:
            return 0
        return len(self.content.splitlines())

    def to_dict(self, include_content: bool = True) -> dict[str, object]:
        """Return deterministic JSON-compatible artifact metadata."""
        data: dict[str, object] = {
            "path": self.path,
            "content_type": self.content_type,
            "description": self.description,
            "byte_count": self.byte_count(),
            "line_count": self.line_count(),
            "metadata": self.metadata,
        }
        if include_content:
            data["content"] = self.content
        return data


@dataclass(frozen=True)
class TrainingArtifactBundle:
    """Deterministically ordered in-memory collection of training export artifacts."""

    name: str
    artifacts: tuple[TrainingArtifact, ...]
    created_at: str = DEFAULT_ARTIFACT_BUNDLE_CREATED_AT
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        artifacts: Sequence[TrainingArtifact],
        created_at: str = DEFAULT_ARTIFACT_BUNDLE_CREATED_AT,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not name:
            raise ValueError("artifact bundle name cannot be empty")
        ordered = tuple(sorted(artifacts, key=lambda artifact: artifact.path))
        paths = [artifact.path for artifact in ordered]
        if len(paths) != len(set(paths)):
            raise ValueError("artifact bundle paths must be unique")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "artifacts", ordered)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def artifact_paths(self) -> tuple[str, ...]:
        """Return artifact paths in deterministic bundle order."""
        return tuple(artifact.path for artifact in self.artifacts)

    def get_artifact(self, path: str) -> TrainingArtifact | None:
        """Return one artifact by normalized path, or None when absent."""
        normalized = normalize_artifact_path(path)
        for artifact in self.artifacts:
            if artifact.path == normalized:
                return artifact
        return None

    def total_byte_count(self) -> int:
        """Return total UTF-8 bytes across all artifacts."""
        return sum(artifact.byte_count() for artifact in self.artifacts)

    def summary(self) -> dict[str, object]:
        """Return a compact deterministic bundle summary."""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "artifact_count": len(self.artifacts),
            "total_byte_count": self.total_byte_count(),
            "paths": list(self.artifact_paths()),
            "metadata": self.metadata,
        }

    def to_dict(self, include_content: bool = False) -> dict[str, object]:
        """Return deterministic JSON-compatible bundle metadata."""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "artifacts": [artifact.to_dict(include_content=include_content) for artifact in self.artifacts],
            "summary": self.summary(),
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return a readable artifact bundle summary."""
        lines = [
            f"Training artifact bundle: {self.name}",
            f"Created at: {self.created_at}",
            f"Artifacts: {len(self.artifacts)}",
            f"Total bytes: {self.total_byte_count()}",
        ]
        lines.extend(f"- {artifact.path} ({artifact.byte_count()} bytes)" for artifact in self.artifacts)
        return "\n".join(lines)


class TrainingArtifactBuilder:
    """Build deterministic in-memory artifacts from a dataset package and plan."""

    def build(
        self,
        package: TrainingDatasetPackage,
        plan: TrainingPlan,
        name: str = DEFAULT_ARTIFACT_BUNDLE_NAME,
        created_at: str = DEFAULT_ARTIFACT_BUNDLE_CREATED_AT,
        metadata: Mapping[str, object] | None = None,
    ) -> TrainingArtifactBundle:
        """Return a complete artifact bundle without writing files or training models."""
        split_jsonl = {split_name: "" for split_name in TRAINING_SPLIT_NAMES}
        split_jsonl.update(package.native_jsonl_by_split(include_metadata=True))
        artifacts = [
            TrainingArtifact(
                f"data/{split_name}.jsonl",
                split_jsonl[split_name],
                "application/jsonl",
                f"Grona-native JSONL for the {split_name} split.",
                {"split": split_name, "empty": split_jsonl[split_name] == ""},
            )
            for split_name in TRAINING_SPLIT_NAMES
        ]
        artifacts.extend(
            (
                TrainingArtifact(
                    "config/training_config.json",
                    plan.config.to_json(),
                    "application/json",
                    "Config-only training run description. No training is performed.",
                    {"config_only": True, "trains_model": False},
                ),
                TrainingArtifact(
                    "manifests/dataset_manifest.json",
                    dataset_manifest_json(package),
                    "application/json",
                    "Dataset package manifest with split summaries and dataset metadata.",
                    {"source": "TrainingDatasetPackage"},
                ),
                TrainingArtifact(
                    "manifests/training_export_manifest.json",
                    package.manifest.to_json(),
                    "application/json",
                    "Training export manifest for the in-memory package.",
                    {"source": "TrainingExportManifest"},
                ),
                TrainingArtifact(
                    "docs/dataset_card.md",
                    plan.dataset_card.to_markdown(),
                    "text/markdown",
                    "Dataset card draft for review.",
                ),
                TrainingArtifact(
                    "docs/model_card.md",
                    model_card_markdown(plan),
                    "text/markdown",
                    "Model card draft for a future adapter experiment. No model exists yet.",
                    {"training_status": "not_trained_config_only"},
                ),
                TrainingArtifact(
                    "docs/safety_notes.md",
                    safety_notes_markdown(plan),
                    "text/markdown",
                    "Safety and validation notes for the artifact bundle.",
                ),
                TrainingArtifact(
                    "README.md",
                    bundle_readme_markdown(package, plan, name),
                    "text/markdown",
                    "Human-readable bundle overview and artifact index.",
                    {"config_only": True, "writes_files_by_default": False},
                ),
            )
        )
        return TrainingArtifactBundle(
            name=name,
            artifacts=artifacts,
            created_at=created_at,
            metadata={"builder": "TrainingArtifactBuilder", **json_metadata(metadata or {})},
        )


@dataclass(frozen=True)
class TrainingArtifactWriteConfig:
    """Conservative write settings for artifact bundle export."""

    overwrite: bool = False
    create_parents: bool = False
    dry_run: bool = True
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        overwrite: bool = False,
        create_parents: bool = False,
        dry_run: bool = True,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "overwrite", overwrite)
        object.__setattr__(self, "create_parents", create_parents)
        object.__setattr__(self, "dry_run", dry_run)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))


@dataclass(frozen=True)
class TrainingArtifactWriteReport:
    """Result of a dry-run or explicit artifact bundle write."""

    output_dir: str
    dry_run: bool
    planned_paths: tuple[str, ...] = ()
    written_paths: tuple[str, ...] = ()
    skipped_paths: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    summary: dict[str, int] = field(default_factory=dict)
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        output_dir: str,
        dry_run: bool,
        planned_paths: Sequence[str] = (),
        written_paths: Sequence[str] = (),
        skipped_paths: Sequence[str] = (),
        errors: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        summary = {
            "planned": len(tuple(planned_paths)),
            "written": len(tuple(written_paths)),
            "skipped": len(tuple(skipped_paths)),
            "errors": len(tuple(errors)),
        }
        object.__setattr__(self, "output_dir", output_dir)
        object.__setattr__(self, "dry_run", dry_run)
        object.__setattr__(self, "planned_paths", tuple(planned_paths))
        object.__setattr__(self, "written_paths", tuple(written_paths))
        object.__setattr__(self, "skipped_paths", tuple(skipped_paths))
        object.__setattr__(self, "errors", tuple(errors))
        object.__setattr__(self, "summary", summary)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible write report."""
        return {
            "output_dir": self.output_dir,
            "dry_run": self.dry_run,
            "planned_paths": list(self.planned_paths),
            "written_paths": list(self.written_paths),
            "skipped_paths": list(self.skipped_paths),
            "errors": list(self.errors),
            "summary": self.summary,
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return a compact human-readable write report."""
        status = "dry-run" if self.dry_run else "write"
        lines = [
            f"Training artifact writer report: {status}",
            f"Output dir: {self.output_dir}",
            f"Planned: {self.summary['planned']}",
            f"Written: {self.summary['written']}",
            f"Skipped: {self.summary['skipped']}",
            f"Errors: {self.summary['errors']}",
        ]
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


class TrainingArtifactWriter:
    """Write artifact bundles only when callers explicitly opt out of dry-run mode."""

    def write(
        self,
        bundle: TrainingArtifactBundle,
        output_dir: str | Path,
        config: TrainingArtifactWriteConfig | None = None,
    ) -> TrainingArtifactWriteReport:
        """Plan or write a bundle to an explicit output directory."""
        if not str(output_dir):
            raise ValueError("artifact output_dir cannot be empty")
        write_config = config or TrainingArtifactWriteConfig()
        base = Path(output_dir)
        planned_paths = tuple(str(base / path_from_artifact_path(artifact.path)) for artifact in bundle.artifacts)
        if write_config.dry_run:
            return TrainingArtifactWriteReport(
                str(base),
                True,
                planned_paths,
                metadata={"writer": "TrainingArtifactWriter", **write_config.metadata},
            )
        if not base.exists() and not write_config.create_parents:
            return TrainingArtifactWriteReport(
                str(base),
                False,
                planned_paths,
                skipped_paths=planned_paths,
                errors=("output_dir does not exist and create_parents is false",),
                metadata={"writer": "TrainingArtifactWriter", **write_config.metadata},
            )

        written: list[str] = []
        skipped: list[str] = []
        errors: list[str] = []
        for artifact in bundle.artifacts:
            target = base / path_from_artifact_path(artifact.path)
            if target.exists() and not write_config.overwrite:
                skipped.append(str(target))
                errors.append(f"refusing to overwrite existing artifact: {target}")
                continue
            if not target.parent.exists() and not write_config.create_parents:
                skipped.append(str(target))
                errors.append(f"parent directory does not exist: {target.parent}")
                continue
            if write_config.create_parents:
                target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(artifact.content, encoding="utf-8")
            written.append(str(target))
        return TrainingArtifactWriteReport(
            str(base),
            False,
            planned_paths,
            written,
            skipped,
            errors,
            metadata={"writer": "TrainingArtifactWriter", **write_config.metadata},
        )


def build_demo_training_artifact_bundle() -> TrainingArtifactBundle:
    """Build a deterministic offline demo artifact bundle without writing files."""
    package = build_training_dataset_package(
        create_demo_training_plan_examples(),
        dataset_name="demo-training-artifact-package",
        description="Reviewed examples for a config-only artifact bundle demo.",
        metadata={"demo": "training_artifacts", "config_only": True},
    )
    plan = build_demo_training_plan(package)
    return TrainingArtifactBuilder().build(package, plan, name="demo-training-artifact-bundle")


def dataset_manifest_json(package: TrainingDatasetPackage) -> str:
    """Return stable JSON for dataset package metadata and split summaries."""
    return dumps(
        {
            "dataset": {
                "name": package.dataset.name,
                "description": package.dataset.description,
                "created_at": package.dataset.created_at,
                "example_count": package.dataset.count(),
                "metadata": package.dataset.metadata,
            },
            "splits": [split.to_dict(include_examples=False) for split in package.splits],
            "manifest": package.manifest.to_dict(),
        },
        sort_keys=True,
    )


def model_card_markdown(plan: TrainingPlan) -> str:
    """Return model card markdown with a clear no-training fallback."""
    if plan.model_card_draft:
        return plan.model_card_draft.to_markdown()
    return "\n".join(
        (
            "# Model Card Draft",
            "",
            "## Training Status",
            "not_trained_config_only",
            "",
            "No model has been trained and no model artifact exists.",
        )
    )


def safety_notes_markdown(plan: TrainingPlan) -> str:
    """Return Markdown safety notes and validation results for a bundle."""
    lines = [
        "# Safety Notes",
        "",
        "This artifact bundle is config-only. It does not train, load, download, or upload models.",
        "",
        "## Training Config Safety Notes",
    ]
    lines.extend(markdown_list(plan.config.safety_notes))
    lines.extend(("", "## Validation"))
    lines.append(f"- valid: {plan.validation.valid}")
    lines.extend(f"- warning: {warning}" for warning in plan.validation.warnings)
    lines.extend(f"- error: {error}" for error in plan.validation.errors)
    return "\n".join(lines).strip()


def bundle_readme_markdown(
    package: TrainingDatasetPackage,
    plan: TrainingPlan,
    name: str,
) -> str:
    """Return a concise README for the generated artifact bundle."""
    empty_splits = [name for name, count in package.manifest.split_counts.items() if count == 0]
    lines = [
        f"# Training Artifact Bundle: {name}",
        "",
        "This bundle is a deterministic config-only export foundation.",
        "It does not train a model, load a model, call APIs, download datasets, or upload files.",
        "",
        "## Dataset",
        f"- name: {package.dataset.name}",
        f"- examples: {package.dataset.count()}",
        f"- splits: {split_counts_text(package.manifest.split_counts)}",
        "",
        "## Artifacts",
    ]
    lines.extend(f"- `{path}`" for path in TRAINING_ARTIFACT_PATHS)
    lines.extend(("", "## Empty Splits"))
    if empty_splits:
        lines.extend(f"- `{split}` is empty but still has an empty JSONL artifact." for split in empty_splits)
    else:
        lines.append("- none")
    lines.extend(
        (
            "",
            "## Validation",
            f"- valid: {plan.validation.valid}",
            f"- warnings: {len(plan.validation.warnings)}",
            f"- errors: {len(plan.validation.errors)}",
        )
    )
    return "\n".join(lines).strip()


def split_counts_text(split_counts: Mapping[str, int]) -> str:
    """Return compact split=count text."""
    return ", ".join(f"{name}={count}" for name, count in split_counts.items()) or "none"


def markdown_list(values: Sequence[str]) -> list[str]:
    """Return Markdown list lines with a none fallback."""
    if not values:
        return ["- none"]
    return [f"- {value}" for value in values]


def normalize_artifact_path(path: str) -> str:
    """Return a safe POSIX-style relative artifact path."""
    normalized = str(path).replace("\\", "/").strip()
    pure_path = PurePosixPath(normalized)
    if not normalized or pure_path.is_absolute():
        raise ValueError("artifact path must be a relative path")
    if any(part in {"", ".", ".."} for part in pure_path.parts):
        raise ValueError("artifact path cannot contain empty, current, or parent segments")
    return pure_path.as_posix()


def path_from_artifact_path(path: str) -> Path:
    """Convert a normalized artifact path into a platform path."""
    pure_path = PurePosixPath(normalize_artifact_path(path))
    return Path(*pure_path.parts)
