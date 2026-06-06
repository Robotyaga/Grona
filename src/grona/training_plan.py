"""Config-only fine-tuning plan scaffold for future adapter experiments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps

from .feedback import Metadata
from .training import TrainingExample, json_metadata
from .training_package import (
    DatasetCardDraft,
    TrainingDatasetPackage,
    TrainingExportManifest,
    TrainingSplitConfig,
    build_training_dataset_package,
)

SUPPORTED_ADAPTER_TYPES = ("lora", "qlora", "full_finetune_placeholder")
CONFIG_ONLY_TRAINING_STATUS = "not_trained_config_only"
DEFAULT_TRAINING_PLAN_CREATED_AT = "2026-01-01T00:00:00+00:00"


@dataclass(frozen=True)
class BaseModelSpec:
    """Identity and policy metadata for a future base model, without loading it."""

    name: str
    provider: str
    model_id: str
    parameter_count: str
    context_length: int
    license: str
    intended_use: str
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        provider: str,
        model_id: str,
        parameter_count: str = "unknown",
        context_length: int = 0,
        license: str = "unknown",
        intended_use: str = "future adapter training experiment",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not name:
            raise ValueError("base model name cannot be empty")
        if not provider:
            raise ValueError("base model provider cannot be empty")
        if not model_id:
            raise ValueError("base model model_id cannot be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "model_id", model_id)
        object.__setattr__(self, "parameter_count", parameter_count or "unknown")
        object.__setattr__(self, "context_length", context_length)
        object.__setattr__(self, "license", license or "unknown")
        object.__setattr__(self, "intended_use", intended_use)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible base model record."""
        return {
            "name": self.name,
            "provider": self.provider,
            "model_id": self.model_id,
            "parameter_count": self.parameter_count,
            "context_length": self.context_length,
            "license": self.license,
            "intended_use": self.intended_use,
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return a readable base model summary."""
        return "\n".join(
            (
                f"Base model: {self.name}",
                f"Provider: {self.provider}",
                f"Model id: {self.model_id}",
                f"Parameters: {self.parameter_count}",
                f"Context length: {self.context_length}",
                f"License: {self.license}",
                f"Intended use: {self.intended_use}",
            )
        )


@dataclass(frozen=True)
class AdapterTrainingSpec:
    """Config-only adapter plan for future LoRA, QLoRA, or placeholder runs."""

    adapter_type: str = "lora"
    rank: int = 8
    alpha: int = 16
    dropout: float = 0.05
    target_modules: tuple[str, ...] = ()
    quantization: str = "none"
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        adapter_type: str = "lora",
        rank: int = 8,
        alpha: int = 16,
        dropout: float = 0.05,
        target_modules: Sequence[str] = (),
        quantization: str = "none",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "adapter_type", adapter_type)
        object.__setattr__(self, "rank", rank)
        object.__setattr__(self, "alpha", alpha)
        object.__setattr__(self, "dropout", dropout)
        object.__setattr__(self, "target_modules", tuple(target_modules))
        object.__setattr__(self, "quantization", quantization or "none")
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible adapter record."""
        return {
            "adapter_type": self.adapter_type,
            "rank": self.rank,
            "alpha": self.alpha,
            "dropout": self.dropout,
            "target_modules": list(self.target_modules),
            "quantization": self.quantization,
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return a readable adapter summary."""
        return "\n".join(
            (
                f"Adapter type: {self.adapter_type}",
                f"Rank: {self.rank}",
                f"Alpha: {self.alpha}",
                f"Dropout: {self.dropout}",
                f"Target modules: {', '.join(self.target_modules) or 'none'}",
                f"Quantization: {self.quantization}",
            )
        )


@dataclass(frozen=True)
class TrainingRunConfig:
    """Config-only description of a future training run."""

    run_name: str
    base_model: BaseModelSpec
    adapter: AdapterTrainingSpec
    dataset_manifest: TrainingExportManifest
    dataset_package_summary: dict[str, object]
    epochs: int = 1
    learning_rate: float = 0.0002
    batch_size: int = 1
    gradient_accumulation_steps: int = 1
    max_sequence_length: int = 2048
    seed: int = 42
    evaluation_plan: str = "deterministic config validation only"
    safety_notes: tuple[str, ...] = ()
    output_policy: str = "no artifacts are written by default"
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        run_name: str,
        base_model: BaseModelSpec,
        adapter: AdapterTrainingSpec,
        dataset_manifest: TrainingExportManifest,
        dataset_package_summary: Mapping[str, object] | None = None,
        epochs: int = 1,
        learning_rate: float = 0.0002,
        batch_size: int = 1,
        gradient_accumulation_steps: int = 1,
        max_sequence_length: int = 2048,
        seed: int = 42,
        evaluation_plan: str = "deterministic config validation only",
        safety_notes: Sequence[str] = (),
        output_policy: str = "no artifacts are written by default",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not run_name:
            raise ValueError("training run name cannot be empty")
        object.__setattr__(self, "run_name", run_name)
        object.__setattr__(self, "base_model", base_model)
        object.__setattr__(self, "adapter", adapter)
        object.__setattr__(self, "dataset_manifest", dataset_manifest)
        object.__setattr__(
            self,
            "dataset_package_summary",
            json_metadata(dataset_package_summary or dataset_summary_from_manifest(dataset_manifest)),
        )
        object.__setattr__(self, "epochs", epochs)
        object.__setattr__(self, "learning_rate", learning_rate)
        object.__setattr__(self, "batch_size", batch_size)
        object.__setattr__(self, "gradient_accumulation_steps", gradient_accumulation_steps)
        object.__setattr__(self, "max_sequence_length", max_sequence_length)
        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "evaluation_plan", evaluation_plan)
        object.__setattr__(self, "safety_notes", tuple(safety_notes))
        object.__setattr__(self, "output_policy", output_policy)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible config record."""
        return {
            "run_name": self.run_name,
            "base_model": self.base_model.to_dict(),
            "adapter": self.adapter.to_dict(),
            "dataset_manifest": self.dataset_manifest.to_dict(),
            "dataset_package_summary": self.dataset_package_summary,
            "epochs": self.epochs,
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "max_sequence_length": self.max_sequence_length,
            "seed": self.seed,
            "evaluation_plan": self.evaluation_plan,
            "safety_notes": list(self.safety_notes),
            "output_policy": self.output_policy,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Return stable JSON for the config."""
        return dumps(self.to_dict(), sort_keys=True)

    def to_text(self) -> str:
        """Return a readable config summary."""
        return "\n".join(
            (
                f"Training run config: {self.run_name}",
                self.base_model.to_text(),
                self.adapter.to_text(),
                f"Dataset: {self.dataset_manifest.dataset_name}",
                f"Total examples: {self.dataset_manifest.total_examples}",
                f"Epochs: {self.epochs}",
                f"Learning rate: {self.learning_rate}",
                f"Batch size: {self.batch_size}",
                f"Gradient accumulation steps: {self.gradient_accumulation_steps}",
                f"Max sequence length: {self.max_sequence_length}",
                f"Seed: {self.seed}",
                f"Evaluation plan: {self.evaluation_plan}",
                f"Output policy: {self.output_policy}",
            )
        )


@dataclass(frozen=True)
class TrainingRunValidationResult:
    """Validation result for a config-only training plan."""

    valid: bool
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        valid: bool,
        warnings: Sequence[str] = (),
        errors: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "valid", valid)
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "errors", tuple(errors))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible validation result."""
        return {
            "valid": self.valid,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return a readable validation summary."""
        status = "valid" if self.valid else "invalid"
        lines = [f"Training run validation: {status}"]
        lines.extend(f"Error: {error}" for error in self.errors)
        lines.extend(f"Warning: {warning}" for warning in self.warnings)
        return "\n".join(lines)


class TrainingRunValidator:
    """Validate training run configuration without training anything."""

    tiny_dataset_threshold = 10

    def validate(self, config: TrainingRunConfig) -> TrainingRunValidationResult:
        """Return config-only validation errors and warnings."""
        errors: list[str] = []
        warnings: list[str] = list(config.dataset_manifest.warnings)
        manifest = config.dataset_manifest
        train_count = int(manifest.split_counts.get("train", 0))
        validation_count = int(manifest.split_counts.get("validation", 0))
        test_count = int(manifest.split_counts.get("test", 0))

        if train_count <= 0:
            errors.append("dataset must contain at least one train example")
        if manifest.total_examples <= 0:
            errors.append("dataset manifest must contain at least one example")
        if validation_count <= 0:
            warnings.append("validation split is empty")
        if test_count <= 0:
            warnings.append("test split is empty")
        if 0 < manifest.total_examples < self.tiny_dataset_threshold:
            warnings.append("dataset is tiny; this config is for scaffolding only")
        if missing_license(config.base_model.license):
            errors.append("base model license must be present")
        if missing_license_summary(manifest.license_summary):
            errors.append("dataset license summary must be present")
        if config.adapter.adapter_type not in SUPPORTED_ADAPTER_TYPES:
            errors.append(f"unsupported adapter type: {config.adapter.adapter_type}")
        if config.adapter.adapter_type in {"lora", "qlora"}:
            if config.adapter.rank <= 0:
                errors.append("adapter rank must be positive")
            if config.adapter.alpha <= 0:
                errors.append("adapter alpha must be positive")
        if config.adapter.adapter_type == "qlora" and config.adapter.quantization == "none":
            warnings.append("qlora adapter config has no quantization label")
        if config.adapter.adapter_type == "full_finetune_placeholder":
            warnings.append("full fine-tune mode is only a placeholder")
        if config.max_sequence_length <= 0:
            errors.append("max sequence length must be positive")
        if config.learning_rate <= 0:
            errors.append("learning rate must be positive")
        if config.epochs <= 0:
            errors.append("epochs must be positive")
        if config.batch_size <= 0:
            errors.append("batch size must be positive")
        if config.gradient_accumulation_steps <= 0:
            errors.append("gradient accumulation steps must be positive")
        if not config.output_policy:
            errors.append("output policy must be present")
        if not config.safety_notes:
            errors.append("safety notes must be present")
        if config.base_model.context_length and config.max_sequence_length > config.base_model.context_length:
            warnings.append("max sequence length exceeds base model context length")

        return TrainingRunValidationResult(
            valid=not errors,
            warnings=dedupe_strings(warnings),
            errors=dedupe_strings(errors),
            metadata={"validator": "TrainingRunValidator", "config_only": True},
        )


@dataclass(frozen=True)
class ModelCardDraft:
    """Markdown draft for a future adapted model, before any training exists."""

    model_name: str
    base_model: BaseModelSpec
    adapter_type: str
    dataset_summary: dict[str, object]
    intended_use: str
    limitations: tuple[str, ...]
    safety_notes: tuple[str, ...]
    evaluation_plan: str
    training_status: str = CONFIG_ONLY_TRAINING_STATUS
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        model_name: str,
        base_model: BaseModelSpec,
        adapter_type: str,
        dataset_summary: Mapping[str, object],
        intended_use: str,
        limitations: Sequence[str],
        safety_notes: Sequence[str],
        evaluation_plan: str,
        training_status: str = CONFIG_ONLY_TRAINING_STATUS,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "model_name", model_name)
        object.__setattr__(self, "base_model", base_model)
        object.__setattr__(self, "adapter_type", adapter_type)
        object.__setattr__(self, "dataset_summary", json_metadata(dataset_summary))
        object.__setattr__(self, "intended_use", intended_use)
        object.__setattr__(self, "limitations", tuple(limitations))
        object.__setattr__(self, "safety_notes", tuple(safety_notes))
        object.__setattr__(self, "evaluation_plan", evaluation_plan)
        object.__setattr__(self, "training_status", training_status)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_markdown(self) -> str:
        """Return a readable Markdown model card draft."""
        lines = [
            f"# Model Card Draft: {self.model_name}",
            "",
            "## Training Status",
            self.training_status,
            "",
            "## Base Model",
            f"- Name: {self.base_model.name}",
            f"- Provider: {self.base_model.provider}",
            f"- Model id: {self.base_model.model_id}",
            f"- License: {self.base_model.license}",
            "",
            "## Adapter",
            f"- Type: {self.adapter_type}",
            "",
            "## Dataset Summary",
        ]
        lines.extend(f"- {key}: {value}" for key, value in self.dataset_summary.items())
        lines.extend(("", "## Intended Use", self.intended_use, "", "## Evaluation Plan"))
        lines.append(self.evaluation_plan)
        lines.extend(("", "## Safety Notes"))
        lines.extend(markdown_list(self.safety_notes))
        lines.extend(("", "## Limitations"))
        lines.extend(markdown_list(self.limitations))
        return "\n".join(lines).strip()


@dataclass(frozen=True)
class TrainingPlan:
    """Complete config-only training plan bundle."""

    config: TrainingRunConfig
    validation: TrainingRunValidationResult
    dataset_card: DatasetCardDraft
    model_card_draft: ModelCardDraft | None = None
    created_at: str = DEFAULT_TRAINING_PLAN_CREATED_AT
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        config: TrainingRunConfig,
        validation: TrainingRunValidationResult,
        dataset_card: DatasetCardDraft,
        model_card_draft: ModelCardDraft | None = None,
        created_at: str = DEFAULT_TRAINING_PLAN_CREATED_AT,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "config", config)
        object.__setattr__(self, "validation", validation)
        object.__setattr__(self, "dataset_card", dataset_card)
        object.__setattr__(self, "model_card_draft", model_card_draft)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible plan summary."""
        return {
            "created_at": self.created_at,
            "config": self.config.to_dict(),
            "validation": self.validation.to_dict(),
            "dataset_card_markdown": self.dataset_card.to_markdown(),
            "model_card_draft_markdown": (
                self.model_card_draft.to_markdown() if self.model_card_draft else None
            ),
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Return a readable plan summary without performing training."""
        return "\n\n".join(
            (
                "Training plan scaffold",
                f"Created at: {self.created_at}",
                "Execution: config only; no model loading, no training, no files, no APIs.",
                self.config.to_text(),
                self.validation.to_text(),
            )
        )


def build_demo_training_plan(
    package: TrainingDatasetPackage | None = None,
    created_at: str = DEFAULT_TRAINING_PLAN_CREATED_AT,
) -> TrainingPlan:
    """Build a deterministic offline demo training plan without training a model."""
    dataset_package = package or build_training_dataset_package(
        create_demo_training_plan_examples(),
        split_config=TrainingSplitConfig(stratify_by_domain=True),
        dataset_name="demo-training-plan-package",
        description="Reviewed examples for a config-only adapter training plan demo.",
        created_at=created_at,
        metadata={"demo": "training_plan", "config_only": True},
    )
    base_model = BaseModelSpec(
        name="Demo local base model placeholder",
        provider="local-placeholder",
        model_id="demo/local-base-model",
        parameter_count="7B-placeholder",
        context_length=4096,
        license="demo-only",
        intended_use="future local adapter experiment planning",
        metadata={"loads_model": False, "downloads_model": False},
    )
    adapter = AdapterTrainingSpec(
        adapter_type="qlora",
        rank=8,
        alpha=16,
        dropout=0.05,
        target_modules=("q_proj", "v_proj"),
        quantization="4bit-placeholder",
        metadata={"training_backend": "not_configured"},
    )
    config = TrainingRunConfig(
        run_name="demo-training-plan-config-only",
        base_model=base_model,
        adapter=adapter,
        dataset_manifest=dataset_package.manifest,
        dataset_package_summary=dataset_summary_from_manifest(dataset_package.manifest),
        epochs=1,
        learning_rate=0.0002,
        batch_size=1,
        gradient_accumulation_steps=4,
        max_sequence_length=2048,
        seed=42,
        evaluation_plan="future deterministic holdout review; no real evaluation yet",
        safety_notes=(
            "Reviewed examples remain candidates, not guaranteed high-quality training data.",
            "No model weights or training artifacts are produced by this scaffold.",
        ),
        output_policy="no artifacts are written unless future caller code opts in explicitly",
        metadata={"config_only": True, "trains_model": False},
    )
    validation = TrainingRunValidator().validate(config)
    dataset_card = DatasetCardDraft.from_package(dataset_package)
    model_card = ModelCardDraft(
        model_name=f"{base_model.name} + {adapter.adapter_type} scaffold",
        base_model=base_model,
        adapter_type=adapter.adapter_type,
        dataset_summary=dataset_summary_from_manifest(dataset_package.manifest),
        intended_use="Configuration review for a future local adapter experiment.",
        limitations=(
            "No model has been trained.",
            "Hyperparameters are placeholders, not recommendations.",
            "No real evaluation has been run.",
        ),
        safety_notes=config.safety_notes,
        evaluation_plan=config.evaluation_plan,
        metadata={"demo": "training_plan"},
    )
    return TrainingPlan(
        config=config,
        validation=validation,
        dataset_card=dataset_card,
        model_card_draft=model_card,
        created_at=created_at,
        metadata={"demo": "training_plan", "config_only": True},
    )


def create_demo_training_plan_examples() -> tuple[TrainingExample, ...]:
    """Create deterministic reviewed examples for the training plan demo."""
    domains = ("routing", "documents", "safety")
    capabilities = ("route_trace", "context_review", "safety_review")
    examples: list[TrainingExample] = []
    for index in range(12):
        domain = domains[index % len(domains)]
        capability = capabilities[index % len(capabilities)]
        examples.append(
            TrainingExample(
                instruction=f"Plan reviewed {domain} adapter example {index}.",
                input=f"Config-only task {index} for {domain} behavior.",
                output=f"Reviewed {domain} behavior {index} preserves provenance and limits.",
                source="reviewed_inference_trace",
                domains=(domain,),
                capabilities=(capability,),
                provenance={
                    "origin": "reviewed_inference_trace",
                    "trace_id": f"trace:plan:{index:02d}",
                    "review_id": f"review:plan:{index:02d}",
                },
                license="demo-only",
                validation_status="reviewed",
                metadata={"demo_index": index, "config_only": True},
            )
        )
    return tuple(examples)


def dataset_summary_from_manifest(manifest: TrainingExportManifest) -> dict[str, object]:
    """Return a compact dataset package summary for training configs."""
    return {
        "dataset_name": manifest.dataset_name,
        "total_examples": manifest.total_examples,
        "split_counts": manifest.split_counts,
        "domain_summary": manifest.domain_summary,
        "license_summary": manifest.license_summary,
        "validation_status_summary": manifest.validation_status_summary,
        "warnings": list(manifest.warnings),
    }


def missing_license(value: str) -> bool:
    """Return whether a license string is absent or unknown."""
    return not value or value == "unknown"


def missing_license_summary(summary: Mapping[str, int]) -> bool:
    """Return whether a dataset license summary is missing useful license data."""
    return not summary or all(missing_license(key) for key in summary)


def markdown_list(values: Sequence[str]) -> list[str]:
    """Return Markdown list lines with a none fallback."""
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
