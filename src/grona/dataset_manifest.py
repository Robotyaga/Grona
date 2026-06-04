"""Dataset manifest, license policy, and JSONL ingestion foundation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import JSONDecodeError, loads
from pathlib import Path
from typing import TextIO

from .datasets import (
    AlpacaFormatAdapter,
    DatasetSample,
    DatasetSource,
    ShareGPTFormatAdapter,
    clean_text,
    extract_keywords,
    infer_domains,
)
from .feedback import Metadata
from .growth import KnowledgeSeed

DATASET_ALLOWED_USES = (
    "routing_eval",
    "knowledge_seed_candidate",
    "training_export_candidate",
    "benchmark_candidate",
)
DATASET_MANIFEST_FORMATS = ("alpaca", "sharegpt", "jsonl", "text", "unknown")
BLOCKED_TRAINING_LICENSES = (
    "unknown",
    "unknown-demo-license",
    "research-only",
    "research-only-demo",
    "non-commercial",
    "proprietary",
)


@dataclass(frozen=True)
class DatasetManifest:
    """Explicit description of a small local dataset source before ingestion."""

    name: str
    description: str
    source: str
    format: str
    license: str
    allowed_uses: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    requires_review: bool = True
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        description: str,
        source: str,
        format: str = "jsonl",
        license: str = "unknown",
        allowed_uses: Sequence[str] = (),
        domains: Sequence[str] = (),
        capabilities: Sequence[str] = (),
        requires_review: bool = True,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "format", format)
        object.__setattr__(self, "license", license or "unknown")
        object.__setattr__(self, "allowed_uses", tuple(allowed_uses))
        object.__setattr__(self, "domains", tuple(domains))
        object.__setattr__(self, "capabilities", tuple(capabilities))
        object.__setattr__(self, "requires_review", requires_review)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not name:
            raise ValueError("dataset manifest name cannot be empty")
        if not description:
            raise ValueError("dataset manifest description cannot be empty")
        if not source:
            raise ValueError("dataset manifest source cannot be empty")
        if format not in DATASET_MANIFEST_FORMATS:
            raise ValueError(f"unsupported dataset manifest format: {format}")
        for allowed_use in self.allowed_uses:
            if allowed_use not in DATASET_ALLOWED_USES:
                raise ValueError(f"unsupported dataset allowed use: {allowed_use}")

    def to_dataset_source(self) -> DatasetSource:
        """Convert the manifest into the existing DatasetSource shape."""
        return DatasetSource(
            id=f"dataset:{slug(self.name)}",
            name=self.name,
            source_type=source_type_from_manifest(self),
            format=source_format_from_manifest(self),
            license=self.license,
            language=str(self.metadata.get("language", "unknown")),
            reliability=float(self.metadata.get("reliability", 0.5)),
            metadata={
                "manifest_name": self.name,
                "manifest_source": self.source,
                "allowed_uses": list(self.allowed_uses),
                "requires_review": self.requires_review,
                "manifest_format": self.format,
                **self.metadata,
            },
        )


@dataclass(frozen=True)
class DatasetPolicyDecision:
    """Deterministic policy decision for one manifest use."""

    use: str
    allowed: bool
    reason: str
    review_required: bool

    def to_text(self) -> str:
        """Format the policy decision for reports."""
        status = "allowed" if self.allowed else "rejected"
        review = "review required" if self.review_required else "no review required"
        return f"{self.use}: {status}; {review}; {self.reason}"


@dataclass(frozen=True)
class DatasetLicensePolicy:
    """Conservative policy for manifest allowed uses and license boundaries."""

    blocked_training_licenses: tuple[str, ...] = BLOCKED_TRAINING_LICENSES

    def decision_for_use(self, manifest: DatasetManifest, use: str) -> DatasetPolicyDecision:
        """Return whether one manifest use is allowed and why."""
        if use not in DATASET_ALLOWED_USES:
            return DatasetPolicyDecision(use, False, "unsupported allowed use", True)
        if use not in manifest.allowed_uses:
            return DatasetPolicyDecision(use, False, "use is not listed in manifest", True)
        if use == "training_export_candidate" and self.training_license_blocked(manifest):
            return DatasetPolicyDecision(
                use,
                False,
                f"license is not training-safe: {manifest.license}",
                True,
            )
        return DatasetPolicyDecision(
            use,
            True,
            "use is listed in manifest and passes license policy",
            manifest.requires_review,
        )

    def can_create_knowledge_seed_candidates(self, manifest: DatasetManifest) -> bool:
        """Return whether the manifest can produce knowledge seed candidates."""
        return self.decision_for_use(manifest, "knowledge_seed_candidate").allowed

    def can_create_training_export_candidates(self, manifest: DatasetManifest) -> bool:
        """Return whether the manifest can produce training export candidates."""
        return self.decision_for_use(manifest, "training_export_candidate").allowed

    def review_required(self, manifest: DatasetManifest) -> bool:
        """Return whether review is required before promotion or export."""
        return manifest.requires_review

    def policy_summary(self, manifest: DatasetManifest) -> tuple[DatasetPolicyDecision, ...]:
        """Return deterministic decisions for all supported allowed uses."""
        return tuple(self.decision_for_use(manifest, allowed_use) for allowed_use in DATASET_ALLOWED_USES)

    def training_license_blocked(self, manifest: DatasetManifest) -> bool:
        """Return whether license metadata blocks training export candidates."""
        normalized = manifest.license.lower().strip()
        return any(blocked in normalized for blocked in self.blocked_training_licenses)


@dataclass(frozen=True)
class JsonlDatasetRecord:
    """One parsed JSONL row with its source line number."""

    line_number: int
    data: dict[str, object]
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        line_number: int,
        data: Mapping[str, object],
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "line_number", line_number)
        object.__setattr__(self, "data", dict(data))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if line_number < 1:
            raise ValueError("JSONL line_number must be positive")


@dataclass(frozen=True)
class DatasetIngestionReport:
    """Deterministic report for one manifest-aware JSONL ingestion run."""

    manifest_name: str
    records_read: int
    records_accepted: int
    records_rejected: int
    rejection_reasons: tuple[str, ...]
    normalized_sample_count: int
    policy_decisions: tuple[DatasetPolicyDecision, ...]
    metadata: Metadata = field(default_factory=dict)

    def to_text(self) -> str:
        """Format the report for CLI demos."""
        lines = [
            f"Dataset ingestion report: {self.manifest_name}",
            f"Records read: {self.records_read}",
            f"Records accepted: {self.records_accepted}",
            f"Records rejected: {self.records_rejected}",
            f"Normalized samples: {self.normalized_sample_count}",
            "Policy decisions:",
        ]
        lines.extend(f"- {decision.to_text()}" for decision in self.policy_decisions)
        if self.rejection_reasons:
            lines.append("Rejections:")
            lines.extend(f"- {reason}" for reason in self.rejection_reasons)
        return "\n".join(lines)


class DatasetIngestor:
    """Manifest-aware JSONL ingestor for small deterministic local samples."""

    def __init__(self, policy: DatasetLicensePolicy | None = None) -> None:
        self.policy = policy or DatasetLicensePolicy()

    def ingest_records(
        self,
        manifest: DatasetManifest,
        records: Sequence[JsonlDatasetRecord],
    ) -> tuple[tuple[DatasetSample, ...], DatasetIngestionReport]:
        """Normalize supported JSONL records and return samples plus a report."""
        policy_decisions = self.policy.policy_summary(manifest)
        source = manifest.to_dataset_source()
        samples: list[DatasetSample] = []
        rejection_reasons: list[str] = []
        manifest_allowed = any(decision.allowed for decision in policy_decisions)
        if not manifest_allowed:
            rejection_reasons.append("manifest rejected for all supported uses")
        for record in records:
            if not manifest_allowed:
                rejection_reasons.append(f"line {record.line_number}: manifest policy rejected record")
                continue
            sample = normalize_jsonl_record(record, manifest, source)
            if sample is None:
                rejection_reasons.append(f"line {record.line_number}: unsupported or incomplete record")
                continue
            samples.append(sample)
        report = DatasetIngestionReport(
            manifest_name=manifest.name,
            records_read=len(records),
            records_accepted=len(samples),
            records_rejected=len(records) - len(samples),
            rejection_reasons=tuple(rejection_reasons),
            normalized_sample_count=len(samples),
            policy_decisions=policy_decisions,
            metadata={
                "manifest_source": manifest.source,
                "manifest_format": manifest.format,
                "manifest_license": manifest.license,
            },
        )
        return tuple(samples), report

    def ingest_jsonl_text(
        self,
        manifest: DatasetManifest,
        text: str,
    ) -> tuple[tuple[DatasetSample, ...], DatasetIngestionReport]:
        """Parse and ingest a JSONL text block."""
        return self.ingest_records(manifest, read_jsonl_records(text))

    def knowledge_seed_candidates(
        self,
        manifest: DatasetManifest,
        records: Sequence[JsonlDatasetRecord],
    ) -> tuple[tuple[KnowledgeSeed, ...], DatasetIngestionReport]:
        """Return raw KnowledgeSeed candidates when manifest policy allows it."""
        from .datasets import knowledge_seeds_from_dataset_samples

        samples, report = self.ingest_records(manifest, records)
        if not self.policy.can_create_knowledge_seed_candidates(manifest):
            return (), report
        return knowledge_seeds_from_dataset_samples(samples), report


def read_jsonl_records(text: str, strict: bool = True) -> tuple[JsonlDatasetRecord, ...]:
    """Parse JSONL text into records while preserving source line numbers."""
    records: list[JsonlDatasetRecord] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = loads(stripped)
        except JSONDecodeError as exc:
            if strict:
                raise ValueError(f"invalid JSONL at line {line_number}: {exc.msg}") from exc
            continue
        if not isinstance(parsed, Mapping):
            if strict:
                raise ValueError(f"invalid JSONL at line {line_number}: expected object")
            continue
        records.append(JsonlDatasetRecord(line_number, parsed, {"origin": "jsonl_text"}))
    return tuple(records)


def read_jsonl_stream(stream: TextIO, strict: bool = True) -> tuple[JsonlDatasetRecord, ...]:
    """Parse records from an already-open text stream."""
    return read_jsonl_records(stream.read(), strict=strict)


def read_jsonl_file(path: str | Path, strict: bool = True) -> tuple[JsonlDatasetRecord, ...]:
    """Parse records from an explicit JSONL path without scanning directories."""
    with Path(path).open("r", encoding="utf-8") as handle:
        return read_jsonl_stream(handle, strict=strict)


def normalize_jsonl_record(
    record: JsonlDatasetRecord,
    manifest: DatasetManifest,
    source: DatasetSource,
) -> DatasetSample | None:
    """Normalize one supported JSONL record into the existing DatasetSample shape."""
    data = record.data
    if has_alpaca_shape(data):
        return first_dataset_sample(
            AlpacaFormatAdapter().parse((record_with_metadata(record, manifest),), source)
        )
    if has_sharegpt_shape(data):
        return first_dataset_sample(
            ShareGPTFormatAdapter().parse((record_with_metadata(record, manifest),), source)
        )
    text = clean_text(data.get("text"))
    if text:
        return generic_text_sample(record, manifest, source, text)
    return None


def record_with_metadata(
    record: JsonlDatasetRecord,
    manifest: DatasetManifest,
) -> dict[str, object]:
    """Attach manifest and line metadata to one loose record."""
    metadata = record_metadata(record, manifest)
    return {**record.data, "metadata": metadata}


def record_metadata(record: JsonlDatasetRecord, manifest: DatasetManifest) -> Metadata:
    """Build metadata shared by all normalized records."""
    return {
        "origin": "jsonl_dataset_record",
        "line_number": record.line_number,
        "manifest_name": manifest.name,
        "manifest_source": manifest.source,
        "manifest_license": manifest.license,
        "manifest_allowed_uses": list(manifest.allowed_uses),
        "manifest_requires_review": manifest.requires_review,
        **manifest.metadata,
        **record.metadata,
    }


def generic_text_sample(
    record: JsonlDatasetRecord,
    manifest: DatasetManifest,
    source: DatasetSource,
    text: str,
) -> DatasetSample:
    """Normalize a generic text JSONL row into a DatasetSample."""
    domains = manifest.domains or infer_domains(text)
    keywords = extract_keywords(text)
    return DatasetSample(
        id=f"{source.id}:text-{record.line_number:04d}",
        source=source,
        content=text,
        sample_type="unknown",
        domains=domains,
        keywords=keywords,
        metadata=record_metadata(record, manifest),
    )


def first_dataset_sample(samples: Sequence[object]) -> DatasetSample | None:
    """Return the first adapter-normalized generic sample."""
    if not samples:
        return None
    sample = samples[0]
    if hasattr(sample, "to_dataset_sample"):
        return sample.to_dataset_sample()
    if isinstance(sample, DatasetSample):
        return sample
    return None


def has_alpaca_shape(data: Mapping[str, object]) -> bool:
    """Return whether a JSON object looks Alpaca-like."""
    return "instruction" in data and "output" in data


def has_sharegpt_shape(data: Mapping[str, object]) -> bool:
    """Return whether a JSON object looks ShareGPT-like."""
    return "conversations" in data or "messages" in data


def source_type_from_manifest(manifest: DatasetManifest) -> str:
    """Infer the existing DatasetSource source_type from manifest fields."""
    if manifest.format == "sharegpt":
        return "conversation_dataset"
    if manifest.format == "alpaca":
        return "instruction_dataset"
    if "code" in manifest.domains:
        return "code_dataset"
    return "unknown"


def source_format_from_manifest(manifest: DatasetManifest) -> str:
    """Map manifest format into existing DatasetSource format values."""
    if manifest.format in {"alpaca", "sharegpt", "jsonl", "text"}:
        return manifest.format
    return "unknown"


def slug(value: str) -> str:
    """Create a deterministic id-safe slug."""
    cleaned = "".join(character if character.isalnum() else "-" for character in value.lower())
    return "-".join(part for part in cleaned.split("-") if part) or "unknown"
