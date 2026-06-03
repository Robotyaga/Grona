"""Route-scoped context building for Grona demos."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .decision import ModuleMatch, RoutingDecision
from .feedback import Metadata
from .router import normalized_terms

if TYPE_CHECKING:
    from .memory import MemoryModule


@dataclass(frozen=True)
class ContextItem:
    """A small piece of context prepared for a selected module."""

    source: str
    content: str
    relevance: float
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.relevance <= 1.0:
            raise ValueError("relevance must be between 0.0 and 1.0")


class ContextBuilder:
    """Build lightweight route-scoped context for the selected route."""

    def __init__(
        self,
        memory_modules: Sequence[MemoryModule] = (),
        max_context_items: int = 5,
        memory_context_limit: int = 3,
        include_stub_context: bool = True,
    ) -> None:
        if max_context_items < 1:
            raise ValueError("max_context_items must be at least 1")
        if memory_context_limit < 0:
            raise ValueError("memory_context_limit cannot be negative")
        self.memory_modules = tuple(memory_modules)
        self.max_context_items = max_context_items
        self.memory_context_limit = memory_context_limit
        self.include_stub_context = include_stub_context

    def build(
        self,
        decision: RoutingDecision,
        task: str | None = None,
    ) -> tuple[ContextItem, ...]:
        """Build context items for a routing decision and original task text."""
        task_text = task or decision.task
        if not decision.selected_modules:
            return (
                ContextItem(
                    source="demo:fallback",
                    content="No specialized modules were selected for this task.",
                    relevance=0.0,
                    metadata={"task": task_text, "context_kind": "stub"},
                ),
            )

        stub_items = ()
        if self.include_stub_context:
            stub_items = self._build_stub_context(task_text, decision)
        memory_items = self._build_memory_context(task_text, decision)
        return dedupe_context_items((*stub_items, *memory_items))[: self.max_context_items]

    def _build_stub_context(
        self,
        task: str,
        decision: RoutingDecision,
    ) -> tuple[ContextItem, ...]:
        max_score = max(match.score for match in decision.selected_modules) or 1.0
        return tuple(
            self._context_for_match(task, match, max_score)
            for match in decision.selected_modules
        )

    def _build_memory_context(
        self,
        task: str,
        decision: RoutingDecision,
    ) -> tuple[ContextItem, ...]:
        if not self.memory_modules or self.memory_context_limit == 0:
            return ()

        selected_domains = tuple(match.module.domain for match in decision.selected_modules)
        selected_capabilities = tuple(
            capability
            for match in decision.selected_modules
            for capability in match.module.capabilities
        )
        relevant_modules = tuple(
            module
            for module in self.memory_modules
            if is_memory_module_relevant(module, selected_domains, selected_capabilities)
        )

        memory_items: list[ContextItem] = []
        for module in relevant_modules:
            memory_items.extend(
                module.search(
                    task,
                    domains=selected_domains,
                    capabilities=selected_capabilities,
                    limit=self.memory_context_limit,
                )
            )

        memory_items.sort(key=lambda item: (-item.relevance, item.source, item.content))
        return tuple(memory_items[: self.memory_context_limit])

    def _context_for_match(
        self,
        task: str,
        match: ModuleMatch,
        max_score: float,
    ) -> ContextItem:
        module_name = match.module.name
        content = context_stub_for_module(module_name, task)
        return ContextItem(
            source=f"demo:{module_name}",
            content=content,
            relevance=round(match.score / max_score, 4),
            metadata={
                "context_kind": "stub",
                "module": module_name,
                "domain": match.module.domain,
                "capabilities": list(match.module.capabilities),
                "score": match.score,
                "base_score": match.base_score,
            },
        )


def is_memory_module_relevant(
    module: MemoryModule,
    domains: Sequence[str],
    capabilities: Sequence[str],
) -> bool:
    """Return whether a memory module overlaps the selected route."""
    if not module.domains:
        return True
    module_terms = normalized_terms(module.domains)
    route_terms = normalized_terms((*domains, *capabilities))
    return bool(module_terms & route_terms)


def dedupe_context_items(items: Sequence[ContextItem]) -> tuple[ContextItem, ...]:
    """Remove duplicate context items while preserving deterministic order."""
    seen: set[tuple[str, str]] = set()
    deduped: list[ContextItem] = []
    for item in items:
        key = (item.source, item.content)
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return tuple(deduped)


def context_stub_for_module(module_name: str, task: str) -> str:
    """Return deterministic demo context for a selected module."""
    if module_name == "code-assistant":
        return (
            "Code review checklist: inspect control flow, error handling, tests, "
            f"static analysis signals, and debugging clues for: {task}"
        )
    if module_name == "automotive-diagnostics":
        return (
            "Automotive diagnostic stub: check coolant level, thermostat operation, "
            f"radiator flow, fan activation, air pockets, and symptom order for: {task}"
        )
    if module_name == "cybersecurity-scanner":
        return (
            "Cybersecurity checklist: review input validation, secrets handling, "
            f"authentication, permissions, logs, and threat exposure for: {task}"
        )
    if module_name == "media-video-tool":
        return (
            "Media workflow stub: inspect codec needs, color workflow, audio/video "
            f"processing, stabilization, metadata, and export constraints for: {task}"
        )
    if module_name == "document-search":
        return (
            "Document context stub: consider indexing, extraction, search terms, "
            f"source evidence, and summarization needs for: {task}"
        )
    if module_name == "general-reasoning":
        return (
            "General reasoning checklist: clarify goals, decompose ambiguity, "
            f"compare likely paths, and coordinate selected modules for: {task}"
        )
    return f"Prepare route-scoped demo context for {module_name}: {task}"
