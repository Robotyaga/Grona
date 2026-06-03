"""Deterministic KnowledgeSeed deduplication and conflict review helpers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from string import punctuation

from .feedback import Metadata
from .growth import KnowledgeSeed, KnowledgeValidator, ValidationResult

CONFLICT_SEVERITIES = ("none", "low", "medium", "high")
SEED_REVIEW_DECISIONS = (
    "promote_candidate",
    "merge_duplicate",
    "quarantine_conflict",
    "quarantine_weak",
    "reject_broken",
    "needs_review",
)
NEGATION_MARKERS = (
    "does not",
    "do not",
    "did not",
    "cannot",
    "can not",
    "should not",
    "must not",
    "not",
    "never",
    "no ",
)
OPPOSING_TERMS = (
    ("supports", "does not support"),
    ("enabled", "disabled"),
    ("allowed", "blocked"),
    ("true", "false"),
    ("available", "unavailable"),
    ("safe", "unsafe"),
    ("works", "does not work"),
)
_TRANSLATION_TABLE = str.maketrans({mark: " " for mark in punctuation})


@dataclass(frozen=True)
class NormalizedKnowledge:
    """Normalized seed view used for deterministic duplicate and conflict checks."""

    seed_id: str
    normalized_content: str
    normalized_keywords: tuple[str, ...]
    domains: tuple[str, ...]
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        seed_id: str,
        normalized_content: str,
        normalized_keywords: Sequence[str] = (),
        domains: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "seed_id", seed_id)
        object.__setattr__(self, "normalized_content", normalized_content)
        object.__setattr__(self, "normalized_keywords", tuple(normalized_keywords))
        object.__setattr__(self, "domains", tuple(domains))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not seed_id:
            raise ValueError("normalized knowledge seed_id cannot be empty")


@dataclass(frozen=True)
class DuplicateCheckResult:
    """Deterministic duplicate check result for one seed."""

    seed_id: str
    duplicate_of: str | None
    is_duplicate: bool
    score: float
    reasons: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        seed_id: str,
        duplicate_of: str | None,
        is_duplicate: bool,
        score: float,
        reasons: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "seed_id", seed_id)
        object.__setattr__(self, "duplicate_of", duplicate_of)
        object.__setattr__(self, "is_duplicate", is_duplicate)
        object.__setattr__(self, "score", round(score, 3))
        object.__setattr__(self, "reasons", tuple(reasons))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not seed_id:
            raise ValueError("duplicate check seed_id cannot be empty")
        if not 0.0 <= score <= 1.0:
            raise ValueError("duplicate score must be between 0.0 and 1.0")


@dataclass(frozen=True)
class ConflictCheckResult:
    """Potential conflict check result for one seed."""

    seed_id: str
    conflicts_with: tuple[str, ...]
    conflict_detected: bool
    severity: str
    reasons: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        seed_id: str,
        conflicts_with: Sequence[str] = (),
        conflict_detected: bool = False,
        severity: str = "none",
        reasons: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "seed_id", seed_id)
        object.__setattr__(self, "conflicts_with", tuple(conflicts_with))
        object.__setattr__(self, "conflict_detected", conflict_detected)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "reasons", tuple(reasons))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not seed_id:
            raise ValueError("conflict check seed_id cannot be empty")
        if severity not in CONFLICT_SEVERITIES:
            raise ValueError(f"unsupported conflict severity: {severity}")


@dataclass(frozen=True)
class SeedReviewDecision:
    """Recommended next step for a seed before promotion or clustering."""

    seed_id: str
    decision: str
    reasons: tuple[str, ...] = ()
    duplicate_of: str | None = None
    conflicts_with: tuple[str, ...] = ()
    recommended_status: str = "new"
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        seed_id: str,
        decision: str,
        reasons: Sequence[str] = (),
        duplicate_of: str | None = None,
        conflicts_with: Sequence[str] = (),
        recommended_status: str = "new",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "seed_id", seed_id)
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "reasons", tuple(reasons))
        object.__setattr__(self, "duplicate_of", duplicate_of)
        object.__setattr__(self, "conflicts_with", tuple(conflicts_with))
        object.__setattr__(self, "recommended_status", recommended_status)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not seed_id:
            raise ValueError("seed review decision seed_id cannot be empty")
        if decision not in SEED_REVIEW_DECISIONS:
            raise ValueError(f"unsupported seed review decision: {decision}")


class KnowledgeDeduplicator:
    """Deterministic duplicate detector for raw knowledge seeds."""

    def __init__(self, keyword_overlap_threshold: float = 0.8) -> None:
        if not 0.0 <= keyword_overlap_threshold <= 1.0:
            raise ValueError("keyword_overlap_threshold must be between 0.0 and 1.0")
        self.keyword_overlap_threshold = keyword_overlap_threshold

    def normalize(self, seed: KnowledgeSeed) -> NormalizedKnowledge:
        """Normalize one seed without semantic or fuzzy dependencies."""
        return NormalizedKnowledge(
            seed_id=seed.id,
            normalized_content=normalize_text(seed.content),
            normalized_keywords=normalize_keyword_values(seed.keywords),
            domains=normalize_keyword_values(seed.domains),
            metadata={
                "source_id": seed.source.id,
                "source_type": seed.source.source_type,
                "source_reliability": seed.source.reliability,
                "content_length": len(seed.content),
            },
        )

    def find_duplicates(self, seeds: Sequence[KnowledgeSeed]) -> list[DuplicateCheckResult]:
        """Find deterministic duplicate candidates while preserving input order."""
        normalized = {seed.id: self.normalize(seed) for seed in seeds}
        canonical: list[KnowledgeSeed] = []
        results: list[DuplicateCheckResult] = []
        for seed in seeds:
            current = normalized[seed.id]
            duplicate = self._find_first_duplicate(seed, current, canonical, normalized)
            if duplicate is None:
                canonical.append(seed)
                results.append(DuplicateCheckResult(seed.id, None, False, 0.0))
            else:
                duplicate_of, score, reasons, metadata = duplicate
                results.append(
                    DuplicateCheckResult(
                        seed.id,
                        duplicate_of=duplicate_of,
                        is_duplicate=True,
                        score=score,
                        reasons=reasons,
                        metadata=metadata,
                    )
                )
        return results

    def group_duplicates(self, seeds: Sequence[KnowledgeSeed]) -> dict[str, list[str]]:
        """Group duplicate seed ids under their first canonical seed id."""
        groups: dict[str, list[str]] = defaultdict(list)
        for result in self.find_duplicates(seeds):
            if result.is_duplicate and result.duplicate_of is not None:
                groups[result.duplicate_of].append(result.seed_id)
        return dict(groups)

    def _find_first_duplicate(
        self,
        seed: KnowledgeSeed,
        current: NormalizedKnowledge,
        candidates: Sequence[KnowledgeSeed],
        normalized: Mapping[str, NormalizedKnowledge],
    ) -> tuple[str, float, tuple[str, ...], Metadata] | None:
        for candidate in candidates:
            other = normalized[candidate.id]
            score, reasons, metadata = self._duplicate_score(seed, current, candidate, other)
            if score >= 1.0 or reasons:
                return candidate.id, score, reasons, metadata
        return None

    def _duplicate_score(
        self,
        seed: KnowledgeSeed,
        current: NormalizedKnowledge,
        candidate: KnowledgeSeed,
        other: NormalizedKnowledge,
    ) -> tuple[float, tuple[str, ...], Metadata]:
        if current.normalized_content and current.normalized_content == other.normalized_content:
            reasons = ["exact normalized content duplicate"]
            if seed.source.id == candidate.source.id:
                reasons.append("same source and same normalized content")
            return 1.0, tuple(reasons), {"matched_seed_id": candidate.id}

        if has_opposite_polarity(current.normalized_content, other.normalized_content):
            return 0.0, (), {}

        shared_domains = overlap_ratio(current.domains, other.domains)
        keyword_overlap = overlap_ratio(current.normalized_keywords, other.normalized_keywords)
        if shared_domains and keyword_overlap >= self.keyword_overlap_threshold:
            return (
                round(keyword_overlap, 3),
                ("high keyword overlap within the same domain",),
                {"matched_seed_id": candidate.id, "keyword_overlap": keyword_overlap},
            )

        text_overlap = token_overlap_ratio(current.normalized_content, other.normalized_content)
        is_short = short_statement(current.normalized_content, other.normalized_content)
        if is_short and text_overlap >= 0.85:
            return (
                round(text_overlap, 3),
                ("highly similar short statements",),
                {"matched_seed_id": candidate.id, "text_overlap": text_overlap},
            )
        return 0.0, (), {}


class KnowledgeConflictDetector:
    """Conservative deterministic detector for potential seed conflicts."""

    def __init__(self, keyword_overlap_threshold: float = 0.25) -> None:
        if not 0.0 <= keyword_overlap_threshold <= 1.0:
            raise ValueError("keyword_overlap_threshold must be between 0.0 and 1.0")
        self.keyword_overlap_threshold = keyword_overlap_threshold
        self.deduplicator = KnowledgeDeduplicator()

    def find_conflicts(self, seeds: Sequence[KnowledgeSeed]) -> list[ConflictCheckResult]:
        """Detect potential conflicts without claiming factual resolution."""
        normalized = {seed.id: self.deduplicator.normalize(seed) for seed in seeds}
        conflicts: dict[str, list[str]] = defaultdict(list)
        reasons: dict[str, list[str]] = defaultdict(list)
        severities: dict[str, str] = {}
        metadata: dict[str, Metadata] = defaultdict(dict)

        for index, seed in enumerate(seeds):
            for other in seeds[index + 1 :]:
                result = self._pair_conflict(seed, normalized[seed.id], other, normalized[other.id])
                if result is None:
                    continue
                severity, reason, pair_metadata = result
                conflicts[seed.id].append(other.id)
                conflicts[other.id].append(seed.id)
                reasons[seed.id].append(reason)
                reasons[other.id].append(reason)
                severities[seed.id] = max_severity(severities.get(seed.id, "none"), severity)
                severities[other.id] = max_severity(severities.get(other.id, "none"), severity)
                metadata[seed.id].update(pair_metadata)
                metadata[other.id].update(pair_metadata)

        results: list[ConflictCheckResult] = []
        for seed in seeds:
            seed_conflicts = tuple(dict.fromkeys(conflicts.get(seed.id, ())))
            severity = severities.get(seed.id, "none")
            results.append(
                ConflictCheckResult(
                    seed.id,
                    conflicts_with=seed_conflicts,
                    conflict_detected=bool(seed_conflicts),
                    severity=severity,
                    reasons=tuple(dict.fromkeys(reasons.get(seed.id, ()))),
                    metadata=metadata.get(seed.id, {}),
                )
            )
        return results

    def _pair_conflict(
        self,
        seed: KnowledgeSeed,
        current: NormalizedKnowledge,
        other_seed: KnowledgeSeed,
        other: NormalizedKnowledge,
    ) -> tuple[str, str, Metadata] | None:
        if not overlap_ratio(current.domains, other.domains):
            return None
        keyword_overlap = overlap_ratio(current.normalized_keywords, other.normalized_keywords)
        text_overlap = token_overlap_ratio(current.normalized_content, other.normalized_content)
        if keyword_overlap < self.keyword_overlap_threshold and text_overlap < 0.25:
            return None

        current_polarity = statement_polarity(current.normalized_content)
        other_polarity = statement_polarity(other.normalized_content)
        if current_polarity == 0 or other_polarity == 0 or current_polarity == other_polarity:
            return None

        severity = conflict_severity(seed, other_seed, keyword_overlap, text_overlap)
        return (
            severity,
            "potential conflict: opposite polarity in overlapping domain",
            {
                "keyword_overlap": round(keyword_overlap, 3),
                "text_overlap": round(text_overlap, 3),
                "left_polarity": current_polarity,
                "right_polarity": other_polarity,
            },
        )


class KnowledgeReviewPipeline:
    """Combine validation, deduplication, and conflict checks into review decisions."""

    def __init__(
        self,
        validator: KnowledgeValidator | None = None,
        deduplicator: KnowledgeDeduplicator | None = None,
        conflict_detector: KnowledgeConflictDetector | None = None,
    ) -> None:
        self.validator = validator or KnowledgeValidator()
        self.deduplicator = deduplicator or KnowledgeDeduplicator()
        self.conflict_detector = conflict_detector or KnowledgeConflictDetector()

    def review(self, seeds: Sequence[KnowledgeSeed]) -> list[SeedReviewDecision]:
        """Review seeds and recommend next steps without promoting anything."""
        validations = {seed.id: self.validator.validate(seed) for seed in seeds}
        duplicate_results = self.deduplicator.find_duplicates(seeds)
        conflict_results = self.conflict_detector.find_conflicts(seeds)
        duplicates = {result.seed_id: result for result in duplicate_results}
        conflicts = {result.seed_id: result for result in conflict_results}
        decisions: list[SeedReviewDecision] = []
        for seed in seeds:
            decisions.append(
                self._decide(seed, validations[seed.id], duplicates[seed.id], conflicts[seed.id])
            )
        return decisions

    def _decide(
        self,
        seed: KnowledgeSeed,
        validation: ValidationResult,
        duplicate: DuplicateCheckResult,
        conflict: ConflictCheckResult,
    ) -> SeedReviewDecision:
        metadata = {
            "validation_status": validation.status,
            "validation_score": validation.score,
            "duplicate_score": duplicate.score,
            "conflict_severity": conflict.severity,
            "source_id": seed.source.id,
            "source_reliability": seed.source.reliability,
        }
        if validation.status == "rejected":
            return SeedReviewDecision(
                seed.id,
                "reject_broken",
                reasons=validation.reasons or ("validation rejected seed",),
                recommended_status="rejected",
                metadata=metadata,
            )
        if duplicate.is_duplicate:
            return SeedReviewDecision(
                seed.id,
                "merge_duplicate",
                reasons=duplicate.reasons or ("duplicate candidate",),
                duplicate_of=duplicate.duplicate_of,
                recommended_status="quarantined",
                metadata=metadata,
            )
        if conflict.conflict_detected:
            if conflict.severity in {"medium", "high"}:
                decision = "quarantine_conflict"
            else:
                decision = "needs_review"
            return SeedReviewDecision(
                seed.id,
                decision,
                reasons=conflict.reasons or ("potential conflict requires review",),
                conflicts_with=conflict.conflicts_with,
                recommended_status="quarantined",
                metadata=metadata,
            )
        if validation.status in {"weak", "quarantined"}:
            return SeedReviewDecision(
                seed.id,
                "quarantine_weak",
                reasons=validation.reasons or validation.warnings or ("seed is weak",),
                recommended_status="quarantined",
                metadata=metadata,
            )
        return SeedReviewDecision(
            seed.id,
            "promote_candidate",
            reasons=("validated seed has no detected duplicates or conflicts",),
            recommended_status="validated",
            metadata=metadata,
        )


def normalize_text(content: str) -> str:
    """Normalize text for deterministic matching without semantic claims."""
    lowered = content.lower().strip()
    no_punctuation = lowered.translate(_TRANSLATION_TABLE)
    return " ".join(no_punctuation.split())


def normalize_keyword_values(values: Sequence[str]) -> tuple[str, ...]:
    """Normalize keywords or domains while preserving deterministic order."""
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = normalize_text(value)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            normalized.append(cleaned)
    return tuple(normalized)


def overlap_ratio(left: Sequence[str], right: Sequence[str]) -> float:
    """Return intersection over the smaller non-empty set."""
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / min(len(left_set), len(right_set))


def token_overlap_ratio(left: str, right: str) -> float:
    """Return token overlap over the smaller non-empty token set."""
    return overlap_ratio(tuple(left.split()), tuple(right.split()))


def short_statement(left: str, right: str) -> bool:
    """Return whether both normalized statements are short enough for simple overlap checks."""
    return len(left) <= 140 and len(right) <= 140


def statement_polarity(content: str) -> int:
    """Detect a conservative positive or negative polarity marker."""
    negative_phrase = any(negative in content for _, negative in OPPOSING_TERMS)
    positive_phrase = any(positive in content for positive, _ in OPPOSING_TERMS)
    if negative_phrase:
        return -1
    if any(marker in content for marker in NEGATION_MARKERS):
        return -1
    if positive_phrase:
        return 1
    return 0


def has_opposite_polarity(left: str, right: str) -> bool:
    """Return whether two normalized statements have opposite detected polarity."""
    left_polarity = statement_polarity(left)
    right_polarity = statement_polarity(right)
    return bool(left_polarity and right_polarity and left_polarity != right_polarity)


def conflict_severity(
    seed: KnowledgeSeed,
    other: KnowledgeSeed,
    keyword_overlap: float,
    text_overlap: float,
) -> str:
    """Score a potential conflict conservatively from source strength and overlap."""
    weaker_reliability = min(seed.source.reliability, other.source.reliability)
    if weaker_reliability < 0.4:
        return "low"
    if keyword_overlap >= 0.75 or text_overlap >= 0.65:
        return "high"
    return "medium"


def max_severity(left: str, right: str) -> str:
    """Return the higher conflict severity."""
    return left if CONFLICT_SEVERITIES.index(left) >= CONFLICT_SEVERITIES.index(right) else right


def create_demo_review_knowledge_seeds() -> tuple[KnowledgeSeed, ...]:
    """Create deterministic seeds that exercise duplicate and conflict review decisions."""
    from .growth import create_demo_knowledge_sources

    sources = {source.id: source for source in create_demo_knowledge_sources()}
    return (
        KnowledgeSeed(
            id="seed:cooling-clean",
            content=(
                "Engine overheating triage supports checking coolant level, radiator flow, "
                "thermostat behavior, fan activation, leaks, and air pockets."
            ),
            source=sources["source:user-notes"],
            domains=("automotive",),
            keywords=("engine", "overheating", "coolant", "radiator"),
            confidence=0.9,
        ),
        KnowledgeSeed(
            id="seed:cooling-exact-duplicate",
            content=(
                "Engine overheating triage supports checking coolant level, radiator flow, "
                "thermostat behavior, fan activation, leaks, and air pockets."
            ),
            source=sources["source:user-notes"],
            domains=("automotive",),
            keywords=("engine", "overheating", "coolant", "radiator"),
            confidence=0.88,
        ),
        KnowledgeSeed(
            id="seed:cooling-near-duplicate",
            content=(
                "Engine overheating diagnosis should inspect coolant level, radiator flow, "
                "thermostat behavior, fan activation, leaks, and trapped air."
            ),
            source=sources["source:documents"],
            domains=("automotive",),
            keywords=("engine", "overheating", "coolant", "radiator"),
            confidence=0.82,
        ),
        KnowledgeSeed(
            id="seed:cooling-conflict",
            content=(
                "Engine overheating triage does not support checking coolant level, "
                "radiator flow, thermostat behavior, fan activation, leaks, or air pockets."
            ),
            source=sources["source:documents"],
            domains=("automotive",),
            keywords=("engine", "coolant", "policy"),
            confidence=0.78,
        ),
        KnowledgeSeed(
            id="seed:weak-donor",
            content=(
                "Unverified donor note says a media workflow may need codec, color, "
                "audio sync, export, and render review before use."
            ),
            source=sources["source:donor"],
            domains=("media",),
            keywords=("media", "codec", "render"),
            confidence=0.62,
        ),
        KnowledgeSeed(
            id="seed:broken-empty",
            content="",
            source=sources["source:unknown"],
            domains=("general",),
            keywords=("empty",),
            confidence=0.2,
        ),
        KnowledgeSeed(
            id="seed:security-clean",
            content=(
                "Security review supports checking authentication boundaries, secret "
                "exposure, permissions, firewall logs, suspicious ports, and outbound traffic."
            ),
            source=sources["source:documents"],
            domains=("cybersecurity", "code"),
            keywords=("security", "auth", "secrets", "firewall"),
            confidence=0.84,
        ),
    )
