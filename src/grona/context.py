"""Route-scoped context building for Grona demos."""

from __future__ import annotations

from dataclasses import dataclass, field

from .decision import ModuleMatch, RoutingDecision
from .feedback import Metadata


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
    """Build lightweight synthetic context for the selected route."""

    def build(self, decision: RoutingDecision) -> tuple[ContextItem, ...]:
        """Build context items for a routing decision."""
        if not decision.selected_modules:
            return (
                ContextItem(
                    source="demo:fallback",
                    content="No specialized modules were selected for this task.",
                    relevance=0.0,
                    metadata={"task": decision.task},
                ),
            )

        max_score = max(match.score for match in decision.selected_modules) or 1.0
        return tuple(
            self._context_for_match(decision.task, match, max_score)
            for match in decision.selected_modules
        )

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
                "module": module_name,
                "domain": match.module.domain,
                "score": match.score,
                "base_score": match.base_score,
            },
        )


def context_stub_for_module(module_name: str, task: str) -> str:
    """Return deterministic demo context for a selected module."""
    if module_name == "code-assistant":
        return f"Focus on code structure, tests, errors, and refactoring signals in: {task}"
    if module_name == "automotive-diagnostics":
        return f"Consider symptoms, operating conditions, safety checks, and inspection order for: {task}"
    if module_name == "cybersecurity-scanner":
        return f"Look for threat indicators, suspicious network behavior, logs, and risk evidence in: {task}"
    if module_name == "media-video-tool":
        return f"Prepare media workflow details such as clips, audio, frames, metadata, and rendering for: {task}"
    if module_name == "document-search":
        return f"Search for documents, manuals, notes, reports, and source evidence related to: {task}"
    if module_name == "general-reasoning":
        return f"Break down the task, identify ambiguity, and coordinate selected modules for: {task}"
    return f"Prepare route-scoped demo context for {module_name}: {task}"
