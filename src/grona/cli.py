"""Command-line helpers for the Grona routing prototype."""

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Sequence

from .adapters import create_default_adapter_registry
from .adaptive import AdaptiveRoutingConfig
from .context import ContextBuilder
from .decision import RoutingDecision
from .defaults import create_default_registry
from .documents import DocumentIngestor, create_demo_document_sources
from .executor import create_default_executor_registry
from .feedback import FeedbackRecord, JsonlFeedbackStore
from .memory import MemoryModule, create_default_memory_modules
from .orchestrator import OrchestrationResult, Orchestrator, format_result_backend
from .router import Router
from .safety import create_default_safety_policy
from .tools import SafeToolRunner, create_default_tool_registry

DEFAULT_TASK = "Analyze engine overheating symptoms and explain what to inspect first."


def format_decision(decision: RoutingDecision) -> str:
    """Format a routing decision for humans."""
    lines = [f"Task: {decision.task}"]
    if decision.adaptive_enabled:
        history_note = (
            "feedback history loaded" if decision.feedback_available else "no feedback history"
        )
        lines.extend(["", f"Adaptive routing: enabled ({history_note})"])
    lines.extend(["", "Selected modules:"])

    if decision.selected_modules:
        for match in decision.selected_modules:
            lines.append(f"- {match.module.name} (score {match.score:.1f})")
            if match.adaptive_enabled:
                lines.append(
                    f"  base score: {match.base_score:.1f}; "
                    f"adaptive adjustment: {match.adaptive_adjustment:+.2f}; "
                    f"final score: {match.final_score:.1f}"
                )
            for reason in match.reasons:
                lines.append(f"  reason: {reason}")
    else:
        lines.append("- none")

    lines.extend(["", "Skipped modules:"])
    if decision.skipped_modules:
        for match in decision.skipped_modules:
            lines.append(f"- {match.module.name} (score {match.score:.1f})")
            if match.adaptive_enabled:
                lines.append(
                    f"  base score: {match.base_score:.1f}; "
                    f"adaptive adjustment: {match.adaptive_adjustment:+.2f}; "
                    f"final score: {match.final_score:.1f}"
                )
            lines.append(f"  reason: {'; '.join(match.reasons)}")
    else:
        lines.append("- none")

    return "\n".join(lines)


def format_orchestration_result(result: OrchestrationResult) -> str:
    """Format an orchestration result for humans."""
    lines = [format_decision(result.routing_decision)]
    lines.extend(["", "Context items:"])
    if result.context_items:
        for item in result.context_items:
            kind = item.metadata.get("context_kind", "context")
            lines.append(f"- {item.source} ({kind}, relevance {item.relevance:.2f})")
            lines.append(f"  content: {item.content}")
            reasons = item.metadata.get("reasons")
            if reasons:
                lines.append(f"  reason: {'; '.join(str(reason) for reason in reasons)}")
    else:
        lines.append("- none")

    lines.extend(["", "Expert results:"])
    if result.expert_results:
        for expert_result in result.expert_results:
            lines.append(expert_result.to_text())
            backend = format_result_backend(expert_result)
            if backend:
                lines.append(backend)
    else:
        lines.append("- not run")

    missing_executors = result.metadata.get("missing_executors") or ()
    if missing_executors:
        lines.append(f"Missing executors: {', '.join(str(name) for name in missing_executors)}")
    missing_adapters = result.metadata.get("missing_adapters") or ()
    if missing_adapters:
        lines.append(f"Missing adapters: {', '.join(str(name) for name in missing_adapters)}")
    if result.metadata.get("safety_policy_used"):
        lines.append(format_safety_summary(result))
    if result.metadata.get("tool_results_used"):
        lines.append(format_tool_summary(result))

    lines.extend(
        [
            "",
            execution_line(result),
            f"Orchestration summary: {result.summary}",
        ]
    )
    return "\n".join(lines)


def format_safety_summary(result: OrchestrationResult) -> str:
    """Format safety policy summary metadata."""
    return (
        "Safety: policy used; "
        f"planned {result.metadata.get('planned_action_count', 0)} actions, "
        f"allowed {result.metadata.get('allowed_action_count', 0)}, "
        f"blocked {result.metadata.get('blocked_action_count', 0)}, "
        f"dry-run {result.metadata.get('dry_run_tools', False)}"
    )


def format_tool_summary(result: OrchestrationResult) -> str:
    """Format mock tool summary metadata."""
    return (
        "Tools: mock tool results used; "
        f"count {result.metadata.get('tool_result_count', 0)}, "
        f"success {result.metadata.get('tool_success_count', 0)}, "
        f"blocked {result.metadata.get('tool_blocked_count', 0)}, "
        f"dry-run {result.metadata.get('tool_dry_run_count', 0)}"
    )


def execution_line(result: OrchestrationResult) -> str:
    """Return a human-readable execution status line."""
    backend = result.metadata.get("execution_backend")
    if backend == "expert_executor":
        return "Execution: deterministic demo executors only; no real AI or tools were called."
    if backend == "execution_adapter":
        if result.metadata.get("tool_results_used"):
            return "Execution: deterministic mock tools only; no real tools were called."
        if result.metadata.get("safety_policy_used"):
            return "Execution: safety policy planning only; no real tools were called."
        return "Execution: deterministic demo adapters only; no real AI or tools were called."
    return "Execution: not run; this prototype only prepares a structured handoff."


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Grona demo router from the command line."""
    parser = build_parser()
    args = parser.parse_args(argv)

    task = " ".join(args.task).strip() or DEFAULT_TASK
    feedback_file = args.feedback_file or args.save_feedback
    feedback_records = (
        load_feedback_records(feedback_file) if args.adaptive and feedback_file else ()
    )
    router = Router(
        create_default_registry(),
        top_k=args.top_k,
        adaptive_config=AdaptiveRoutingConfig(enabled=args.adaptive),
        feedback_records=feedback_records,
    )

    should_orchestrate = (
        args.orchestrate
        or args.execute_demo_experts
        or args.use_demo_adapters
        or args.use_demo_tools
    )
    if should_orchestrate:
        context_builder = ContextBuilder(memory_modules=build_cli_memory_modules(args))
        use_adapters = args.use_demo_adapters or args.use_demo_tools
        executor_registry = (
            create_default_executor_registry() if args.execute_demo_experts else None
        )
        adapter_registry = create_default_adapter_registry() if use_adapters else None
        safety_policy = (
            create_default_safety_policy(dry_run=args.dry_run_tools)
            if args.safe or args.dry_run_tools or args.use_demo_tools
            else None
        )
        tool_runner = None
        if args.use_demo_tools:
            tool_runner = SafeToolRunner(
                create_default_tool_registry(),
                policy=safety_policy,
                force_dry_run=args.dry_run_tools,
            )
        result = Orchestrator(
            router,
            context_builder=context_builder,
            executor_registry=executor_registry,
            adapter_registry=adapter_registry,
            safety_policy=safety_policy,
            dry_run_tools=args.dry_run_tools,
            tool_runner=tool_runner,
        ).run(task)
        if args.execute_demo_experts and not args.orchestrate:
            print("Execution note: --execute-demo-experts implies --orchestrate.\n")
        if args.use_demo_adapters and not args.orchestrate:
            print("Execution note: --use-demo-adapters implies --orchestrate.\n")
        if args.use_demo_tools and not args.orchestrate:
            print("Execution note: --use-demo-tools implies --orchestrate.\n")
        if args.use_demo_tools and not args.safe:
            print("Execution note: --use-demo-tools uses the default safety policy.\n")
        if args.ingest_demo_docs:
            print("Memory note: --ingest-demo-docs added deterministic ingested memory.\n")
        if args.dry_run_tools and not args.safe:
            print("Execution note: --dry-run-tools enables the default safety policy.\n")
        if args.execute_demo_experts and args.use_demo_adapters:
            print(
                "Execution note: --execute-demo-experts takes precedence "
                "over --use-demo-adapters.\n"
            )
        print(format_orchestration_result(result))
        decision = result.routing_decision
    else:
        decision = router.route(task)
        print(format_decision(decision))

        print("\nActivated outputs:")
        for match, output in router.run(task):
            print(f"- {match.module.name}: {output}")
        if args.use_demo_memory:
            print("\nMemory note: --use-demo-memory is only used with --orchestrate.")
        if args.ingest_demo_docs:
            print("\nMemory note: --ingest-demo-docs is only used with orchestration.")

    if feedback_file:
        record = FeedbackRecord.from_decision(
            decision,
            rating=args.rating,
            success=parse_success(args.success),
            notes=args.notes,
        )
        JsonlFeedbackStore(feedback_file).add(record)
        print(f"\nSaved feedback: {feedback_file}")

    return 0


def build_cli_memory_modules(args) -> tuple[MemoryModule, ...]:  # noqa: ANN001
    """Build memory modules requested by CLI flags."""
    modules: list[MemoryModule] = []
    if args.use_demo_memory:
        modules.extend(create_default_memory_modules())
    if args.ingest_demo_docs:
        modules.append(
            DocumentIngestor().build_memory_module(
                "demo-document-ingestion",
                create_demo_document_sources(),
            )
        )
    return tuple(modules)


def build_parser() -> ArgumentParser:
    """Build the CLI argument parser."""
    parser = ArgumentParser(description="Route a task through Grona's demo module registry.")
    parser.add_argument("task", nargs="*", help="Task text to route. Uses a demo task if omitted.")
    parser.add_argument("--top-k", type=int, default=3, help="Maximum number of modules to select.")
    parser.add_argument(
        "--adaptive",
        action="store_true",
        help="Enable feedback-informed score adjustments when feedback history is available.",
    )
    parser.add_argument(
        "--orchestrate",
        action="store_true",
        help="Build route-scoped context and prepare an orchestration handoff.",
    )
    parser.add_argument(
        "--use-demo-memory",
        action="store_true",
        help="Use built-in deterministic demo memory during orchestration.",
    )
    parser.add_argument(
        "--ingest-demo-docs",
        action="store_true",
        help="Ingest deterministic in-memory demo documents during orchestration.",
    )
    parser.add_argument(
        "--execute-demo-experts",
        action="store_true",
        help="Run deterministic demo experts during orchestration.",
    )
    parser.add_argument(
        "--use-demo-adapters",
        action="store_true",
        help="Run deterministic demo execution adapters during orchestration.",
    )
    parser.add_argument(
        "--use-demo-tools",
        action="store_true",
        help="Run deterministic mock tools through SafeToolRunner during orchestration.",
    )
    parser.add_argument(
        "--safe",
        action="store_true",
        help="Use the default safety policy for adapter execution planning.",
    )
    parser.add_argument(
        "--dry-run-tools",
        action="store_true",
        help="Force planned tool actions into dry-run mode. No tools are executed.",
    )
    parser.add_argument(
        "--save-feedback",
        help="Optional JSONL file path for saving route feedback.",
    )
    parser.add_argument(
        "--feedback-file",
        help="Optional JSONL file path for loading adaptive history and saving route feedback.",
    )
    parser.add_argument(
        "--rating",
        type=int,
        choices=range(1, 6),
        help="Optional route rating, 1-5.",
    )
    parser.add_argument(
        "--success",
        choices=("true", "false"),
        help="Optional route outcome flag.",
    )
    parser.add_argument("--notes", help="Optional route outcome notes.")
    return parser


def load_feedback_records(feedback_file: str) -> tuple[FeedbackRecord, ...]:
    """Load feedback history for adaptive routing."""
    return JsonlFeedbackStore(feedback_file).list()


def parse_success(value: str | None) -> bool | None:
    """Parse an optional CLI success flag."""
    if value is None:
        return None
    return value == "true"
