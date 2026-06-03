"""Simple orchestration over routed modules, context, and optional execution."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapters import ExecutionAdapterRegistry, ExecutionRequest
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
                backend = format_result_backend(result)
                if backend:
                    lines.append(backend)
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
        adapter_registry: ExecutionAdapterRegistry | None = None,
    ) -> None:
        self.router = router
        self.context_builder = context_builder or ContextBuilder()
        self.executor_registry = executor_registry
        self.adapter_registry = adapter_registry

    def run(self, task: str) -> OrchestrationResult:
        """Route a task, build context, and optionally execute selected modules."""
        decision = self.router.route(task)
        context_items = self.context_builder.build(decision, task)
        selected_modules = decision.selected_names
        source_counts = count_context_sources(context_items)
        execution = self._execute_selected(task, selected_modules, context_items)
        return OrchestrationResult(
            task=task,
            routing_decision=decision,
            context_items=context_items,
            selected_modules=selected_modules,
            expert_results=execution.results,
            summary=summarize_orchestration(
                decision,
                context_items,
                source_counts,
                execution,
            ),
            metadata={
                "context_count": len(context_items),
                "selected_count": len(selected_modules),
                "execution": execution.state,
                "execution_backend": execution.backend,
                "expert_result_count": len(execution.results),
                "missing_executors": execution.missing_executors,
                "missing_adapters": execution.missing_adapters,
                "source_counts": source_counts,
            },
        )

    def _execute_selected(
        self,
        task: str,
        selected_modules: tuple[str, ...],
        context_items: tuple[ContextItem, ...],
    ) -> ExecutionOutcome:
        if self.executor_registry is not None:
            return self._execute_with_executors(task, selected_modules, context_items)
        if self.adapter_registry is not None:
            return self._execute_with_adapters(task, selected_modules, context_items)
        return ExecutionOutcome(state="not_run", backend="handoff")

    def _execute_with_executors(
        self,
        task: str,
        selected_modules: tuple[str, ...],
        context_items: tuple[ContextItem, ...],
    ) -> ExecutionOutcome:
        results: list[ExpertResult] = []
        missing: list[str] = []
        if self.executor_registry is None:
            return ExecutionOutcome(state="not_run", backend="handoff")

        for module_name in selected_modules:
            executor = self.executor_registry.get(module_name)
            if executor is None:
                missing.append(module_name)
                continue
            results.append(executor.execute(task, context_items))
        return ExecutionOutcome(
            state="executed",
            backend="expert_executor",
            results=tuple(results),
            missing_executors=tuple(missing),
        )

    def _execute_with_adapters(
        self,
        task: str,
        selected_modules: tuple[str, ...],
        context_items: tuple[ContextItem, ...],
    ) -> ExecutionOutcome:
        results: list[ExpertResult] = []
        missing: list[str] = []
        if self.adapter_registry is None:
            return ExecutionOutcome(state="not_run", backend="handoff")

        for module_name in selected_modules:
            adapter = self.adapter_registry.get(module_name)
            if adapter is None:
                missing.append(module_name)
                continue
            request = ExecutionRequest(
                task=task,
                module_name=module_name,
                context_items=context_items,
                metadata={"selected_modules": selected_modules},
            )
            results.append(adapter.execute(request))
        return ExecutionOutcome(
            state="executed",
            backend="execution_adapter",
            results=tuple(results),
            missing_adapters=tuple(missing),
        )


@dataclass(frozen=True)
class ExecutionOutcome:
    """Internal execution summary for orchestrator result construction."""

    state: str
    backend: str
    results: tuple[ExpertResult, ...] = ()
    missing_executors: tuple[str, ...] = ()
    missing_adapters: tuple[str, ...] = ()


def count_context_sources(context_items: tuple[ContextItem, ...]) -> dict[str, int]:
    """Count context items by source kind."""
    counts: dict[str, int] = {"stub": 0, "memory": 0}
    for item in context_items:
        source_kind = "memory" if item.source.startswith("memory:") else "stub"
        counts[source_kind] = counts.get(source_kind, 0) + 1
    return counts


def format_result_backend(result: ExpertResult) -> str:
    """Format adapter or executor backend metadata for a result."""
    adapter_name = result.metadata.get("adapter_name")
    if adapter_name:
        kind = result.metadata.get("backend_kind", "adapter")
        return f"Backend: adapter {adapter_name} ({kind})"
    executor_kind = result.metadata.get("executor_kind")
    if executor_kind:
        return f"Backend: executor ({executor_kind})"
    return ""


def summarize_orchestration(
    decision: RoutingDecision,
    context_items: tuple[ContextItem, ...],
    source_counts: dict[str, int] | None = None,
    execution: ExecutionOutcome | None = None,
) -> str:
    """Create a compact orchestration summary."""
    selected = ", ".join(decision.selected_names) or "no specialized modules"
    counts = source_counts or count_context_sources(context_items)
    outcome = execution or ExecutionOutcome(state="not_run", backend="handoff")
    execution_note = (
        "would pass this focused context to the next execution layer; "
        "no expert execution was requested"
    )
    if outcome.results and outcome.backend == "expert_executor":
        execution_note = f"executed {len(outcome.results)} deterministic demo experts"
    if outcome.results and outcome.backend == "execution_adapter":
        execution_note = f"executed {len(outcome.results)} deterministic adapter results"
    if outcome.missing_executors:
        missing = ", ".join(outcome.missing_executors)
        execution_note += f"; missing executors for {missing}"
    if outcome.missing_adapters:
        missing = ", ".join(outcome.missing_adapters)
        execution_note += f"; missing adapters for {missing}"
    return (
        f"Grona selected {selected}, prepared {len(context_items)} context items "
        f"({counts.get('stub', 0)} stub, {counts.get('memory', 0)} memory), "
        f"and {execution_note}."
    )
