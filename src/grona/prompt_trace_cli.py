"""CLI demo for prompt building and inference trace records."""

from __future__ import annotations

from collections.abc import Sequence

from .context import ContextBuilder
from .defaults import create_default_registry
from .prompting import InMemoryInferenceTraceStore, run_static_prompt_trace
from .router import Router

DEMO_TASK = "Explain how sparse routing keeps a local modular AI prototype inspectable."


def format_prompt_trace_demo() -> str:
    """Run deterministic prompt trace demo and format output."""
    router = Router(create_default_registry(), top_k=3)
    decision = router.route(DEMO_TASK)
    context_items = ContextBuilder().build(decision, DEMO_TASK)
    result = run_static_prompt_trace(
        DEMO_TASK,
        routing_decision=decision,
        context_items=context_items,
        workspace_metadata={"workspace": "default", "demo": "prompt_trace"},
    )
    store = InMemoryInferenceTraceStore()
    store.add(result.trace)
    response_preview = result.response.text[:180]
    lines = [
        "Prompt trace demo",
        "Execution: deterministic static adapter only; no LM Studio, APIs, downloads, or training.",
        "",
        "Rendered prompt preview:",
        result.prompt.to_text(),
        "",
        "Response preview:",
        response_preview,
        "",
        "Trace summary:",
        result.trace.to_text(),
        "",
        f"Stored traces: {store.count()}",
        "Trace JSON preview:",
        result.trace.to_json(),
    ]
    return "\n".join(lines).rstrip()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the deterministic prompt trace demo helper."""
    _ = argv
    print(format_prompt_trace_demo())
    return 0
