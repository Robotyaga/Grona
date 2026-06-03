# Development Notes

Grona is currently an early research prototype. The code should stay small, readable, and easy to inspect while the architecture is still being explored.

## Repository Structure

```text
src/grona/
├── __init__.py      Public package exports
├── __main__.py      Enables `python -m grona`
├── cli.py           Small routing CLI and output formatting
├── decision.py      Routing result data structures
├── defaults.py      Default mock/demo modules
├── module.py        ExpertModule definition
├── registry.py      ModuleRegistry definition
└── router.py        Keyword/domain router
```

Supporting files:

- `examples/basic_routing_demo.py` shows multiple task routes.
- `tests/` covers core routing behavior.
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

## What Not to Add Yet

Do not add these until the routing prototype justifies them:

- web servers
- vector databases
- production task queues
- external LLM dependencies
- heavy agent frameworks
- hidden global memory
- claims that Grona has learned routing or production orchestration

The current goal is a clean foundation for research, tests, and extension.
