"""Simple orchestration over routed modules and built context."""

from __future__ import annotations

from dataclasses import dataclass, field

from .context import ContextBuilder, ContextItem
from .decision import RoutingDecision
from .feedback import Metadata
from .router import Router


@dataclass(frozen=True)
class OrchestrationResult:
    """The visible result of routing, context building, and module execution."""

    task: str
    routing_decision: RoutingDecision
    context_items: tuple[ContextItem, ...]
    module_outputs: tuple[tuple[str, str], ...]
    summary: str
    metadata: Metadata = field(default_factory=dict)

    @property
    def selected_modules(self) -> tuple[str, ...]:
        """Return selected module names in route order."""
        return self.routing_decision.selected_names

    @property
    def context_sources(self) -> tuple[str, ...]:
        """Return context source names in build order."""
        return tuple(item.source for item in self.context_items)


class Orchestrator:
    """Coordinate routing, context building, and selected module execution."""

    def __init__(
        self,
        router: Router,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self.router = router
        self.context_builder = context_builder or ContextBuilder()

    def run(self, task: str) -> OrchestrationResult:
        """Route a task, build context, and invoke selected demo modules."""
        decision = self.router.route(task)
        context_items = self.context_builder.build(decision)
        module_context = {
            "selected_modules": ", ".join(decision.selected_names),
            "context_sources": ", ".join(item.source for item in context_items),
            "context_summary": summarize_context(context_items),
        }
        outputs = tuple(
            (match.module.name, match.module.run(task, module_context))
            for match in decision.selected_modules
        )
        return OrchestrationResult(
            task=task,
            routing_decision=decision,
            context_items=context_items,
            module_outputs=outputs,
            summary=summarize_orchestration(decision, context_items, outputs),
            metadata={"context_count": len(context_items), "output_count": len(outputs)},
        )


def summarize_context(context_items: tuple[ContextItem, ...]) -> str:
    """Create a compact context summary for module handlers."""
    if not context_items:
        return "No context items were built."
    sources = ", ".join(item.source for item in context_items)
    return f"Built {len(context_items)} context items from: {sources}."


def summarize_orchestration(
    decision: RoutingDecision,
    context_items: tuple[ContextItem, ...],
    outputs: tuple[tuple[str, str], ...],
) -> str:
    """Create a compact orchestration summary."""
    selected = ", ".join(decision.selected_names) or "none"
    return (
        f"Selected {len(decision.selected_modules)} modules ({selected}), "
        f"built {len(context_items)} context items, "
        f"and collected {len(outputs)} module outputs."
    )
