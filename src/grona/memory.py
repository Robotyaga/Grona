"""Lightweight memory records and deterministic keyword retrieval."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from json import dumps, loads
from pathlib import Path
from typing import Any, Protocol

from .context import ContextItem
from .feedback import Metadata
from .router import normalized_terms, tokenize


@dataclass(frozen=True)
class MemoryRecord:
    """A small stored knowledge item for route-scoped context building."""

    id: str
    content: str
    domains: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    source: str = "memory"
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "domains", tuple(self.domains))
        object.__setattr__(self, "keywords", tuple(self.keywords))
        if not self.id:
            raise ValueError("memory record id cannot be empty")
        if not self.content:
            raise ValueError("memory record content cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the record to JSON-compatible data."""
        return {
            "id": self.id,
            "content": self.content,
            "domains": list(self.domains),
            "keywords": list(self.keywords),
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryRecord:
        """Deserialize a memory record from JSON-compatible data."""
        return cls(
            id=str(data["id"]),
            content=str(data["content"]),
            domains=tuple(data.get("domains", ())),
            keywords=tuple(data.get("keywords", ())),
            source=str(data.get("source", "memory")),
            metadata=dict(data.get("metadata") or {}),
        )


class MemoryModule(Protocol):
    """Minimal interface for route-scoped memory modules."""

    name: str
    description: str
    domains: tuple[str, ...]

    def search(
        self,
        task: str,
        domains: Sequence[str],
        capabilities: Sequence[str],
        limit: int,
    ) -> tuple[ContextItem, ...]:
        """Return context items relevant to a routed task."""


class InMemoryKeywordMemory:
    """Deterministic keyword/domain memory over in-memory records."""

    def __init__(
        self,
        records: Iterable[MemoryRecord],
        name: str = "demo-memory",
        description: str = "Deterministic in-memory keyword retrieval.",
        domains: Sequence[str] = (),
    ) -> None:
        self.records = tuple(records)
        self.name = name
        self.description = description
        self.domains = tuple(domains) or tuple(
            sorted({domain for record in self.records for domain in record.domains})
        )

    def search(
        self,
        task: str,
        domains: Sequence[str],
        capabilities: Sequence[str],
        limit: int,
    ) -> tuple[ContextItem, ...]:
        """Search records by deterministic keyword, domain, and capability overlap."""
        if limit < 1:
            return ()

        task_terms = tokenize(task)
        domain_terms = normalized_terms(domains)
        capability_terms = normalized_terms(capabilities)
        scored: list[tuple[float, MemoryRecord, tuple[str, ...]]] = []

        for record in self.records:
            score, reasons = self._score_record(record, task_terms, domain_terms, capability_terms)
            if score > 0:
                scored.append((score, record, reasons))

        scored.sort(key=lambda item: (-item[0], item[1].source, item[1].id))
        max_score = scored[0][0] if scored else 1.0
        return tuple(
            context_item_from_record(record, self.name, round(score / max_score, 4), reasons)
            for score, record, reasons in scored[:limit]
        )

    def _score_record(
        self,
        record: MemoryRecord,
        task_terms: set[str],
        domain_terms: set[str],
        capability_terms: set[str],
    ) -> tuple[float, tuple[str, ...]]:
        record_domain_terms = normalized_terms(record.domains)
        record_keyword_terms = normalized_terms(record.keywords)
        record_content_terms = tokenize(record.content)
        searchable_terms = record_keyword_terms | record_content_terms

        reasons: list[str] = []
        score = 0.0

        domain_hits = sorted(record_domain_terms & domain_terms)
        if domain_hits:
            score += 2.0 * len(domain_hits)
            reasons.append("domain match: " + ", ".join(domain_hits))

        keyword_hits = sorted(record_keyword_terms & task_terms)
        if keyword_hits:
            score += 1.5 * len(keyword_hits)
            reasons.append("keyword match: " + ", ".join(keyword_hits))

        content_hits = sorted((record_content_terms & task_terms) - record_keyword_terms)
        if content_hits:
            score += 0.5 * len(content_hits)
            reasons.append("content match: " + ", ".join(content_hits[:5]))

        capability_hits = sorted(searchable_terms & capability_terms)
        if capability_hits:
            score += 1.0 * len(capability_hits)
            reasons.append("capability match: " + ", ".join(capability_hits))

        return score, tuple(reasons)


def context_item_from_record(
    record: MemoryRecord,
    memory_module_name: str,
    relevance: float,
    reasons: tuple[str, ...],
) -> ContextItem:
    """Convert a memory record into a context item."""
    return ContextItem(
        source=f"memory:{memory_module_name}:{record.source}:{record.id}",
        content=record.content,
        relevance=relevance,
        metadata={
            "context_kind": "memory",
            "memory_module": memory_module_name,
            "record_id": record.id,
            "record_source": record.source,
            "domains": list(record.domains),
            "keywords": list(record.keywords),
            "reasons": list(reasons),
            **record.metadata,
        },
    )


class JsonlMemoryStore:
    """Tiny JSONL store for memory records."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, records: Iterable[MemoryRecord]) -> None:
        """Replace the JSONL file with the provided memory records."""
        if self.path.parent != Path(""):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        rows = [dumps(record.to_dict(), sort_keys=True) for record in records]
        self.path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")

    def load(self) -> tuple[MemoryRecord, ...]:
        """Load memory records from JSONL."""
        if not self.path.exists():
            return ()
        records: list[MemoryRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                records.append(MemoryRecord.from_dict(loads(stripped)))
        return tuple(records)

    def to_memory_module(
        self,
        name: str = "jsonl-memory",
        description: str = "JSONL-backed keyword memory.",
    ) -> InMemoryKeywordMemory:
        """Load records into an in-memory keyword memory module."""
        return InMemoryKeywordMemory(self.load(), name=name, description=description)


def create_default_memory_modules() -> tuple[MemoryModule, ...]:
    """Create small demo memory modules for Grona examples and tests."""
    records = (
        MemoryRecord(
            id="auto-overheating-checklist",
            content=(
                "Check coolant level, thermostat operation, radiator flow, "
                "fan activation, and air pockets."
            ),
            domains=("automotive", "car", "engine"),
            keywords=("overheating", "coolant", "thermostat", "radiator", "fan"),
            source="automotive_knowledge_stub",
        ),
        MemoryRecord(
            id="auto-diagnostic-order",
            content=(
                "Start with visible leaks and coolant level, then inspect fan "
                "operation, thermostat behavior, and circulation."
            ),
            domains=("automotive", "vehicle", "maintenance"),
            keywords=("diagnostic", "inspection", "coolant", "engine", "maintenance"),
            source="automotive_knowledge_stub",
        ),
        MemoryRecord(
            id="security-input-validation",
            content=(
                "Review input validation, authentication boundaries, permission "
                "checks, secrets handling, and network exposure."
            ),
            domains=("cybersecurity", "security", "network"),
            keywords=("validation", "authentication", "permissions", "secrets", "exposure"),
            source="security_knowledge_stub",
        ),
        MemoryRecord(
            id="security-log-review",
            content=(
                "For suspicious logs, compare ports, repeated source addresses, "
                "failed authentication, and unexpected outbound traffic."
            ),
            domains=("cybersecurity", "security", "network"),
            keywords=("logs", "ports", "scan", "authentication", "traffic"),
            source="security_knowledge_stub",
        ),
        MemoryRecord(
            id="code-quality-checklist",
            content=(
                "Check package structure, tests, linting, error handling, "
                "type boundaries, and small cohesive functions."
            ),
            domains=("code", "software", "programming"),
            keywords=("tests", "linting", "errors", "package", "function"),
            source="code_knowledge_stub",
        ),
        MemoryRecord(
            id="media-workflow-notes",
            content=(
                "For media tasks, inspect codec compression, color grading, "
                "audio EQ, stabilization, metadata, and export settings."
            ),
            domains=("media", "video", "audio"),
            keywords=("codec", "compression", "color", "audio", "stabilization"),
            source="media_knowledge_stub",
        ),
        MemoryRecord(
            id="document-retrieval-notes",
            content=(
                "For document tasks, identify indexing fields, extraction "
                "boundaries, query terms, citations, and summary scope."
            ),
            domains=("document", "search", "retrieval"),
            keywords=("document", "indexing", "extraction", "summary", "retrieval"),
            source="document_knowledge_stub",
        ),
        MemoryRecord(
            id="general-planning-checklist",
            content=(
                "Clarify the goal, list constraints, split the task into checks, "
                "compare paths, and keep the trace explainable."
            ),
            domains=("general", "reasoning", "planning"),
            keywords=("plan", "checklist", "constraints", "compare", "explain"),
            source="general_knowledge_stub",
        ),
    )
    return (
        InMemoryKeywordMemory(
            records,
            name="demo-memory",
            description="Small deterministic demo memory for route-scoped context.",
        ),
    )
