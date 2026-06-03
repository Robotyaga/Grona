# Development Notes

Grona is currently an early research prototype. The code should stay small, readable, and easy to inspect while the architecture is still being explored.

## Repository Structure

```text
src/grona/
|-- __init__.py      Public package exports
|-- __main__.py      Enables `python -m grona`
|-- adaptive.py      Feedback-informed score adjustment helpers
|-- cli.py           Small routing CLI and output formatting
|-- context.py       ContextItem and route-scoped ContextBuilder
|-- decision.py      Routing result data structures
|-- defaults.py      Default mock/demo modules
|-- feedback.py      Feedback records and route history stores
|-- memory.py        MemoryRecord and deterministic keyword memory
|-- module.py        ExpertModule definition
|-- orchestrator.py  Orchestrator and OrchestrationResult
|-- registry.py      ModuleRegistry definition
`-- router.py        Keyword/domain router
```

Supporting files:

- `examples/basic_routing_demo.py` shows multiple task routes.
- `examples/feedback_demo.py` shows route history without persistent storage.
- `examples/adaptive_routing_demo.py` shows feedback-informed score adjustments.
- `examples/orchestration_demo.py` shows route-scoped context and handoff summaries.
- `examples/memory_demo.py` shows deterministic memory context retrieval.
- `tests/` covers routing, feedback, adaptive routing, context, memory, and orchestration.

## Add Memory Records

Use `MemoryRecord` for small knowledge items:

```python
from grona import InMemoryKeywordMemory, MemoryRecord

records = [
    MemoryRecord(
        id="cooling-checklist",
        content="Check coolant level, thermostat operation, radiator flow, and fan activation.",
        domains=("automotive",),
        keywords=("coolant", "thermostat", "radiator", "fan"),
        source="local_stub",
    )
]

memory = InMemoryKeywordMemory(records, name="automotive-memory")
```

Memory records should stay small, domain-specific, and deterministic. Do not claim semantic search when the matching is keyword/domain overlap.

## Use Memory During Orchestration

```python
from grona import ContextBuilder, Orchestrator, Router, create_default_memory_modules, create_default_registry

router = Router(create_default_registry())
builder = ContextBuilder(memory_modules=create_default_memory_modules())
result = Orchestrator(router, context_builder=builder).run("Analyze engine overheating")
print(result.to_text())
```

## Feedback Store vs Memory Module

- Feedback stores record route outcomes, ratings, success flags, and notes.
- Memory modules provide knowledge records to the context builder.

They solve different problems and should remain separate.

## Run Tests

```bash
pip install -e .[dev]
pytest
ruff check .
```

## Keep the System Modular

- Put module metadata near the module definition.
- Keep handlers small and explicit.
- Prefer route traces over hidden behavior.
- Keep scoring deterministic while the router is rule-based.
- Keep memory retrieval deterministic until a stronger baseline is needed.
- Keep feedback passive unless adaptive routing is explicitly enabled.
- Keep context building separate from routing.
- Keep orchestration separate from real execution.

## What Not to Add Yet

Do not add these until the routing, context, and memory prototype justifies them:

- web servers
- vector databases
- SQL databases
- production task queues
- external LLM dependencies
- embeddings
- semantic search claims
- heavy agent frameworks
- hidden global memory
- fake AI execution
- automatic route adaptation without tests and route traces
- claims that Grona has neural learning or production orchestration

The current goal is a clean foundation for research, tests, route history, adaptive scoring, route-scoped context, deterministic memory stubs, and future orchestration experiments.
