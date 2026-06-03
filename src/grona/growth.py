"""Growth Lab primitives for deterministic knowledge seed validation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .documents import DocumentChunk, assign_domains, extract_keywords
from .feedback import Metadata
from .tools import ToolResult

KNOWLEDGE_SOURCE_TYPES = (
    "user_note",
    "document",
    "donor_model",
    "tool_result",
    "feedback",
    "benchmark",
    "unknown",
)
KNOWLEDGE_SEED_STATUSES = ("new", "validated", "weak", "quarantined", "rejected", "promoted")
GENERIC_CONTENT_MARKERS = {
    "good idea",
    "important note",
    "needs review",
    "check later",
    "unknown",
    "todo",
}


@dataclass(frozen=True)
class KnowledgeSource:
    """Raw origin for a knowledge seed before trust or promotion."""

    id: str
    source_type: str
    name: str
    reliability: float = 0.5
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        source_type: str,
        name: str,
        reliability: float = 0.5,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "source_type", source_type)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "reliability", reliability)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("knowledge source id cannot be empty")
        if not name:
            raise ValueError("knowledge source name cannot be empty")
        if source_type not in KNOWLEDGE_SOURCE_TYPES:
            raise ValueError(f"unsupported knowledge source_type: {source_type}")
        if not 0.0 <= reliability <= 1.0:
            raise ValueError("knowledge source reliability must be between 0.0 and 1.0")


@dataclass(frozen=True)
class KnowledgeSeed:
    """Raw knowledge candidate that is not trusted memory yet."""

    id: str
    content: str
    source: KnowledgeSource
    domains: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    confidence: float = 0.5
    status: str = "new"
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        content: str,
        source: KnowledgeSource,
        domains: Sequence[str] = (),
        keywords: Sequence[str] = (),
        confidence: float = 0.5,
        status: str = "new",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "domains", tuple(domains))
        object.__setattr__(self, "keywords", tuple(keywords))
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("knowledge seed id cannot be empty")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("knowledge seed confidence must be between 0.0 and 1.0")
        if status not in KNOWLEDGE_SEED_STATUSES:
            raise ValueError(f"unsupported knowledge seed status: {status}")


@dataclass(frozen=True)
class ValidationResult:
    """Deterministic validation result for one knowledge seed."""

    seed_id: str
    accepted: bool
    status: str
    score: float
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        seed_id: str,
        accepted: bool,
        status: str,
        score: float,
        reasons: Sequence[str] = (),
        warnings: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "seed_id", seed_id)
        object.__setattr__(self, "accepted", accepted)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "score", round(score, 3))
        object.__setattr__(self, "reasons", tuple(reasons))
        object.__setattr__(self, "warnings", tuple(warnings))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not seed_id:
            raise ValueError("validation result seed_id cannot be empty")
        if status not in KNOWLEDGE_SEED_STATUSES:
            raise ValueError(f"unsupported validation status: {status}")
        if not 0.0 <= score <= 1.0:
            raise ValueError("validation score must be between 0.0 and 1.0")

    def to_text(self) -> str:
        """Format the validation result for humans."""
        lines = [
            f"Seed: {self.seed_id}",
            f"Accepted: {self.accepted}",
            f"Status: {self.status}",
            f"Score: {self.score:.2f}",
        ]
        if self.reasons:
            lines.append("Reasons:")
            lines.extend(f"- {reason}" for reason in self.reasons)
        if self.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in self.warnings)
        return "\n".join(lines)


class KnowledgeValidator:
    """Deterministic validator for raw knowledge seeds."""

    def __init__(
        self,
        min_content_chars: int = 40,
        weak_score_threshold: float = 0.7,
        quarantine_score_threshold: float = 0.35,
    ) -> None:
        if min_content_chars < 1:
            raise ValueError("min_content_chars must be at least 1")
        if not 0.0 <= quarantine_score_threshold <= weak_score_threshold <= 1.0:
            raise ValueError("validation thresholds must be ordered between 0.0 and 1.0")
        self.min_content_chars = min_content_chars
        self.weak_score_threshold = weak_score_threshold
        self.quarantine_score_threshold = quarantine_score_threshold

    def validate(self, seed: KnowledgeSeed) -> ValidationResult:
        """Validate one seed without external fact-checking."""
        reasons: list[str] = []
        warnings: list[str] = []
        content = " ".join(seed.content.split())
        if not content:
            return ValidationResult(
                seed.id,
                accepted=False,
                status="rejected",
                score=0.0,
                reasons=("content is empty",),
                metadata=result_metadata(seed),
            )

        score = validation_score(seed, self.min_content_chars)
        if len(content) < self.min_content_chars:
            warnings.append("content is short")
        if seed.source.reliability < 0.5:
            warnings.append("source reliability is low")
        if seed.confidence < 0.4:
            warnings.append("seed confidence is low")
        if not seed.domains:
            warnings.append("domains are missing")
        if not seed.keywords:
            warnings.append("keywords are missing")
        if seed.source.source_type == "unknown":
            warnings.append("source type is unknown")
        if looks_generic(content):
            warnings.append("content looks generic")

        if seed.source.reliability <= 0.05:
            return ValidationResult(
                seed.id,
                accepted=False,
                status="rejected",
                score=score,
                reasons=("source reliability is too low",),
                warnings=warnings,
                metadata=result_metadata(seed),
            )
        if seed.confidence < 0.25:
            return ValidationResult(
                seed.id,
                accepted=False,
                status="quarantined",
                score=score,
                reasons=("seed confidence is too low for promotion",),
                warnings=warnings,
                metadata=result_metadata(seed),
            )
        if score < self.quarantine_score_threshold or "content looks generic" in warnings:
            return ValidationResult(
                seed.id,
                accepted=False,
                status="quarantined",
                score=score,
                reasons=("seed needs review before use",),
                warnings=warnings,
                metadata=result_metadata(seed),
            )
        if score < self.weak_score_threshold or warnings:
            return ValidationResult(
                seed.id,
                accepted=True,
                status="weak",
                score=score,
                reasons=("seed is usable but should be weighted cautiously",),
                warnings=warnings,
                metadata=result_metadata(seed),
            )
        reasons.append("seed passed deterministic validation checks")
        return ValidationResult(
            seed.id,
            accepted=True,
            status="validated",
            score=score,
            reasons=reasons,
            warnings=warnings,
            metadata=result_metadata(seed),
        )


def validation_score(seed: KnowledgeSeed, min_content_chars: int) -> float:
    """Compute a simple deterministic validation score."""
    content = " ".join(seed.content.split())
    length_score = min(len(content) / max(min_content_chars * 2, 1), 1.0)
    domain_score = 1.0 if seed.domains else 0.0
    keyword_score = min(len(seed.keywords) / 4, 1.0)
    score = (
        seed.source.reliability * 0.35
        + seed.confidence * 0.35
        + length_score * 0.15
        + domain_score * 0.075
        + keyword_score * 0.075
    )
    return round(max(0.0, min(score, 1.0)), 3)


def looks_generic(content: str) -> bool:
    """Detect content that is too generic to promote automatically."""
    normalized = " ".join(content.lower().split())
    if normalized in GENERIC_CONTENT_MARKERS:
        return True
    tokens = [token for token in normalized.replace(".", " ").replace(",", " ").split() if token]
    if len(tokens) < 5:
        return True
    counts = Counter(tokens)
    repeated_ratio = max(counts.values()) / len(tokens)
    return repeated_ratio > 0.55


def result_metadata(seed: KnowledgeSeed) -> Metadata:
    """Return metadata shared by validation results."""
    return {
        "source_id": seed.source.id,
        "source_type": seed.source.source_type,
        "source_reliability": seed.source.reliability,
        "seed_confidence": seed.confidence,
        "domain_count": len(seed.domains),
        "keyword_count": len(seed.keywords),
    }


def knowledge_seed_from_document_chunk(
    chunk: DocumentChunk,
    source: KnowledgeSource,
    confidence: float | None = None,
) -> KnowledgeSeed:
    """Convert one existing DocumentChunk into a raw KnowledgeSeed."""
    seed_confidence = source.reliability if confidence is None else confidence
    return KnowledgeSeed(
        id=f"seed:{chunk.id}",
        content=chunk.content,
        source=source,
        domains=chunk.domains,
        keywords=chunk.keywords,
        confidence=seed_confidence,
        metadata={
            "origin": "document_chunk",
            "chunk_id": chunk.id,
            "source_id": chunk.source_id,
            "chunk_index": chunk.index,
            **chunk.metadata,
        },
    )


def knowledge_seed_from_tool_result(
    result: ToolResult,
    source: KnowledgeSource,
    confidence: float | None = None,
) -> KnowledgeSeed:
    """Convert one mock ToolResult into a raw KnowledgeSeed."""
    content = " ".join((result.output, *result.details)).strip()
    domains = tool_result_domains(result)
    keywords = extract_keywords(content)
    seed_confidence = min(source.reliability, 0.75) if confidence is None else confidence
    return KnowledgeSeed(
        id=f"seed:tool:{result.tool_name}",
        content=content,
        source=source,
        domains=domains,
        keywords=keywords,
        confidence=seed_confidence,
        metadata={
            "origin": "tool_result",
            "tool_name": result.tool_name,
            "tool_success": result.success,
            **result.metadata,
        },
    )


def tool_result_domains(result: ToolResult) -> tuple[str, ...]:
    """Infer simple domains from tool metadata and text."""
    domain = result.metadata.get("domain")
    if isinstance(domain, str) and domain:
        return (domain,)
    assigned = assign_domains(" ".join((result.tool_name, result.output, *result.details)))
    return assigned or ("general",)


def create_demo_knowledge_sources() -> tuple[KnowledgeSource, ...]:
    """Create deterministic demo sources for Growth Lab examples and tests."""
    return (
        KnowledgeSource("source:user-notes", "user_note", "User notes", 0.9),
        KnowledgeSource("source:documents", "document", "Demo document chunks", 0.82),
        KnowledgeSource("source:donor", "donor_model", "Unverified donor model output", 0.45),
        KnowledgeSource("source:tools", "tool_result", "Mock tool results", 0.72),
        KnowledgeSource("source:feedback", "feedback", "Feedback observations", 0.65),
        KnowledgeSource("source:unknown", "unknown", "Unknown source", 0.3),
    )


def create_demo_knowledge_seeds() -> tuple[KnowledgeSeed, ...]:
    """Create deterministic demo seeds with mixed validation outcomes."""
    sources = {source.id: source for source in create_demo_knowledge_sources()}
    return (
        KnowledgeSeed(
            id="seed:auto-cooling",
            content=(
                "Engine overheating triage should first check coolant level, radiator flow, "
                "thermostat behavior, fan activation, leaks, and air pockets."
            ),
            source=sources["source:user-notes"],
            domains=("automotive",),
            keywords=("engine", "overheating", "coolant", "radiator"),
            confidence=0.88,
        ),
        KnowledgeSeed(
            id="seed:security-review",
            content=(
                "Security review should inspect authentication boundaries, secret exposure, "
                "permissions, firewall logs, suspicious ports, and unexpected outbound traffic."
            ),
            source=sources["source:documents"],
            domains=("cybersecurity", "code"),
            keywords=("security", "auth", "secrets", "firewall"),
            confidence=0.82,
        ),
        KnowledgeSeed(
            id="seed:code-review",
            content=(
                "Python code review should check tests, lint output, imports, error handling, "
                "public API boundaries, and small readable functions."
            ),
            source=sources["source:documents"],
            domains=("code",),
            keywords=("python", "tests", "lint", "api"),
            confidence=0.78,
        ),
        KnowledgeSeed(
            id="seed:media-workflow",
            content=(
                "MotionCam workflow notes should review codec choice, audio sync, color workflow, "
                "stabilization, export settings, and render constraints."
            ),
            source=sources["source:donor"],
            domains=("media",),
            keywords=("motioncam", "codec", "color", "render"),
            confidence=0.72,
        ),
        KnowledgeSeed(
            id="seed:document-indexing",
            content=(
                "Document indexing should preserve source metadata, chunk boundaries, citations, "
                "retrieval notes, and update behavior before adding vector search."
            ),
            source=sources["source:feedback"],
            domains=("documents",),
            keywords=(),
            confidence=0.7,
        ),
        KnowledgeSeed(
            id="seed:low-confidence",
            content=(
                "Possible benchmark observation: route quality changed, "
                "but evidence is incomplete."
            ),
            source=sources["source:feedback"],
            domains=("general",),
            keywords=("benchmark", "route"),
            confidence=0.18,
        ),
        KnowledgeSeed(
            id="seed:generic",
            content="good idea",
            source=sources["source:unknown"],
            domains=(),
            keywords=(),
            confidence=0.4,
        ),
        KnowledgeSeed(
            id="seed:empty",
            content="",
            source=sources["source:unknown"],
            domains=("general",),
            keywords=("empty",),
            confidence=0.2,
        ),
    )
