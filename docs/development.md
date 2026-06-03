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
- `tests/` covers routing, feedback, adaptive routing, context building, and orchestration.
- `pyproject.toml` defines packaging, test, and lint settings.
- `.github/workflows/tests.yml` runs the test suite in CI.

## Add a New Expert Module

Add new demo modules in `src/grona/defaults.py` or create them in your own script:

```python
from grona import ExpertModule

module = ExpertModule(
    name="new-domain-module",
    domain="new domain",
    capabilities=("inspection", "summarization"),
    keywords=("domain", "specific", "terms"),
    handler=lambda task, context: "mock result",
    description="Short explanation of what the module is for.",
    cost=1,
)
```

Then register it:

```python
from grona import ModuleRegistry

registry = ModuleRegistry([module])
```

## Add Routing Keywords or Domains

Routing is currently based on normalized text terms from three metadata fields:

- `domain`: broad task area, weighted highest.
- `keywords`: specific task signals.
- `capabilities`: operations the module can perform.

Keep keywords concrete and domain-specific. Avoid adding every generic word to every module, because that makes sparse routing less useful.

## Add Context Stubs

Context stubs live in `src/grona/context.py`. Add small deterministic strings that help explain what context a selected module would receive later.

Good context stubs are:

- domain-specific
- deterministic
- short enough to inspect in CLI output
- honest that they are not real retrieval
- covered by tests when they affect routing or orchestration expectations

Do not add file indexing, vector retrieval, SQL, external APIs, or LLM memory here yet.

## Use the Orchestrator

The orchestrator routes a task, builds route-scoped context, and returns a structured handoff:

```python
from grona import Orchestrator, Router, create_default_registry

router = Router(create_default_registry())
result = Orchestrator(router).run("Analyze engine overheating symptoms")
print(result.to_text())
```

The orchestrator does not execute real experts yet. Keep it as a visible coordination layer until real module execution is designed and tested.

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
- Let modules be added, disabled, or replaced through the registry.
- Keep scoring deterministic while the router is rule-based.
- Keep feedback passive unless adaptive routing is explicitly enabled.
- Keep adaptive routing bounded, explainable, and tested.
- Keep context building separate from routing.
- Keep orchestration separate from real execution.

## What Not to Add Yet

Do not add these until the routing and context prototype justifies them:

- web servers
- vector databases
- SQL databases
- production task queues
- external LLM dependencies
- heavy agent frameworks
- hidden global memory
- opaque learned routing
- fake AI execution
- automatic route adaptation without tests and route traces
- claims that Grona has neural learning or production orchestration

The current goal is a clean foundation for research, tests, route history, adaptive scoring, route-scoped context, and future orchestration experiments.
