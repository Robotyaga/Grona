# Development Notes

Grona is currently an early research prototype. The code should stay small, readable, and easy to inspect while the architecture is still being explored.

## Repository Structure

```text
src/grona/
├── __init__.py      Public package exports
├── __main__.py      Enables `python -m grona`
├── adaptive.py      Feedback-informed score adjustment helpers
├── cli.py           Small routing CLI and output formatting
├── decision.py      Routing result data structures
├── defaults.py      Default mock/demo modules
├── feedback.py      Feedback records and route history stores
├── module.py        ExpertModule definition
├── registry.py      ModuleRegistry definition
└── router.py        Keyword/domain router
```

Supporting files:

- `examples/basic_routing_demo.py` shows multiple task routes.
- `examples/feedback_demo.py` shows route history without persistent storage.
- `examples/adaptive_routing_demo.py` shows feedback-informed score adjustments.
- `tests/` covers core routing, feedback, and adaptive behavior.
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

## Use Feedback Records

A feedback record captures one route decision and optional outcome information:

```python
from grona import FeedbackRecord, InMemoryFeedbackStore, Router, create_default_registry

router = Router(create_default_registry())
decision = router.route("Analyze engine overheating symptoms")
record = FeedbackRecord.from_decision(decision, rating=5, success=True, notes="Good route")

store = InMemoryFeedbackStore()
store.add(record)
```

Use `InMemoryFeedbackStore` for tests and demos. Use `JsonlFeedbackStore` when you explicitly want a local JSONL route history file. The JSONL store writes one JSON object per line and does not require a database.

## Use Adaptive Routing

Adaptive routing is opt-in. It uses feedback records to slightly adjust module scores after the base keyword/domain score is computed:

```python
from grona import AdaptiveRoutingConfig, Router, create_default_registry

router = Router(
    create_default_registry(),
    adaptive_config=AdaptiveRoutingConfig(enabled=True),
    feedback_records=store.list(),
)
decision = router.route("Analyze engine overheating symptoms")
```

Keep adaptive scoring conservative:

- Do not let history select modules with no base relevance.
- Keep `max_adjustment` small.
- Include adjustment explanations in route decisions.
- Treat this as deterministic scoring, not machine learning.

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

## What Not to Add Yet

Do not add these until the routing prototype justifies them:

- web servers
- vector databases
- production task queues
- external LLM dependencies
- heavy agent frameworks
- hidden global memory
- opaque learned routing
- automatic route adaptation without tests and route traces
- claims that Grona has neural learning or production orchestration

The current goal is a clean foundation for research, tests, route history, adaptive scoring experiments, and extension.
