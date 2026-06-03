"""Simple orchestration over routed modules, context, and optional execution."""

from __future__ import annotations

from dataclasses import dataclass, field

from .context import ContextBuilder, ContextItem
from .decision import RoutingDecision
from .executor import ExpertExecutorRegistry, ExpertResult
from .feedback import Metadata
from .router import Router


@dataclass(frozen=True)
class OrchestrationResult:
    """The visible result of routing, context preparation, and optional execution."""

    task: str
    routing_decision: RoutingDecision
    context_items: tuple[ContextItem, ...]
    selected_modules: tuple[str, ...]
    summary: str
    expert_results: tuple[ExpertResult, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    @property
    def context_sources(self) -> tuple[str, ...]:
        """Return context source names in build order."""
        return tuple(item.source for item in self.context_items)

    def to_text(self) -> str:
        """Format the orchestration result without claiming real AI execution."""
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

        lines.extend(["", "Expert results:"])
        if self.expert_results:
            for result in self.expert_results:
                lines.append(result.to_text())
        else:
            lines.append("- not run")

        lines.append(f"Orchestration summary: {self.summary}")
        return "\n".join(lines)


class Orchestrator:
    """Coordinate routing, context building, and optional expert execution."""

    def __init__(
        self,
        router: Router,
        context_builder: ContextBuilder | None = None,
        executor_registry: ExpertExecutorRegistry | None = None,
    ) -> None:
        self.router = router
        self.context_builder = context_builder or ContextBuilder()
        self.executor_registry = executor_registry

    def run(self, task: str) -> OrchestrationResult:
        """Route a task, build context, and optionally execute demo experts."""
        decision = self.router.route(task)
        context_items = self.context_builder.build(decision, task)
        selected_modules = decision.selected_names
        source_counts = count_context_sources(context_items)
        expert_results, missing_executors = self._execute_selected(
            task,
            selected_modules,
            context_items,
        )
        execution_state = "executed" if self.executor_registry else "not_run"
        return OrchestrationResult(
            task=task,
            routing_decision=decision,
            context_items=context_items,
            selected_modules=selected_modules,
            expert_results=expert_results,
            summary=summarize_orchestration(
                decision,
                context_items,
                source_counts,
                expert_results,
                missing_executors,
            ),
            metadata={
                "context_count": len(context_items),
                "selected_count": len(selected_modules),
                "execution": execution_state,
                "expert_result_count": len(expert_results),
                "missing_executors": missing_executors,
                "source_counts": source_counts,
            },
        )

    def _execute_selected(
        self,
        task: str,
        selected_modules: tuple[str, ...],
        context_items: tuple[ContextItem, ...],
    ) -> tuple[tuple[ExpertResult, ...], tuple[str, ...]]:
        if self.executor_registry is None:
            return (), ()

        results: list[ExpertResult] = []
        missing: list[str] = []
        for module_name in selected_modules:
            executor = self.executor_registry.get(module_name)
            if executor is None:
                missing.append(module_name)
                continue
            results.append(executor.execute(task, context_items))
        return tuple(results), tuple(missing)


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
    expert_results: tuple[ExpertResult, ...] = (),
    missing_executors: tuple[str, ...] = (),
) -> str:
    """Create a compact orchestration summary."""
    selected = ", ".join(decision.selected_names) or "no specialized modules"
    counts = source_counts or count_context_sources(context_items)
    execution_note = "no expert execution was requested"
    if expert_results:
        execution_note = f"executed {len(expert_results)} deterministic demo experts"
    if missing_executors:
        missing = ", ".join(missing_executors)
        execution_note += f"; missing executors for {missing}"
    return (
        f"Grona selected {selected}, prepared {len(context_items)} context items "
        f"({counts.get('stub', 0)} stub, {counts.get('memory', 0)} memory), "
        f"and {execution_note}."
    )
