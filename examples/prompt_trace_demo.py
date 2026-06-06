"""Demonstrate prompt building and deterministic inference trace creation."""

from grona import (
    ContextBuilder,
    InMemoryInferenceTraceStore,
    Router,
    create_default_registry,
    get_default_prompt_template,
    run_static_prompt_trace,
)


def main() -> None:
    """Run a deterministic prompt trace example without network access."""
    task = "Explain why a sparse modular assistant should keep prompt provenance."
    router = Router(create_default_registry(), top_k=3)
    decision = router.route(task)
    context_items = ContextBuilder().build(decision, task)
    template = get_default_prompt_template("general_task")
    result = run_static_prompt_trace(
        task,
        template=template,
        routing_decision=decision,
        context_items=context_items,
        workspace_metadata={"workspace": "default", "example": "prompt_trace"},
    )
    store = InMemoryInferenceTraceStore()
    store.add(result.trace)

    print("Prompt trace example")
    print("Execution: deterministic static adapter only; no LM Studio, APIs, or training.")
    print()
    print(result.prompt.to_text())
    print()
    print(result.response.to_text())
    print()
    print(result.trace.to_text())
    print()
    print(f"Stored traces: {store.count()}")
    print("Trace JSON preview:")
    print(result.trace.to_json())


if __name__ == "__main__":
    main()
