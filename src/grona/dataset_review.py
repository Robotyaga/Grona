"""Deterministic dataset sample quality review before promotion or export."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256

from .dataset_manifest import DatasetLicensePolicy, DatasetManifest
from .datasets import DatasetSample, knowledge_seed_from_dataset_sample
from .feedback import Metadata
from .growth import KnowledgeSeed

DATASET_REVIEW_DECISIONS = (
    "accepted",
    "rejected_empty",
    "rejected_too_short",
    "rejected_duplicate",
    "rejected_license",
    "rejected_unsupported",
    "needs_human_review",
)
SUSPICIOUS_MARKERS = (
    "ignore previous instructions",
    "system prompt",
    "developer message",
    "jailbreak",
    "prompt injection",
    "do not obey",
    "reveal secrets",
    "api key",
    "password",
)
SUPPORTED_REVIEW_SAMPLE_TYPES = (
    "instruction",
    "conversation",
    "factual_qa",
    "reasoning",
    "writing",
    "classification",
    "summarization",
    "code",
    "unknown",
)
ANSWER_SAMPLE_TYPES = {
    "instruction",
    "conversation",
    "factual_qa",
    "reasoning",
    "classification",
    "summarization",
    "code",
}
HARD_REJECTION_REASONS = {
    "content is too short",
    "output or assistant answer is missing",
    "output is too short",
}


@dataclass(frozen=True)
class DatasetSampleReview:
    """Deterministic review decision for one normalized dataset sample."""

    sample_id: str
    accepted: bool
    decision: str
    reasons: tuple[str, ...]
    quality_score: float
    domains: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        sample_id: str,
        accepted: bool,
        decision: str,
        reasons: Sequence[str] = (),
        quality_score: float = 0.0,
        domains: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "sample_id", sample_id)
        object.__setattr__(self, "accepted", accepted)
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "reasons", tuple(reasons))
        object.__setattr__(self, "quality_score", round(quality_score, 3))
        object.__setattr__(self, "domains", tuple(domains))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not sample_id:
            raise ValueError("dataset sample review sample_id cannot be empty")
        if decision not in DATASET_REVIEW_DECISIONS:
            raise ValueError(f"unsupported dataset review decision: {decision}")
        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError("dataset review quality_score must be between 0.0 and 1.0")

    def to_text(self) -> str:
        """Format one review decision for demo output."""
        status = "accepted" if self.accepted else "rejected"
        reasons = "; ".join(self.reasons) or "no issues"
        return (
            f"{self.sample_id}: {status}; decision={self.decision}; "
            f"score={self.quality_score:.2f}; reasons={reasons}"
        )


@dataclass(frozen=True)
class DatasetReviewConfig:
    """Conservative deterministic quality gate configuration."""

    min_instruction_length: int = 16
    min_output_length: int = 16
    min_text_length: int = 40
    deduplicate: bool = True
    require_output: bool = True
    flag_suspicious_markers: bool = True
    require_allowed_license: bool = True
    human_review_threshold: float = 0.62
    expected_domains: tuple[str, ...] = ()

    def __init__(
        self,
        min_instruction_length: int = 16,
        min_output_length: int = 16,
        min_text_length: int = 40,
        deduplicate: bool = True,
        require_output: bool = True,
        flag_suspicious_markers: bool = True,
        require_allowed_license: bool = True,
        human_review_threshold: float = 0.62,
        expected_domains: Sequence[str] = (),
    ) -> None:
        object.__setattr__(self, "min_instruction_length", min_instruction_length)
        object.__setattr__(self, "min_output_length", min_output_length)
        object.__setattr__(self, "min_text_length", min_text_length)
        object.__setattr__(self, "deduplicate", deduplicate)
        object.__setattr__(self, "require_output", require_output)
        object.__setattr__(self, "flag_suspicious_markers", flag_suspicious_markers)
        object.__setattr__(self, "require_allowed_license", require_allowed_license)
        object.__setattr__(self, "human_review_threshold", human_review_threshold)
        object.__setattr__(self, "expected_domains", tuple(expected_domains))
        validate_review_config(self)


@dataclass(frozen=True)
class DatasetReviewReport:
    """Aggregate deterministic review report for normalized dataset samples."""

    total_samples: int
    accepted_count: int
    rejected_count: int
    needs_human_review_count: int
    decision_counts: dict[str, int]
    average_quality_score: float
    duplicate_count: int
    rejection_reasons_summary: dict[str, int]
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        total_samples: int,
        accepted_count: int,
        rejected_count: int,
        needs_human_review_count: int,
        decision_counts: Mapping[str, int],
        average_quality_score: float,
        duplicate_count: int,
        rejection_reasons_summary: Mapping[str, int],
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "total_samples", total_samples)
        object.__setattr__(self, "accepted_count", accepted_count)
        object.__setattr__(self, "rejected_count", rejected_count)
        object.__setattr__(self, "needs_human_review_count", needs_human_review_count)
        object.__setattr__(self, "decision_counts", dict(decision_counts))
        object.__setattr__(self, "average_quality_score", round(average_quality_score, 3))
        object.__setattr__(self, "duplicate_count", duplicate_count)
        object.__setattr__(self, "rejection_reasons_summary", dict(rejection_reasons_summary))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def to_text(self) -> str:
        """Format the aggregate review report for humans."""
        decision_text = ", ".join(
            f"{decision}={count}" for decision, count in self.decision_counts.items()
        )
        reason_text = ", ".join(
            f"{reason}={count}"
            for reason, count in self.rejection_reasons_summary.items()
        )
        return "\n".join(
            (
                "Dataset quality review report",
                f"Total samples: {self.total_samples}",
                f"Accepted: {self.accepted_count}",
                f"Rejected: {self.rejected_count}",
                f"Needs human review: {self.needs_human_review_count}",
                f"Average quality score: {self.average_quality_score:.2f}",
                f"Duplicates: {self.duplicate_count}",
                f"Decision counts: {decision_text or 'none'}",
                f"Reason summary: {reason_text or 'none'}",
            )
        )


class DatasetQualityReviewer:
    """Deterministic quality gate for normalized dataset samples."""

    def __init__(
        self,
        config: DatasetReviewConfig | None = None,
        license_policy: DatasetLicensePolicy | None = None,
    ) -> None:
        self.config = config or DatasetReviewConfig()
        self.license_policy = license_policy or DatasetLicensePolicy()

    def review_samples(
        self,
        samples: Sequence[DatasetSample],
        manifest: DatasetManifest | None = None,
    ) -> tuple[tuple[DatasetSampleReview, ...], DatasetReviewReport]:
        """Review all samples and return decisions plus an aggregate report."""
        seen_hashes: set[str] = set()
        reviews: list[DatasetSampleReview] = []
        for sample in samples:
            review = self.review_sample(sample, manifest, seen_hashes)
            reviews.append(review)
            if review.metadata.get("content_hash") and review.decision != "rejected_duplicate":
                seen_hashes.add(str(review.metadata["content_hash"]))
        return tuple(reviews), build_review_report(reviews, manifest)

    def review_sample(
        self,
        sample: DatasetSample,
        manifest: DatasetManifest | None = None,
        seen_hashes: set[str] | None = None,
    ) -> DatasetSampleReview:
        """Review one normalized sample using deterministic quality signals."""
        text = normalized_text(sample.content)
        content_hash = sample_content_hash(sample)
        if not text:
            return self.rejected(sample, "rejected_empty", "content is empty", content_hash)
        if sample.sample_type not in SUPPORTED_REVIEW_SAMPLE_TYPES:
            reason = f"unsupported sample type: {sample.sample_type}"
            return self.rejected(sample, "rejected_unsupported", reason, content_hash)
        if self.license_is_rejected(sample, manifest):
            reason = f"license is not allowed for review promotion: {sample.source.license}"
            return self.rejected(sample, "rejected_license", reason, content_hash)
        if self.duplicate_is_rejected(content_hash, seen_hashes):
            return self.rejected(
                sample,
                "rejected_duplicate",
                "duplicate normalized content",
                content_hash,
            )
        return self.scored_review(sample, text, content_hash)

    def scored_review(
        self,
        sample: DatasetSample,
        text: str,
        content_hash: str,
    ) -> DatasetSampleReview:
        """Score a non-empty, non-duplicate, license-compatible sample."""
        reasons: list[str] = []
        penalties: list[float] = []
        self.collect_length_reasons(sample, text, reasons, penalties)
        self.collect_domain_reasons(sample, reasons, penalties)
        if low_information_density(text):
            reasons.append("content has low information density")
            penalties.append(0.25)
        suspicious = suspicious_markers(text) if self.config.flag_suspicious_markers else ()
        if suspicious:
            reasons.append("suspicious marker detected: " + ", ".join(suspicious))
            penalties.append(0.25)
        score = quality_score(sample, text, penalties)
        if any(reason in HARD_REJECTION_REASONS for reason in reasons):
            return self.build_review(
                sample,
                False,
                "rejected_too_short",
                reasons,
                score,
                content_hash,
            )
        if score < self.config.human_review_threshold or suspicious:
            if not reasons:
                reasons.append("quality score is below human review threshold")
            return self.build_review(
                sample,
                False,
                "needs_human_review",
                reasons,
                score,
                content_hash,
            )
        reasons.append("sample passed deterministic review checks")
        return self.build_review(sample, True, "accepted", reasons, score, content_hash)

    def collect_length_reasons(
        self,
        sample: DatasetSample,
        text: str,
        reasons: list[str],
        penalties: list[float],
    ) -> None:
        """Collect deterministic length and answer-shape reasons."""
        if len(text) < self.config.min_text_length:
            reasons.append("content is too short")
            penalties.append(0.45)
        instruction = extract_instruction_text(sample)
        if instruction and len(instruction) < self.config.min_instruction_length:
            reasons.append("instruction is too short")
            penalties.append(0.2)
        output = extract_output_text(sample)
        if self.config.require_output and requires_answer(sample):
            if not output:
                reasons.append("output or assistant answer is missing")
                penalties.append(0.55)
            elif len(output) < self.config.min_output_length:
                reasons.append("output is too short")
                penalties.append(0.35)

    def collect_domain_reasons(
        self,
        sample: DatasetSample,
        reasons: list[str],
        penalties: list[float],
    ) -> None:
        """Collect optional domain mismatch reasons."""
        expected = self.config.expected_domains
        if expected and not domain_matches(sample, expected):
            reasons.append("sample domains do not match expected domains")
            penalties.append(0.25)

    def license_is_rejected(
        self,
        sample: DatasetSample,
        manifest: DatasetManifest | None,
    ) -> bool:
        """Return whether the configured license gate rejects the sample."""
        if not self.config.require_allowed_license:
            return False
        return license_rejected(sample, manifest, self.license_policy)

    def duplicate_is_rejected(
        self,
        content_hash: str,
        seen_hashes: set[str] | None,
    ) -> bool:
        """Return whether duplicate filtering rejects the content hash."""
        return self.config.deduplicate and seen_hashes is not None and content_hash in seen_hashes

    def rejected(
        self,
        sample: DatasetSample,
        decision: str,
        reason: str,
        content_hash: str,
    ) -> DatasetSampleReview:
        """Build a zero-score rejected review."""
        return self.build_review(sample, False, decision, (reason,), 0.0, content_hash)

    def build_review(
        self,
        sample: DatasetSample,
        accepted: bool,
        decision: str,
        reasons: Sequence[str],
        score: float,
        content_hash: str,
    ) -> DatasetSampleReview:
        """Build a review object with shared metadata."""
        return DatasetSampleReview(
            sample_id=sample.id,
            accepted=accepted,
            decision=decision,
            reasons=reasons,
            quality_score=score,
            domains=sample.domains,
            metadata={
                "content_hash": content_hash,
                "sample_type": sample.sample_type,
                "source_id": sample.source.id,
                "source_name": sample.source.name,
                "source_license": sample.source.license,
                **sample.metadata,
            },
        )

    def accepted_samples(
        self,
        samples: Sequence[DatasetSample],
        reviews: Sequence[DatasetSampleReview],
    ) -> tuple[DatasetSample, ...]:
        """Return samples accepted by matching review decisions."""
        accepted_ids = {review.sample_id for review in reviews if review.accepted}
        return tuple(sample for sample in samples if sample.id in accepted_ids)

    def accepted_knowledge_seed_candidates(
        self,
        samples: Sequence[DatasetSample],
        reviews: Sequence[DatasetSampleReview],
    ) -> tuple[KnowledgeSeed, ...]:
        """Convert only accepted reviewed samples into raw KnowledgeSeed candidates."""
        return accepted_reviewed_samples_to_knowledge_seeds(samples, reviews)


def accepted_reviewed_samples_to_knowledge_seeds(
    samples: Sequence[DatasetSample],
    reviews: Sequence[DatasetSampleReview],
) -> tuple[KnowledgeSeed, ...]:
    """Convert accepted reviewed samples into raw KnowledgeSeed candidates."""
    review_by_id = {review.sample_id: review for review in reviews if review.accepted}
    seeds: list[KnowledgeSeed] = []
    for sample in samples:
        review = review_by_id.get(sample.id)
        if review is None:
            continue
        base = knowledge_seed_from_dataset_sample(sample)
        seeds.append(
            KnowledgeSeed(
                id=base.id,
                content=base.content,
                source=base.source,
                domains=base.domains,
                keywords=base.keywords,
                confidence=min(base.confidence, review.quality_score),
                status="new",
                metadata={
                    **base.metadata,
                    "origin": "reviewed_dataset_sample",
                    "dataset_review_decision": review.decision,
                    "dataset_review_score": review.quality_score,
                    "dataset_review_reasons": list(review.reasons),
                    "dataset_review_status": "candidate_raw",
                },
            )
        )
    return tuple(seeds)


def review_ingested_samples(
    samples: Sequence[DatasetSample],
    manifest: DatasetManifest,
    config: DatasetReviewConfig | None = None,
) -> tuple[tuple[DatasetSampleReview, ...], DatasetReviewReport]:
    """Convenience helper for reviewing samples after DatasetIngestor normalization."""
    return DatasetQualityReviewer(config=config).review_samples(samples, manifest)


def build_review_report(
    reviews: Sequence[DatasetSampleReview],
    manifest: DatasetManifest | None = None,
) -> DatasetReviewReport:
    """Build an aggregate report from sample review decisions."""
    decision_counter = Counter(review.decision for review in reviews)
    reason_counter = Counter(reason for review in reviews for reason in review.reasons)
    total = len(reviews)
    average = sum(review.quality_score for review in reviews) / total if total else 0.0
    rejected = sum(1 for review in reviews if not review.accepted)
    return DatasetReviewReport(
        total_samples=total,
        accepted_count=sum(1 for review in reviews if review.accepted),
        rejected_count=rejected,
        needs_human_review_count=decision_counter["needs_human_review"],
        decision_counts={
            decision: decision_counter[decision]
            for decision in DATASET_REVIEW_DECISIONS
            if decision_counter[decision]
        },
        average_quality_score=average,
        duplicate_count=decision_counter["rejected_duplicate"],
        rejection_reasons_summary=dict(reason_counter),
        metadata={"manifest_name": manifest.name} if manifest is not None else {},
    )


def validate_review_config(config: DatasetReviewConfig) -> None:
    """Validate numeric configuration boundaries."""
    if config.min_instruction_length < 1:
        raise ValueError("min_instruction_length must be at least 1")
    if config.min_output_length < 1:
        raise ValueError("min_output_length must be at least 1")
    if config.min_text_length < 1:
        raise ValueError("min_text_length must be at least 1")
    if not 0.0 <= config.human_review_threshold <= 1.0:
        raise ValueError("human_review_threshold must be between 0.0 and 1.0")


def normalized_text(value: str) -> str:
    """Return a stable normalized text value for review checks."""
    return " ".join(value.split())


def sample_content_hash(sample: DatasetSample) -> str:
    """Return a deterministic duplicate key for one sample."""
    text = normalized_text(sample.content).lower()
    return sha256(text.encode("utf-8")).hexdigest()


def quality_score(sample: DatasetSample, text: str, penalties: Sequence[float]) -> float:
    """Compute a simple deterministic quality score without model judging."""
    length_score = min(len(text) / 240, 1.0)
    domain_score = 1.0 if sample.domains else 0.25
    keyword_score = min(len(sample.keywords) / 5, 1.0)
    source_score = sample.source.reliability
    score = (
        length_score * 0.35
        + domain_score * 0.2
        + keyword_score * 0.2
        + source_score * 0.25
        - sum(penalties)
    )
    return max(0.0, min(score, 1.0))


def license_rejected(
    sample: DatasetSample,
    manifest: DatasetManifest | None,
    policy: DatasetLicensePolicy,
) -> bool:
    """Return whether license metadata blocks reviewed candidate use."""
    if manifest is not None:
        return not policy.can_create_knowledge_seed_candidates(manifest)
    normalized = sample.source.license.lower().strip()
    return any(blocked in normalized for blocked in policy.blocked_training_licenses)


def extract_instruction_text(sample: DatasetSample) -> str:
    """Extract instruction text when the normalized sample carries one."""
    instruction = sample.metadata.get("instruction")
    if isinstance(instruction, str):
        return normalized_text(instruction)
    return extract_prefixed_block(sample.content, "Instruction:")


def extract_output_text(sample: DatasetSample) -> str:
    """Extract answer/output text from normalized instruction or conversation samples."""
    output = extract_prefixed_block(sample.content, "Output:")
    if output:
        return output
    return extract_prefixed_block(sample.content, "assistant:")


def extract_prefixed_block(content: str, prefix: str) -> str:
    """Extract the first line value after a stable normalized prefix."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(prefix.lower()):
            return normalized_text(stripped[len(prefix) :])
    return ""


def requires_answer(sample: DatasetSample) -> bool:
    """Return whether the sample shape should include an output or assistant answer."""
    return sample.sample_type in ANSWER_SAMPLE_TYPES


def domain_matches(sample: DatasetSample, expected_domains: Sequence[str]) -> bool:
    """Return whether a sample has at least one expected domain."""
    expected = set(expected_domains)
    return any(domain in expected for domain in sample.domains)


def low_information_density(text: str) -> bool:
    """Detect very repetitive or placeholder-like text."""
    tokens = [token.strip(".,:;!?()[]{}\"").lower() for token in text.split()]
    tokens = [token for token in tokens if token]
    if len(tokens) < 5:
        return True
    unique_ratio = len(set(tokens)) / len(tokens)
    return unique_ratio < 0.35


def suspicious_markers(text: str) -> tuple[str, ...]:
    """Return suspicious prompt or secret markers found in text."""
    lowered = text.lower()
    return tuple(marker for marker in SUSPICIOUS_MARKERS if marker in lowered)
