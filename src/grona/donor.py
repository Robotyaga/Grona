"""Donor model proposal adapters for local-first Growth Lab experiments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps, loads
from typing import Protocol
from urllib import error, request

from .documents import assign_domains, extract_keywords
from .feedback import Metadata
from .growth import KnowledgeSeed, KnowledgeSource

DONOR_PROPOSAL_TYPES = (
    "route_hint",
    "summary",
    "knowledge_seed",
    "benchmark_answer",
    "module_suggestion",
    "context_hint",
)


@dataclass(frozen=True)
class DonorModelProposal:
    """Untrusted proposal returned by a donor model adapter."""

    task: str
    source: str
    proposal_type: str
    content: str
    confidence: float | None = None
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        task: str,
        source: str,
        proposal_type: str,
        content: str,
        confidence: float | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "task", task)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "proposal_type", proposal_type)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not task:
            raise ValueError("donor proposal task cannot be empty")
        if not source:
            raise ValueError("donor proposal source cannot be empty")
        if proposal_type not in DONOR_PROPOSAL_TYPES:
            raise ValueError(f"unsupported donor proposal_type: {proposal_type}")
        if not content:
            raise ValueError("donor proposal content cannot be empty")
        if confidence is not None and not 0.0 <= confidence <= 1.0:
            raise ValueError("donor proposal confidence must be between 0.0 and 1.0")

    def to_text(self) -> str:
        """Format the proposal for deterministic demo output."""
        confidence = "unknown" if self.confidence is None else f"{self.confidence:.2f}"
        return "\n".join(
            (
                f"Proposal type: {self.proposal_type}",
                f"Source: {self.source}",
                f"Confidence: {confidence}",
                f"Content: {self.content}",
            )
        )


class DonorModelAdapter(Protocol):
    """Minimal protocol for donor models that provide untrusted proposals."""

    name: str

    def propose(self, task: str, proposal_type: str = "summary") -> DonorModelProposal:
        """Return one untrusted proposal for a task."""


class DonorModelError(RuntimeError):
    """Raised when an optional donor adapter cannot produce a proposal."""


class StaticDonorModelAdapter:
    """Deterministic offline donor adapter for examples and tests."""

    def __init__(self, name: str = "static-donor", confidence: float = 0.7) -> None:
        if not name:
            raise ValueError("static donor name cannot be empty")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("static donor confidence must be between 0.0 and 1.0")
        self.name = name
        self.confidence = confidence

    def propose(self, task: str, proposal_type: str = "summary") -> DonorModelProposal:
        """Return a deterministic proposal without network access."""
        validate_proposal_type(proposal_type)
        content = static_proposal_content(task, proposal_type)
        return DonorModelProposal(
            task=task,
            source=self.name,
            proposal_type=proposal_type,
            content=content,
            confidence=self.confidence,
            metadata={"adapter": "static", "network_used": False},
        )


class LMStudioAdapter:
    """Optional LM Studio compatible adapter using only the Python standard library."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234",
        model: str | None = None,
        timeout: float = 10.0,
        name: str = "lmstudio-local",
    ) -> None:
        if not base_url:
            raise ValueError("LM Studio base_url cannot be empty")
        if timeout <= 0:
            raise ValueError("LM Studio timeout must be positive")
        if not name:
            raise ValueError("LM Studio adapter name cannot be empty")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.name = name

    def propose(self, task: str, proposal_type: str = "summary") -> DonorModelProposal:
        """Request one proposal from an explicitly configured local LM Studio server."""
        validate_proposal_type(proposal_type)
        if not self.model:
            raise DonorModelError("LM Studio model is not configured")
        payload = {
            "model": self.model,
            "temperature": 0.0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a donor model for Grona. Return a concise proposal only. "
                        "Your output is untrusted and will be validated later."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Task: {task}\nProposal type: {proposal_type}",
                },
            ],
        }
        request_data = dumps(payload).encode("utf-8")
        http_request = request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                data = loads(response.read().decode("utf-8"))
        except (OSError, TimeoutError, error.URLError) as exc:
            raise DonorModelError(f"LM Studio request failed: {exc}") from exc
        content = parse_lmstudio_content(data)
        return DonorModelProposal(
            task=task,
            source=self.name,
            proposal_type=proposal_type,
            content=content,
            confidence=None,
            metadata={
                "adapter": "lmstudio",
                "base_url": self.base_url,
                "model": self.model,
                "network_used": True,
            },
        )


@dataclass(frozen=True)
class DonorProposalError:
    """Visible error from one donor adapter proposal request."""

    adapter: str
    proposal_type: str
    message: str


@dataclass(frozen=True)
class DonorProposalBatch:
    """Collected donor proposals plus explicit adapter errors."""

    task: str
    proposals: tuple[DonorModelProposal, ...]
    errors: tuple[DonorProposalError, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def to_text(self) -> str:
        """Format a proposal batch for demos."""
        lines = [
            f"Task: {self.task}",
            f"Proposals: {len(self.proposals)}",
            f"Errors: {len(self.errors)}",
        ]
        if self.proposals:
            lines.append("Proposal details:")
            for proposal in self.proposals:
                lines.append(f"- {proposal.proposal_type} from {proposal.source}")
                lines.append(f"  {proposal.content}")
        if self.errors:
            lines.append("Errors:")
            for item in self.errors:
                lines.append(f"- {item.adapter}/{item.proposal_type}: {item.message}")
        return "\n".join(lines)


class DonorProposalCollector:
    """Collect proposals from one or more donor adapters."""

    def __init__(self, adapters: Sequence[DonorModelAdapter]) -> None:
        self.adapters = tuple(adapters)

    def collect(
        self,
        task: str,
        proposal_types: Sequence[str] = ("summary",),
    ) -> DonorProposalBatch:
        """Collect successful proposals and keep adapter errors visible."""
        proposals: list[DonorModelProposal] = []
        errors: list[DonorProposalError] = []
        for proposal_type in proposal_types:
            validate_proposal_type(proposal_type)
        for adapter in self.adapters:
            for proposal_type in proposal_types:
                try:
                    proposals.append(adapter.propose(task, proposal_type))
                except Exception as exc:  # noqa: BLE001
                    errors.append(DonorProposalError(adapter.name, proposal_type, str(exc)))
        return DonorProposalBatch(
            task=task,
            proposals=tuple(proposals),
            errors=tuple(errors),
            metadata={"adapter_count": len(self.adapters), "proposal_types": list(proposal_types)},
        )


def knowledge_seed_from_donor_proposal(
    proposal: DonorModelProposal,
    reliability: float = 0.45,
) -> KnowledgeSeed:
    """Convert a donor knowledge proposal into an untrusted KnowledgeSeed candidate."""
    if proposal.proposal_type != "knowledge_seed":
        raise ValueError("only knowledge_seed donor proposals can become KnowledgeSeed candidates")
    source = KnowledgeSource(
        id=f"source:donor:{slug(proposal.source)}",
        source_type="donor_model",
        name=f"Donor model proposal: {proposal.source}",
        reliability=reliability,
        metadata={
            "origin": "donor_model_proposal",
            "proposal_source": proposal.source,
            "proposal_type": proposal.proposal_type,
        },
    )
    return KnowledgeSeed(
        id=f"seed:donor:{slug(proposal.source)}:{slug(proposal.task)[:48]}",
        content=proposal.content,
        source=source,
        domains=assign_domains(proposal.content) or ("general",),
        keywords=extract_keywords(proposal.content),
        confidence=proposal.confidence if proposal.confidence is not None else reliability,
        metadata={
            "origin": "donor_model_proposal",
            "proposal_task": proposal.task,
            "proposal_source": proposal.source,
            "proposal_type": proposal.proposal_type,
            **proposal.metadata,
        },
    )


def static_proposal_content(task: str, proposal_type: str) -> str:
    """Create deterministic offline proposal text."""
    normalized_task = " ".join(task.split()) or "unspecified task"
    if proposal_type == "route_hint":
        return f"Route hint for '{normalized_task}': inspect visible task terms before routing."
    if proposal_type == "summary":
        return f"Summary proposal for '{normalized_task}': keep context scoped and explainable."
    if proposal_type == "knowledge_seed":
        return (
            f"Donor proposal for '{normalized_task}' should be treated as an untrusted "
            "knowledge seed candidate with provenance, validation, review, and benchmarks."
        )
    if proposal_type == "benchmark_answer":
        return f"Benchmark answer proposal for '{normalized_task}': compare against expected traces."
    if proposal_type == "module_suggestion":
        return f"Module suggestion for '{normalized_task}': consider only matching domain modules."
    if proposal_type == "context_hint":
        return f"Context hint for '{normalized_task}': gather small source-aware context only."
    raise ValueError(f"unsupported donor proposal_type: {proposal_type}")


def parse_lmstudio_content(data: Mapping[str, object]) -> str:
    """Extract assistant content from an OpenAI-compatible chat completion payload."""
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise DonorModelError("LM Studio response did not include choices")
    first = choices[0]
    if not isinstance(first, Mapping):
        raise DonorModelError("LM Studio response choice is invalid")
    message = first.get("message")
    if not isinstance(message, Mapping):
        raise DonorModelError("LM Studio response did not include a message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise DonorModelError("LM Studio response content is empty")
    return content.strip()


def validate_proposal_type(proposal_type: str) -> None:
    """Validate a donor proposal type."""
    if proposal_type not in DONOR_PROPOSAL_TYPES:
        raise ValueError(f"unsupported donor proposal_type: {proposal_type}")


def slug(value: str) -> str:
    """Create a deterministic id-safe slug."""
    cleaned = "".join(character if character.isalnum() else "-" for character in value.lower())
    return "-".join(part for part in cleaned.split("-") if part) or "unknown"
