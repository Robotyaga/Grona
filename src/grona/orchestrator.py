"""Simple orchestration over routed modules, context, and optional execution."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapters import ExecutionAdapterRegistry, ExecutionRequest
from .context import ContextBuilder, ContextItem
from .decision import RoutingDecision
from .executor import ExpertExecutorRegistry, ExpertResult
from .feedback import Metadata
from .router import Router
from .safety import SafeExecutionAdapter, SafetyPolicy
from .tools import SafeToolRunner, ToolResult, tool_request_for_module


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
        safety_policy: SafetyPolicy | None = None,
        dry_run_tools: bool = False,
        tool_runner: SafeToolRunner | None = None,
    ) -> None:
        self.router = router
        self.context_builder = context_builder or ContextBuilder()
        self.executor_registry = executor_registry
        self.adapter_registry = adapter_registry
        self.safety_policy = safety_policy
        self.dry_run_tools = dry_run_tools
        self.tool_runner = tool_runner

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
                **execution.safety_summary,
                **execution.tool_summary,
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
        tool_results: list[ToolResult] = []
        if self.adapter_registry is None:
            return ExecutionOutcome(state="not_run", backend="handoff")

        for module_name in selected_modules:
            adapter = self.adapter_registry.get(module_name)
            if adapter is None:
                missing.append(module_name)
                continue
            if self.safety_policy is not None or self.dry_run_tools:
                adapter = SafeExecutionAdapter(
                    adapter,
                    policy=self.safety_policy,
                    force_dry_run=self.dry_run_tools,
                )
            request = ExecutionRequest(
                task=task,
                module_name=module_name,
                context_items=context_items,
                metadata={"selected_modules": selected_modules},
            )
            result = adapter.execute(request)
            tool_result = self._run_demo_tool(module_name, task)
            if tool_result is not None:
                tool_results.append(tool_result)
                result = attach_tool_result(result, tool_result)
            results.append(result)
        return ExecutionOutcome(
            state="executed",
            backend="execution_adapter",
            results=tuple(results),
            missing_adapters=tuple(missing),
            safety_summary=summarize_safety_results(results),
            tool_summary=summarize_tool_results(tuple(tool_results)),
        )

    def _run_demo_tool(self, module_name: str, task: str) -> ToolResult | None:
        if self.tool_runner is None:
            return None
        request = tool_request_for_module(module_name, task)
        if request is None:
            return None
        return self.tool_runner.run(request)


@dataclass(frozen=True)
class ExecutionOutcome:
    """Internal execution summary for orchestrator result construction."""

    state: str
    backend: str
    results: tuple[ExpertResult, ...] = ()
    missing_executors: tuple[str, ...] = ()
    missing_adapters: tuple[str, ...] = ()
    safety_summary: Metadata = field(default_factory=dict)
    tool_summary: Metadata = field(default_factory=dict)


def attach_tool_result(result: ExpertResult, tool_result: ToolResult) -> ExpertResult:
    """Attach a mock tool result to an expert result."""
    tool_details = (
        f"Tool result from {tool_result.tool_name}: {tool_result.output}",
        *(f"Tool detail: {detail}" for detail in tool_result.details),
    )
    metadata = {
        **result.metadata,
        "tool_used": True,
        "tool_name": tool_result.tool_name,
        "tool_success": tool_result.success,
        "tool_policy_allowed": tool_result.metadata.get("policy_allowed"),
        "tool_policy_dry_run": tool_result.metadata.get("policy_dry_run"),
    }
    return ExpertResult(
        module_name=result.module_name,
        task=result.task,
        summary=result.summary,
        details=(*result.details, *tool_details),
        confidence=result.confidence,
        metadata=metadata,
    )


def count_context_sources(context_items: tuple[ContextItem, ...]) -> dict[str, int]:
    """Count context items by source kind."""
    counts: dict[str, int] = {"stub": 0, "memory": 0}
    for item in context_items:
        source_kind = "memory" if item.source.startswith("memory:") else "stub"
        counts[source_kind] = counts.get(source_kind, 0) + 1
    return counts


def summarize_safety_results(results: tuple[ExpertResult, ...]) -> Metadata:
    """Aggregate safety metadata from expert results."""
    safe_results = [item for item in results if item.metadata.get("safety_policy_used")]
    if not safe_results:
        return {"safety_policy_used": False}
    return {
        "safety_policy_used": True,
        "planned_action_count": sum(
            int(item.metadata.get("planned_action_count", 0)) for item in safe_results
        ),
        "allowed_action_count": sum(
            int(item.metadata.get("allowed_action_count", 0)) for item in safe_results
        ),
        "blocked_action_count": sum(
            int(item.metadata.get("blocked_action_count", 0)) for item in safe_results
        ),
        "dry_run_tools": any(bool(item.metadata.get("dry_run_tools")) for item in safe_results),
    }


def summarize_tool_results(tool_results: tuple[ToolResult, ...]) -> Metadata:
    """Aggregate mock tool result metadata."""
    if not tool_results:
        return {"tool_results_used": False}
    return {
        "tool_results_used": True,
        "tool_result_count": len(tool_results),
        "tool_success_count": sum(1 for item in tool_results if item.success),
        "tool_blocked_count": sum(1 for item in tool_results if not item.success),
        "tool_dry_run_count": sum(
            1 for item in tool_results if bool(item.metadata.get("policy_dry_run"))
        ),
    }


def format_result_backend(result: ExpertResult) -> str:
    """Format adapter or executor backend metadata for a result."""
    adapter_name = result.metadata.get("adapter_name")
    safe_adapter_name = result.metadata.get("safe_adapter_name")
    if adapter_name:
        kind = result.metadata.get("backend_kind", "adapter")
        prefix = f"safe wrapper {safe_adapter_name}; " if safe_adapter_name else ""
        return f"Backend: {prefix}adapter {adapter_name} ({kind})"
    if result.metadata.get("safety_policy_used"):
        return "Backend: safe adapter planning result"
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
    if outcome.safety_summary.get("safety_policy_used"):
        execution_note += (
            f"; safety planned {outcome.safety_summary.get('planned_action_count', 0)} "
            "tool actions"
        )
    if outcome.tool_summary.get("tool_results_used"):
        execution_note += (
            f"; mock tools returned {outcome.tool_summary.get('tool_result_count', 0)} "
            "tool results"
        )
    return (
        f"Grona selected {selected}, prepared {len(context_items)} context items "
        f"({counts.get('stub', 0)} stub, {counts.get('memory', 0)} memory), "
        f"and {execution_note}."
    )
