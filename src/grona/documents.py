"""Deterministic in-memory document ingestion stubs for Grona."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from re import finditer

from .feedback import Metadata
from .memory import InMemoryKeywordMemory, MemoryRecord
from .router import tokenize

SOURCE_TYPES = ("text", "markdown", "log", "note", "unknown")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "with",
}
DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "code": (
        "api",
        "bug",
        "class",
        "code",
        "function",
        "lint",
        "package",
        "python",
        "refactor",
        "repository",
        "test",
    ),
    "automotive": (
        "car",
        "coolant",
        "engine",
        "fan",
        "overheat",
        "overheating",
        "radiator",
        "thermostat",
        "vehicle",
    ),
    "cybersecurity": (
        "auth",
        "breach",
        "firewall",
        "logs",
        "malware",
        "permissions",
        "port",
        "scan",
        "secrets",
        "security",
        "threat",
    ),
    "media": (
        "audio",
        "clip",
        "codec",
        "color",
        "export",
        "frames",
        "media",
        "motioncam",
        "render",
        "video",
    ),
    "documents": (
        "archive",
        "citation",
        "document",
        "documents",
        "index",
        "indexing",
        "manual",
        "notes",
        "rag",
        "retrieval",
        "search",
        "summary",
    ),
    "general": (
        "analyze",
        "compare",
        "constraints",
        "explain",
        "plan",
        "reasoning",
        "task",
        "triage",
    ),
}
DOCUMENT_COMPAT_DOMAINS = ("documents", "document", "search", "retrieval")


@dataclass(frozen=True)
class DocumentSource:
    """In-memory raw document content for deterministic ingestion."""

    id: str
    title: str
    content: str
    source_type: str = "unknown"
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        title: str,
        content: str,
        source_type: str = "unknown",
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "source_type", source_type)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("document source id cannot be empty")
        if not title:
            raise ValueError("document source title cannot be empty")
        if source_type not in SOURCE_TYPES:
            raise ValueError(f"unsupported document source_type: {source_type}")


@dataclass(frozen=True)
class DocumentChunk:
    """Small deterministic chunk derived from a DocumentSource."""

    id: str
    source_id: str
    content: str
    index: int
    keywords: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        source_id: str,
        content: str,
        index: int,
        keywords: Sequence[str] = (),
        domains: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "index", index)
        object.__setattr__(self, "keywords", tuple(keywords))
        object.__setattr__(self, "domains", tuple(domains))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("document chunk id cannot be empty")
        if not source_id:
            raise ValueError("document chunk source_id cannot be empty")
        if index < 0:
            raise ValueError("document chunk index cannot be negative")
        if not content:
            raise ValueError("document chunk content cannot be empty")


class TextChunker:
    """Simple deterministic character chunker with practical word-boundary handling."""

    def __init__(self, max_chars: int = 500, overlap_chars: int = 50) -> None:
        if max_chars < 1:
            raise ValueError("max_chars must be at least 1")
        if overlap_chars < 0:
            raise ValueError("overlap_chars cannot be negative")
        if overlap_chars >= max_chars:
            raise ValueError("overlap_chars must be smaller than max_chars")
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk(self, source: DocumentSource) -> tuple[DocumentChunk, ...]:
        """Chunk one in-memory document source."""
        text = normalize_document_text(source.content)
        if not text:
            return ()

        chunks: list[DocumentChunk] = []
        start = 0
        index = 0
        while start < len(text):
            previous_start = start
            end = min(start + self.max_chars, len(text))
            if end < len(text):
                boundary = last_word_boundary(text, start, end)
                if boundary > start:
                    end = boundary
            content = text[start:end].strip()
            if content:
                chunks.append(
                    DocumentChunk(
                        id=f"{source.id}:chunk-{index:04d}",
                        source_id=source.id,
                        content=content,
                        index=index,
                        keywords=extract_keywords(content),
                        domains=assign_domains(content),
                        metadata={
                            "source_title": source.title,
                            "source_type": source.source_type,
                            **source.metadata,
                        },
                    )
                )
                index += 1
            if end >= len(text):
                break
            start = max(0, end - self.overlap_chars)
            if start <= previous_start:
                start = end
        return tuple(chunks)


class DocumentIngestor:
    """Convert in-memory document sources into chunks and memory records."""

    def __init__(self, chunker: TextChunker | None = None) -> None:
        self.chunker = chunker or TextChunker()

    def ingest(self, source: DocumentSource) -> list[DocumentChunk]:
        """Chunk one source and attach deterministic keywords and domains."""
        return list(self.chunker.chunk(source))

    def chunks_to_memory_records(
        self,
        chunks: Sequence[DocumentChunk],
    ) -> list[MemoryRecord]:
        """Convert document chunks into memory records."""
        return [memory_record_from_chunk(chunk) for chunk in chunks]

    def build_memory_module(
        self,
        name: str,
        sources: Sequence[DocumentSource],
    ) -> InMemoryKeywordMemory:
        """Build an in-memory keyword memory module from document sources."""
        chunks = [chunk for source in sources for chunk in self.ingest(source)]
        records = self.chunks_to_memory_records(chunks)
        return InMemoryKeywordMemory(
            records,
            name=name,
            description="Deterministic memory built from in-memory document ingestion.",
        )


def normalize_document_text(text: str) -> str:
    """Normalize whitespace without changing document wording."""
    return " ".join(text.split())


def last_word_boundary(text: str, start: int, end: int) -> int:
    """Return the last whitespace boundary in a chunk window, if one exists."""
    for position in range(end, start, -1):
        if text[position - 1].isspace():
            return position
    return end


def extract_keywords(text: str, limit: int = 12) -> tuple[str, ...]:
    """Extract basic deterministic keywords from text."""
    terms = [term for term in token_sequence(text) if term not in STOPWORDS and len(term) > 2]
    counts = Counter(terms)
    ranked = sorted(counts, key=lambda term: (-counts[term], term))
    return tuple(ranked[:limit])


def token_sequence(text: str) -> tuple[str, ...]:
    """Return lowercase alphanumeric terms in input order."""
    return tuple(match.group(0) for match in finditer(r"[a-z0-9]+", text.lower()))


def assign_domains(text: str) -> tuple[str, ...]:
    """Assign simple Grona-aligned domains with deterministic keyword rules."""
    terms = tokenize(text)
    matched: list[str] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if terms & set(keywords):
            if domain == "documents":
                matched.extend(DOCUMENT_COMPAT_DOMAINS)
            else:
                matched.append(domain)
    if not matched:
        matched.append("general")
    return tuple(dict.fromkeys(matched))


def memory_record_from_chunk(chunk: DocumentChunk) -> MemoryRecord:
    """Convert one document chunk into a memory record."""
    return MemoryRecord(
        id=chunk.id,
        content=chunk.content,
        domains=chunk.domains,
        keywords=chunk.keywords,
        source="document_ingestion",
        metadata={
            "context_kind": "memory",
            "memory_origin": "document_ingestion",
            "chunk_id": chunk.id,
            "source_id": chunk.source_id,
            "chunk_index": chunk.index,
            **chunk.metadata,
        },
    )


def create_demo_document_sources() -> tuple[DocumentSource, ...]:
    """Create small in-memory demo documents for ingestion examples and tests."""
    return (
        DocumentSource(
            id="demo-car-overheating",
            title="Car overheating notes",
            source_type="note",
            content=(
                "Engine overheating notes: check coolant level, radiator flow, "
                "thermostat behavior, fan activation, leaks, and air pockets before "
                "assuming a major engine failure."
            ),
            metadata={"demo_domain": "automotive"},
        ),
        DocumentSource(
            id="demo-python-review",
            title="Python project review notes",
            source_type="markdown",
            content=(
                "Python project review checklist: inspect package structure, tests, "
                "lint output, error handling, imports, public API boundaries, and "
                "small readable functions."
            ),
            metadata={"demo_domain": "code"},
        ),
        DocumentSource(
            id="demo-security-checklist",
            title="Cybersecurity checklist",
            source_type="note",
            content=(
                "Security checklist: review secrets, authentication, permissions, "
                "firewall exposure, suspicious logs, port scan indicators, and "
                "unexpected outbound traffic."
            ),
            metadata={"demo_domain": "cybersecurity"},
        ),
        DocumentSource(
            id="demo-motioncam-workflow",
            title="MotionCam media workflow notes",
            source_type="note",
            content=(
                "MotionCam media workflow notes: inspect video codec, audio sync, "
                "color workflow, stabilization, metadata, export settings, and render "
                "constraints before delivery."
            ),
            metadata={"demo_domain": "media"},
        ),
        DocumentSource(
            id="demo-document-indexing",
            title="Document indexing notes",
            source_type="markdown",
            content=(
                "Document indexing notes: split long documents into chunks, preserve "
                "source metadata, extract keywords, record citations, and keep retrieval "
                "deterministic before adding embeddings or vector search."
            ),
            metadata={"demo_domain": "documents"},
        ),
    )
