"""Dataset split and export manifest foundation for training candidates."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps, loads
from random import Random

from .feedback import Metadata
from .training import (
    TRAINING_VALIDATION_STATUSES,
    TrainingDataExporter,
    TrainingDataset,
    TrainingExample,
    json_metadata,
)

TRAINING_SPLIT_NAMES = ("train", "validation", "test")
DEFAULT_PACKAGE_CREATED_AT = "2026-01-01T00:00:00+00:00"


@dataclass(frozen=True)
class TrainingDatasetSplit:
    """One named in-memory dataset split with summary helpers."""

    name: str
    examples: tuple[TrainingExample, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        examples: Sequence[TrainingExample] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        if not name:
            raise ValueError("training dataset split name cannot be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "examples", tuple(examples))
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def count(self) -> int:
        """Return the number of examples in this split."""
        return len(self.examples)

    def domains(self) -> tuple[str, ...]:
        """Return unique domains in deterministic order."""
        return tuple(sorted({domain for example in self.examples for domain in example.domains}))

    def sources(self) -> tuple[str, ...]:
        """Return unique sources in deterministic order."""
        return tuple(sorted({example.source for example in self.examples}))

    def validation_status_counts(self) -> dict[str, int]:
        """Return validation status counts in stable status order."""
        counts = Counter(example.validation_status for example in self.examples)
        return {status: counts[status] for status in TRAINING_VALIDATION_STATUSES if counts[status]}

    def to_native_jsonl(self, include_metadata: bool = True) -> str:
        """Return Grona-native JSONL for this split without writing files."""
        rows = [
            dumps(example.to_native_record(include_metadata), sort_keys=True)
            for example in self.examples
        ]
        return "\n".join(rows)

    def to_alpaca_jsonl(self) -> str:
        """Return Alpaca-like JSONL for this split without writing files."""
        rows = [dumps(example.to_alpaca_record(), sort_keys=True) for example in self.examples]
        return "\n".join(rows)

    def to_dict(self, include_examples: bool = False) -> dict[str, object]:
        """Return a JSON-compatible split summary."""
        data: dict[str, object] = {
            "name": self.name,
            "count": self.count(),
            "domains": list(self.domains()),
            "sources": list(self.sources()),
            "validation_status_counts": self.validation_status_counts(),
            "metadata": self.metadata,
        }
        if include_examples:
            data["examples"] = [example.to_native_record() for example in self.examples]
        return data

    def to_text(self) -> str:
        """Return a compact human-readable split summary."""
        statuses = ", ".join(
            f"{status}={count}" for status, count in self.validation_status_counts().items()
        )
        return "\n".join(
            (
                f"Split: {self.name}",
                f"Examples: {self.count()}",
                f"Domains: {', '.join(self.domains()) or 'none'}",
                f"Sources: {', '.join(self.sources()) or 'none'}",
                f"Validation statuses: {statuses or 'none'}",
            )
        )


@dataclass(frozen=True)
class TrainingSplitConfig:
    """Configuration for deterministic train/validation/test splitting."""

    train_ratio: float = 0.8
    validation_ratio: float = 0.1
    test_ratio: float = 0.1
    seed: int = 42
    stratify_by_domain: bool = False
    min_examples_per_split: int = 1
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        train_ratio: float = 0.8,
        validation_ratio: float = 0.1,
        test_ratio: float = 0.1,
        seed: int = 42,
        stratify_by_domain: bool = False,
        min_examples_per_split: int = 1,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        ratios = (train_ratio, validation_ratio, test_ratio)
        if any(ratio < 0 for ratio in ratios):
            raise ValueError("training split ratios cannot be negative")
        if sum(ratios) <= 0:
            raise ValueError("at least one training split ratio must be positive")
        if min_examples_per_split < 0:
            raise ValueError("min_examples_per_split cannot be negative")
        object.__setattr__(self, "train_ratio", train_ratio)
        object.__setattr__(self, "validation_ratio", validation_ratio)
        object.__setattr__(self, "test_ratio", test_ratio)
        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "stratify_by_domain", stratify_by_domain)
        object.__setattr__(self, "min_examples_per_split", min_examples_per_split)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))

    def normalized_ratios(self) -> tuple[float, float, float]:
        """Return ratios normalized to a sum of one."""
        total = self.train_ratio + self.validation_ratio + self.test_ratio
        return (self.train_ratio / total, self.validation_ratio / total, self.test_ratio / total)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible configuration record."""
        return {
            "train_ratio": self.train_ratio,
            "validation_ratio": self.validation_ratio,
            "test_ratio": self.test_ratio,
            "seed": self.seed,
            "stratify_by_domain": self.stratify_by_domain,
            "min_examples_per_split": self.min_examples_per_split,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Return stable JSON for this configuration."""
        return dumps(self.to_dict(), sort_keys=True)


class TrainingDatasetSplitter:
    """Create deterministic in-memory dataset splits."""

    def __init__(self, config: TrainingSplitConfig | None = None) -> None:
        self.config = config or TrainingSplitConfig()

    def split(
        self,
        dataset_or_examples: TrainingDataset | Sequence[TrainingExample],
    ) -> tuple[TrainingDatasetSplit, TrainingDatasetSplit, TrainingDatasetSplit]:
        """Split a dataset or sequence of examples into train, validation, and test."""
        examples = examples_from_dataset_or_sequence(dataset_or_examples)
        ordered = tuple(sorted(examples, key=lambda example: example.sort_key()))
        if not ordered:
            return split_tuple((), (), (), self.config)
        if self.config.stratify_by_domain:
            return self._stratified_split(ordered)
        shuffled = list(ordered)
        Random(self.config.seed).shuffle(shuffled)
        counts = split_counts(len(shuffled), self.config)
        return split_tuple_by_counts(tuple(shuffled), counts, self.config)

    def _stratified_split(
        self,
        examples: tuple[TrainingExample, ...],
    ) -> tuple[TrainingDatasetSplit, TrainingDatasetSplit, TrainingDatasetSplit]:
        grouped: dict[str, list[TrainingExample]] = defaultdict(list)
        for example in examples:
            grouped[primary_domain(example)].append(example)
        buckets: dict[str, list[TrainingExample]] = {name: [] for name in TRAINING_SPLIT_NAMES}
        for offset, domain in enumerate(sorted(grouped)):
            domain_examples = sorted(grouped[domain], key=lambda example: example.sort_key())
            Random(self.config.seed + offset).shuffle(domain_examples)
            counts = split_counts(len(domain_examples), self.config)
            start = 0
            for name, count in zip(TRAINING_SPLIT_NAMES, counts, strict=True):
                buckets[name].extend(domain_examples[start : start + count])
                start += count
        return split_tuple(
            stable_shuffle(buckets["train"], self.config.seed + 101),
            stable_shuffle(buckets["validation"], self.config.seed + 102),
            stable_shuffle(buckets["test"], self.config.seed + 103),
            self.config,
        )


def examples_from_dataset_or_sequence(
    dataset_or_examples: TrainingDataset | Sequence[TrainingExample],
) -> tuple[TrainingExample, ...]:
    """Return examples from either a TrainingDataset or a plain sequence."""
    if isinstance(dataset_or_examples, TrainingDataset):
        return dataset_or_examples.examples
    return tuple(dataset_or_examples)


def primary_domain(example: TrainingExample) -> str:
    """Return the first domain for simple stratification, or unknown."""
    return example.domains[0] if example.domains else "unknown"


def split_counts(total: int, config: TrainingSplitConfig) -> tuple[int, int, int]:
    """Return deterministic split counts for a dataset size."""
    if total <= 0:
        return (0, 0, 0)
    if total == 1:
        return (1, 0, 0)
    ratios = config.normalized_ratios()
    raw_counts = [ratio * total for ratio in ratios]
    counts = [int(count) for count in raw_counts]
    remaining = total - sum(counts)
    remainders = sorted(
        ((raw_counts[index] - counts[index], index) for index in range(3)),
        key=lambda item: (-item[0], item[1]),
    )
    for _fraction, index in remainders[:remaining]:
        counts[index] += 1
    positive_ratio_indexes = [index for index, ratio in enumerate(ratios) if ratio > 0]
    if total >= len(positive_ratio_indexes) and config.min_examples_per_split > 0:
        for index in positive_ratio_indexes:
            if counts[index] == 0:
                donor = max(
                    range(3),
                    key=lambda candidate: counts[candidate] - config.min_examples_per_split,
                )
                if counts[donor] > config.min_examples_per_split:
                    counts[donor] -= 1
                    counts[index] += 1
    return (counts[0], counts[1], counts[2])


def split_tuple_by_counts(
    examples: tuple[TrainingExample, ...],
    counts: tuple[int, int, int],
    config: TrainingSplitConfig,
) -> tuple[TrainingDatasetSplit, TrainingDatasetSplit, TrainingDatasetSplit]:
    """Build split records from ordered examples and explicit counts."""
    train_count, validation_count, test_count = counts
    train = examples[:train_count]
    validation = examples[train_count : train_count + validation_count]
    test = examples[train_count + validation_count : train_count + validation_count + test_count]
    return split_tuple(train, validation, test, config)


def split_tuple(
    train: Sequence[TrainingExample],
    validation: Sequence[TrainingExample],
    test: Sequence[TrainingExample],
    config: TrainingSplitConfig,
) -> tuple[TrainingDatasetSplit, TrainingDatasetSplit, TrainingDatasetSplit]:
    """Return split records with shared config metadata."""
    metadata = {"split_config": config.to_dict()}
    return (
        TrainingDatasetSplit("train", train, metadata),
        TrainingDatasetSplit("validation", validation, metadata),
        TrainingDatasetSplit("test", test, metadata),
    )


def stable_shuffle(examples: Sequence[TrainingExample], seed: int) -> tuple[TrainingExample, ...]:
    """Return a deterministic shuffled tuple."""
    items = list(examples)
    Random(seed).shuffle(items)
    return tuple(items)


@dataclass(frozen=True)
class TrainingExportManifest:
    """Manifest describing a packaged in-memory training dataset export."""

    dataset_name: str
    created_at: str
    split_config: TrainingSplitConfig
    split_counts: dict[str, int]
    total_examples: int
    domain_summary: dict[str, int]
    capability_summary: dict[str, int]
    source_summary: dict[str, int]
    license_summary: dict[str, int]
    validation_status_summary: dict[str, int]
    provenance_summary: dict[str, object]
    warnings: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    @classmethod
    def from_dataset_and_splits(
        cls,
        dataset: TrainingDataset,
        splits: Sequence[TrainingDatasetSplit],
        split_config: TrainingSplitConfig,
        created_at: str = DEFAULT_PACKAGE_CREATED_AT,
        warnings: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> TrainingExportManifest:
        """Build a manifest from a dataset and its deterministic splits."""
        examples = dataset.examples
        return cls(
            dataset_name=dataset.name,
            created_at=created_at,
            split_config=split_config,
            split_counts={split.name: split.count() for split in splits},
            total_examples=dataset.count(),
            domain_summary=count_many(example.domains for example in examples),
            capability_summary=count_many(example.capabilities for example in examples),
            source_summary=count_one(example.source for example in examples),
            license_summary=count_one(example.license for example in examples),
            validation_status_summary=count_validation_statuses(examples),
            provenance_summary=provenance_summary(examples),
            warnings=tuple(warnings),
            metadata={**dataset.metadata, **json_metadata(metadata or {})},
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible manifest record."""
        return {
            "dataset_name": self.dataset_name,
            "created_at": self.created_at,
            "split_config": self.split_config.to_dict(),
            "split_counts": self.split_counts,
            "total_examples": self.total_examples,
            "domain_summary": self.domain_summary,
            "capability_summary": self.capability_summary,
            "source_summary": self.source_summary,
            "license_summary": self.license_summary,
            "validation_status_summary": self.validation_status_summary,
            "provenance_summary": self.provenance_summary,
            "warnings": list(self.warnings),
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Return stable JSON for this manifest."""
        return dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> TrainingExportManifest:
        """Rebuild a manifest from its JSON representation."""
        data = loads(text)
        config_data = data["split_config"]
        return cls(
            dataset_name=data["dataset_name"],
            created_at=data["created_at"],
            split_config=TrainingSplitConfig(
                train_ratio=config_data["train_ratio"],
                validation_ratio=config_data["validation_ratio"],
                test_ratio=config_data["test_ratio"],
                seed=config_data["seed"],
                stratify_by_domain=config_data["stratify_by_domain"],
                min_examples_per_split=config_data["min_examples_per_split"],
                metadata=config_data.get("metadata", {}),
            ),
            split_counts=dict(data["split_counts"]),
            total_examples=data["total_examples"],
            domain_summary=dict(data["domain_summary"]),
            capability_summary=dict(data["capability_summary"]),
            source_summary=dict(data["source_summary"]),
            license_summary=dict(data["license_summary"]),
            validation_status_summary=dict(data["validation_status_summary"]),
            provenance_summary=dict(data["provenance_summary"]),
            warnings=tuple(data.get("warnings", ())),
            metadata=data.get("metadata", {}),
        )

    def to_text(self) -> str:
        """Return a readable manifest summary."""
        split_text = ", ".join(f"{name}={count}" for name, count in self.split_counts.items())
        warning_text = "; ".join(self.warnings) if self.warnings else "none"
        return "\n".join(
            (
                f"Training export manifest: {self.dataset_name}",
                f"Created at: {self.created_at}",
                f"Examples: {self.total_examples}",
                f"Splits: {split_text}",
                f"Domains: {summary_text(self.domain_summary)}",
                f"Capabilities: {summary_text(self.capability_summary)}",
                f"Sources: {summary_text(self.source_summary)}",
                f"Licenses: {summary_text(self.license_summary)}",
                f"Validation: {summary_text(self.validation_status_summary)}",
                f"Warnings: {warning_text}",
            )
        )


@dataclass(frozen=True)
class TrainingDatasetPackage:
    """In-memory dataset package with splits and manifest previews."""

    dataset: TrainingDataset
    splits: tuple[TrainingDatasetSplit, ...]
    manifest: TrainingExportManifest

    def native_jsonl_by_split(self, include_metadata: bool = True) -> dict[str, str]:
        """Return Grona-native JSONL previews for each split without writing files."""
        return {
            split.name: split.to_native_jsonl(include_metadata=include_metadata)
            for split in self.splits
        }

    def alpaca_jsonl_by_split(self) -> dict[str, str]:
        """Return Alpaca-like JSONL previews for each split without writing files."""
        return {split.name: split.to_alpaca_jsonl() for split in self.splits}

    def to_text(self) -> str:
        """Return a compact package summary."""
        split_lines = [split.to_text() for split in self.splits]
        return "\n\n".join((self.dataset.to_text(), self.manifest.to_text(), *split_lines))


@dataclass(frozen=True)
class DatasetCardDraft:
    """Markdown draft for an inspectable training dataset card."""

    dataset_name: str
    description: str
    intended_use: str
    limitations: tuple[str, ...]
    sources: tuple[str, ...]
    licenses: tuple[str, ...]
    validation_process: str
    splits: dict[str, int]
    warnings: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    @classmethod
    def from_package(
        cls,
        package: TrainingDatasetPackage,
        intended_use: str = "Future reviewed training-data experiments only.",
        validation_process: str = "Examples pass the current conservative export policy.",
        limitations: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> DatasetCardDraft:
        """Build a dataset card draft from a package manifest."""
        manifest = package.manifest
        default_limitations = (
            "This package does not train a model.",
            "The manifest is not a quality guarantee.",
            "File export is left to explicit caller code.",
        )
        return cls(
            dataset_name=package.dataset.name,
            description=package.dataset.description,
            intended_use=intended_use,
            limitations=tuple(limitations) or default_limitations,
            sources=tuple(manifest.source_summary),
            licenses=tuple(manifest.license_summary),
            validation_process=validation_process,
            splits=manifest.split_counts,
            warnings=manifest.warnings,
            metadata={**manifest.metadata, **json_metadata(metadata or {})},
        )

    def to_markdown(self) -> str:
        """Return a readable Markdown dataset card draft."""
        lines = [
            f"# Dataset Card Draft: {self.dataset_name}",
            "",
            "## Description",
            self.description,
            "",
            "## Intended Use",
            self.intended_use,
            "",
            "## Splits",
        ]
        lines.extend(f"- {name}: {count}" for name, count in self.splits.items())
        lines.extend(("", "## Sources"))
        lines.extend(format_list(self.sources))
        lines.extend(("", "## Licenses"))
        lines.extend(format_list(self.licenses))
        lines.extend(("", "## Validation Process", self.validation_process, "", "## Limitations"))
        lines.extend(format_list(self.limitations))
        lines.extend(("", "## Warnings"))
        lines.extend(format_list(self.warnings))
        return "\n".join(lines).strip()


def build_training_dataset_package(
    examples: Sequence[TrainingExample],
    split_config: TrainingSplitConfig | None = None,
    dataset_name: str = "training-dataset-package",
    description: str = "Deterministic in-memory training dataset package.",
    created_at: str = DEFAULT_PACKAGE_CREATED_AT,
    metadata: Mapping[str, object] | None = None,
) -> TrainingDatasetPackage:
    """Build a deterministic package from exportable training examples."""
    config = split_config or TrainingSplitConfig()
    warnings = package_warnings(examples, config)
    dataset = TrainingDataExporter().build_dataset(
        dataset_name,
        description,
        examples,
        created_at=created_at,
        metadata={"package_builder": "build_training_dataset_package", **json_metadata(metadata or {})},
    )
    splits = TrainingDatasetSplitter(config).split(dataset)
    warnings = (*warnings, *split_warnings(splits, config, dataset.count()))
    manifest = TrainingExportManifest.from_dataset_and_splits(
        dataset,
        splits,
        config,
        created_at=created_at,
        warnings=dedupe_strings(warnings),
    )
    return TrainingDatasetPackage(dataset=dataset, splits=splits, manifest=manifest)


def package_warnings(
    examples: Sequence[TrainingExample],
    config: TrainingSplitConfig,
) -> tuple[str, ...]:
    """Return conservative package warnings before export policy filtering."""
    _ = config
    total = len(examples)
    status_counts = Counter(example.validation_status for example in examples)
    warnings: list[str] = []
    if total == 0:
        warnings.append("No examples were provided.")
    for status in ("raw", "rejected"):
        if status_counts[status]:
            warnings.append(f"{status_counts[status]} {status} examples will be skipped by export policy.")
    if any(example.metadata.get("unsafe") is True for example in examples):
        warnings.append("One or more examples carry unsafe metadata and should be reviewed.")
    return tuple(warnings)


def split_warnings(
    splits: Sequence[TrainingDatasetSplit],
    config: TrainingSplitConfig,
    total_examples: int,
) -> tuple[str, ...]:
    """Return warnings for small or underfilled splits."""
    warnings: list[str] = []
    if 0 < total_examples < 3:
        warnings.append("Dataset is too small for all train/validation/test splits to be populated.")
    for split in splits:
        if total_examples and split.count() < config.min_examples_per_split:
            warnings.append(f"Split {split.name} has fewer examples than min_examples_per_split.")
    return tuple(warnings)


def count_many(values: Iterable[Sequence[str]]) -> dict[str, int]:
    """Count many string values in deterministic key order."""
    counter: Counter[str] = Counter()
    for sequence in values:
        counter.update(str(value) for value in sequence if value)
    return dict(sorted(counter.items()))


def count_one(values: Iterable[str]) -> dict[str, int]:
    """Count one string value per example in deterministic key order."""
    counter = Counter(str(value) or "unknown" for value in values)
    return dict(sorted(counter.items()))


def count_validation_statuses(examples: Sequence[TrainingExample]) -> dict[str, int]:
    """Count validation statuses in stable status order."""
    counter = Counter(example.validation_status for example in examples)
    return {status: counter[status] for status in TRAINING_VALIDATION_STATUSES if counter[status]}


def provenance_summary(examples: Sequence[TrainingExample]) -> dict[str, object]:
    """Summarize simple provenance fields for auditability."""
    origins = Counter(str(example.provenance.get("origin", "unknown")) for example in examples)
    trace_count = sum(1 for example in examples if "trace_id" in example.provenance)
    review_count = sum(1 for example in examples if "review_id" in example.provenance)
    return {
        "origin_counts": dict(sorted(origins.items())),
        "trace_count": trace_count,
        "review_count": review_count,
    }


def summary_text(summary: Mapping[str, int]) -> str:
    """Return a compact key=count summary."""
    return ", ".join(f"{key}={value}" for key, value in summary.items()) or "none"


def format_list(values: Sequence[str]) -> list[str]:
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
