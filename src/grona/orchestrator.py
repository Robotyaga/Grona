"""Simple orchestration over routed modules and built context."""

from __future__ import annotations

from dataclasses import dataclass, field

from .context import ContextBuilder, ContextItem
from .decision import RoutingDecision
from .feedback import Metadata
from .router import Router


@dataclass(frozen=True)
class OrchestrationResult:
    """The visible result of routing and context preparation."""

    task: str
    routing_decision: RoutingDecision
    context_items: tuple[ContextItem, ...]
    selected_modules: tuple[str, ...]
    summary: str
    metadata: Metadata = field(default_factory=dict)

    @property
    def context_sources(self) -> tuple[str, ...]:
        """Return context source names in build order."""
        return tuple(item.source for item in self.context_items)

    def to_text(self) -> str:
        """Format the orchestration result without claiming expert execution."""
        selected = ", ".join(self.selected_modules) or "none"
        lines = [
            f"Task: {self.task}",
            f"Selected modules: {selected}",
            "Context items:",
        ]
        if self.context_items:
            for item in self.context_items:
                kind = item.metadata.get("context_kind", "context")
                lines.append(f"- {item.source} ({kind}, relevance {item.relevance:.2f})")
                lines.append(f"  content: {item.content}")
        else:
            lines.append("- none")
        lines.append(f"Orchestration summary: {self.summary}")
        return "\n".join(lines)


class Orchestrator:
    """Coordinate routing and context building for a selected path."""

    def __init__(
        self,
        router: Router,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self.router = router
        self.context_builder = context_builder or ContextBuilder()

    def run(self, task: str) -> OrchestrationResult:
        """Route a task, build context, and return a planned handoff result."""
        decision = self.router.route(task)
        context_items = self.context_builder.build(decision, task)
        selected_modules = decision.selected_names
        source_counts = count_context_sources(context_items)
        return OrchestrationResult(
            task=task,
            routing_decision=decision,
            context_items=context_items,
            selected_modules=selected_modules,
            summary=summarize_orchestration(decision, context_items, source_counts),
            metadata={
                "context_count": len(context_items),
                "selected_count": len(selected_modules),
                "execution": "not_run",
                "source_counts": source_counts,
            },
        )


def count_context_sources(context_items: tuple[ContextItem, ...]) -> dict[str, int]:
    """Count context items by source kind."""
    counts: dict[str, int] = {"stub": 0, "memory": 0}
    for item in context_items:
        source_kind = "memory" if item.source.startswith("memory:") else "stub"
        counts[source_kind] = counts.get(source_kind, 0) + 1
    return counts


def summarize_orchestration(
    decision: RoutingDecision,
    context_items: tuple[ContextItem, ...],
    source_counts: dict[str, int] | None = None,
) -> str:
    """Create a compact orchestration summary."""
    selected = ", ".join(decision.selected_names) or "no specialized modules"
    counts = source_counts or count_context_sources(context_items)
    return (
        f"Grona selected {selected}, prepared {len(context_items)} context items "
        f"({counts.get('stub', 0)} stub, {counts.get('memory', 0)} memory), "
        "and would pass this focused context to the next execution layer."
    )
