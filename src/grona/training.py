"""Deterministic training data export foundation for validated Grona traces."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps

from .benchmarks import BenchmarkCase, BenchmarkResult
from .feedback import FeedbackRecord, JsonValue, Metadata
from .growth import KnowledgeSeed
from .growth_review import SeedReviewDecision

TRAINING_VALIDATION_STATUSES = (
    "raw",
    "reviewed",
    "validated",
    "rejected",
    "synthetic_demo",
)


@dataclass(frozen=True)
class TrainingExample:
    """One explicit training example candidate with provenance and validation metadata."""

    instruction: str
    input: str
    output: str
    source: str
    domains: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    provenance: Metadata = field(default_factory=dict)
    license: str = "unknown"
    validation_status: str = "raw"
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        instruction: str,
        input: str,
        output: str,
        source: str,
        domains: Sequence[str] = (),
        capabilities: Sequence[str] = (),
        provenance: Mapping[str, object] | None = None,
        license: str = "unknown",
        validation_status: str = "raw",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "instruction", " ".join(instruction.split()))
        object.__setattr__(self, "input", input.strip())
        object.__setattr__(self, "output", output.strip())
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "domains", tuple(domains))
        object.__setattr__(self, "capabilities", tuple(capabilities))
        object.__setattr__(self, "provenance", json_metadata(provenance or {}))
        object.__setattr__(self, "license", license or "unknown")
        object.__setattr__(self, "validation_status", validation_status)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))
        if not instruction:
            raise ValueError("training example instruction cannot be empty")
        if not source:
            raise ValueError("training example source cannot be empty")
        if validation_status not in TRAINING_VALIDATION_STATUSES:
            raise ValueError(f"unsupported training validation_status: {validation_status}")

    def sort_key(self) -> tuple[str, str, str, str]:
        """Return a deterministic ordering key for dataset output."""
        return (self.source, self.validation_status, self.instruction, self.output)

    def to_alpaca_record(self) -> dict[str, str]:
        """Return an Alpaca-like JSON record with only instruction/input/output."""
        return {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
        }

    def to_native_record(self, include_metadata: bool = True) -> dict[str, object]:
        """Return a Grona-native JSON record with provenance preserved."""
        record: dict[str, object] = {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
            "source": self.source,
            "domains": list(self.domains),
            "capabilities": list(self.capabilities),
            "provenance": self.provenance,
            "license": self.license,
            "validation_status": self.validation_status,
        }
        if include_metadata:
            record["metadata"] = self.metadata
        return record


@dataclass(frozen=True)
class TrainingDataset:
    """In-memory collection of deterministic training example candidates."""

    name: str
    description: str
    examples: tuple[TrainingExample, ...]
    created_at: str = "1970-01-01T00:00:00+00:00"
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        description: str,
        examples: Sequence[TrainingExample] = (),
        created_at: str = "1970-01-01T00:00:00+00:00",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "examples", tuple(sorted(examples, key=lambda item: item.sort_key())))
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "metadata", json_metadata(metadata or {}))
        if not name:
            raise ValueError("training dataset name cannot be empty")
        if not description:
            raise ValueError("training dataset description cannot be empty")

    def count(self) -> int:
        """Return the number of examples."""
        return len(self.examples)

    def domains(self) -> tuple[str, ...]:
        """List unique domains in deterministic order."""
        return tuple(sorted({domain for example in self.examples for domain in example.domains}))

    def sources(self) -> tuple[str, ...]:
        """List unique sources in deterministic order."""
        return tuple(sorted({example.source for example in self.examples}))

    def validation_status_counts(self) -> dict[str, int]:
        """Summarize validation statuses in deterministic key order."""
        counts = Counter(example.validation_status for example in self.examples)
        return {status: counts[status] for status in TRAINING_VALIDATION_STATUSES if counts[status]}

    def to_text(self) -> str:
        """Return a deterministic human-readable summary."""
        domains = ", ".join(self.domains()) or "none"
        sources = ", ".join(self.sources()) or "none"
        statuses = ", ".join(
            f"{status}={count}" for status, count in self.validation_status_counts().items()
        )
        return "\n".join(
            (
                f"Training dataset: {self.name}",
                self.description,
                f"Created at: {self.created_at}",
                f"Examples: {self.count()}",
                f"Domains: {domains}",
                f"Sources: {sources}",
                f"Validation statuses: {statuses or 'none'}",
            )
        )

    def to_native_jsonl(self, include_metadata: bool = True) -> str:
        """Return deterministic Grona-native JSONL without writing files."""
        rows = [
            dumps(example.to_native_record(include_metadata), sort_keys=True)
            for example in self.examples
        ]
        return "\n".join(rows)

    def to_alpaca_jsonl(self) -> str:
        """Return deterministic Alpaca-like JSONL without writing files."""
        rows = [dumps(example.to_alpaca_record(), sort_keys=True) for example in self.examples]
        return "\n".join(rows)


@dataclass(frozen=True)
class TrainingExportConfig:
    """Conservative export policy for training example candidates."""

    allow_raw: bool = False
    allow_synthetic_demo: bool = True
    require_validation: bool = True
    include_metadata: bool = True

    def allows_status(self, status: str) -> bool:
        """Return whether one validation status can be exported."""
        if status == "rejected":
            return False
        if status == "synthetic_demo":
            return self.allow_synthetic_demo
        if status == "raw":
            return self.allow_raw and not self.require_validation
        return status in {"reviewed", "validated"}


class TrainingDataExporter:
    """Build explicit training example candidates from safe Grona records."""

    def __init__(self, config: TrainingExportConfig | None = None) -> None:
        self.config = config or TrainingExportConfig()

    def build_dataset(
        self,
        name: str,
        description: str,
        examples: Sequence[TrainingExample],
        created_at: str = "1970-01-01T00:00:00+00:00",
        metadata: Mapping[str, object] | None = None,
    ) -> TrainingDataset:
        """Create a deterministic in-memory training dataset."""
        exportable = tuple(example for example in examples if self.should_export(example))
        return TrainingDataset(name, description, exportable, created_at, metadata)

    def should_export(self, example: TrainingExample) -> bool:
        """Return whether an example passes the configured export policy."""
        return self.config.allows_status(example.validation_status)

    def from_knowledge_seed(
        self,
        seed: KnowledgeSeed,
        validation_status: str | None = None,
    ) -> TrainingExample | None:
        """Create one example from a validated KnowledgeSeed when policy allows it."""
        status = validation_status or training_status_from_seed(seed)
        example = TrainingExample(
            instruction="Explain the validated knowledge item for future expert behavior.",
            input="",
            output=seed.content,
            source=seed.source.name,
            domains=seed.domains,
            capabilities=("knowledge_recall",),
            provenance=knowledge_seed_provenance(seed),
            license=license_from_metadata(seed.metadata, seed.source.metadata),
            validation_status=status,
            metadata={
                "seed_id": seed.id,
                "seed_status": seed.status,
                "source_type": seed.source.source_type,
                "source_reliability": seed.source.reliability,
                **seed.metadata,
            },
        )
        return example if self.should_export(example) else None

    def from_knowledge_seeds(self, seeds: Sequence[KnowledgeSeed]) -> tuple[TrainingExample, ...]:
        """Create examples from all exportable KnowledgeSeed values."""
        return tuple(
            example
            for seed in seeds
            for example in (self.from_knowledge_seed(seed),)
            if example is not None
        )

    def from_review_decisions(
        self,
        seeds: Sequence[KnowledgeSeed],
        decisions: Sequence[SeedReviewDecision],
    ) -> tuple[TrainingExample, ...]:
        """Create examples from seeds accepted by deterministic review decisions."""
        seed_by_id = {seed.id: seed for seed in seeds}
        examples: list[TrainingExample] = []
        for decision in decisions:
            seed = seed_by_id.get(decision.seed_id)
            if seed is None:
                continue
            status = training_status_from_review_decision(decision)
            example = self.from_knowledge_seed(seed, validation_status=status)
            if example is not None:
                examples.append(
                    add_training_metadata(
                        example,
                        {
                            "review_decision": decision.decision,
                            "review_recommended_status": decision.recommended_status,
                            "review_reasons": list(decision.reasons),
                            **decision.metadata,
                        },
                    )
                )
        return tuple(examples)

    def from_feedback_record(self, record: FeedbackRecord) -> TrainingExample | None:
        """Create one reviewed feedback trace example when policy allows it."""
        status = "reviewed" if feedback_is_positive(record) else "raw"
        example = TrainingExample(
            instruction="Use this feedback trace to improve future routing behavior.",
            input=record.task,
            output=record.route_summary,
            source="feedback",
            domains=(),
            capabilities=("routing", "feedback_analysis"),
            provenance={
                "origin": "feedback_record",
                "timestamp": record.timestamp,
                "selected_modules": list(record.selected_modules),
                "skipped_modules": list(record.skipped_modules),
            },
            license=metadata_license(record.metadata),
            validation_status=status,
            metadata={
                "rating": record.rating,
                "success": record.success,
                "confidence": record.confidence,
                "notes": record.notes,
                **record.metadata,
            },
        )
        return example if self.should_export(example) else None

    def from_benchmark_result(
        self,
        case: BenchmarkCase,
        result: BenchmarkResult,
    ) -> TrainingExample | None:
        """Create one synthetic demo example from a benchmark trace."""
        example = TrainingExample(
            instruction="Route the benchmark task and preserve the expected trace rationale.",
            input=case.task,
            output=result.summary,
            source="benchmark",
            domains=case.expected_domains,
            capabilities=("routing", "benchmark_trace"),
            provenance={
                "origin": "benchmark_result",
                "case_id": case.id,
                "config_name": result.config_name,
                "selected_modules": list(result.selected_modules),
            },
            license=metadata_license(case.metadata, default="synthetic-demo"),
            validation_status="synthetic_demo",
            metadata={
                "overall_score": result.overall_score,
                "routing_score": result.routing_score,
                "context_score": result.context_score,
                "growth_score": result.growth_score,
                **case.metadata,
                **result.metadata,
            },
        )
        return example if self.should_export(example) else None


def training_status_from_seed(seed: KnowledgeSeed) -> str:
    """Map KnowledgeSeed status into training export validation status."""
    if seed.status in {"validated", "promoted"}:
        return "validated"
    if seed.status == "rejected":
        return "rejected"
    return "raw"


def training_status_from_review_decision(decision: SeedReviewDecision) -> str:
    """Map review decisions into conservative training export validation status."""
    if decision.decision == "promote_candidate" or decision.recommended_status == "validated":
        return "validated"
    if decision.decision == "needs_review":
        return "reviewed"
    if decision.decision == "reject_broken":
        return "rejected"
    return "raw"


def knowledge_seed_provenance(seed: KnowledgeSeed) -> Metadata:
    """Build provenance metadata for a KnowledgeSeed training example."""
    return json_metadata(
        {
            "origin": "knowledge_seed",
            "seed_id": seed.id,
            "source_id": seed.source.id,
            "source_type": seed.source.source_type,
            "source_name": seed.source.name,
            "source_reliability": seed.source.reliability,
            "seed_confidence": seed.confidence,
        }
    )


def feedback_is_positive(record: FeedbackRecord) -> bool:
    """Return whether a feedback record is reviewed enough for conservative export."""
    if record.success is True:
        return record.rating is None or record.rating >= 4
    return False


def add_training_metadata(
    example: TrainingExample,
    extra_metadata: Mapping[str, object],
) -> TrainingExample:
    """Return a copy of an example with additional metadata."""
    return TrainingExample(
        instruction=example.instruction,
        input=example.input,
        output=example.output,
        source=example.source,
        domains=example.domains,
        capabilities=example.capabilities,
        provenance=example.provenance,
        license=example.license,
        validation_status=example.validation_status,
        metadata={**example.metadata, **json_metadata(extra_metadata)},
    )


def license_from_metadata(
    *metadata_items: Mapping[str, object],
    default: str = "unknown",
) -> str:
    """Return the first license string found in metadata."""
    for metadata in metadata_items:
        license_value = metadata.get("license") or metadata.get("license_name")
        if isinstance(license_value, str) and license_value:
            return license_value
    return default


def metadata_license(metadata: Mapping[str, object], default: str = "unknown") -> str:
    """Return a license string from one metadata mapping."""
    return license_from_metadata(metadata, default=default)


def json_metadata(metadata: Mapping[str, object]) -> Metadata:
    """Normalize arbitrary simple metadata into JSON-compatible values."""
    return {str(key): json_value(value) for key, value in metadata.items()}


def json_value(value: object) -> JsonValue:
    """Convert common Python values into JSON-compatible metadata."""
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    if isinstance(value, Mapping):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str):
        return [json_value(item) for item in value]
    return str(value)
