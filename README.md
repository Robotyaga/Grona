# Grona

Grona is a lightweight research prototype for a modular sparse AI architecture inspired by grape-cluster-like expert activation.

The core idea is simple: do not activate every capability for every task. Route a task to relevant expert modules, gather focused context from stubs or memory modules, optionally run deterministic demo experts, and keep the trace visible.

## Architecture Metaphor

- The router chooses relevant branches and grapes.
- Memory modules are small knowledge pockets attached to parts of the cluster.
- The context builder gathers only the information needed by selected grapes.
- The orchestrator coordinates the selected path.
- Demo expert executors are the first tiny working grapes that can return structured results.
- The feedback layer remembers which paths worked.
- Adaptive routing slightly adjusts future activation from previous outcomes.

## Current Prototype

The current prototype includes:

- `ExpertModule`: metadata used for routing and module identity.
- `ExecutableExpert`: a lightweight execution contract for future runnable experts.
- `ExpertResult`: structured deterministic output from an executor.
- `ExpertExecutorRegistry`: maps routed module names to executors.
- deterministic demo executors for code, automotive, cybersecurity, media/video, document search, and general reasoning.
- `Router`, `RoutingDecision`, feedback, adaptive routing, memory modules, context building, orchestration, CLI, examples, tests, and CI.

The demo executors are not real AI. They are deterministic proof-of-contract adapters that produce summaries and detail bullets from the task and prepared context.

## Install

```bash
pip install -e .
```

For tests and linting:

```bash
pip install -e .[dev]
```

## Run Demos

```bash
python examples/basic_routing_demo.py
python examples/feedback_demo.py
python examples/adaptive_routing_demo.py
python examples/orchestration_demo.py
python examples/memory_demo.py
python examples/expert_execution_demo.py
```

## Run the CLI

Route a task:

```bash
python -m grona "Review firewall logs for suspicious port scans"
```

Build context with demo memory:

```bash
python -m grona "Diagnose engine overheating" --orchestrate --use-demo-memory
```

Run deterministic demo experts:

```bash
python -m grona "Diagnose engine overheating" --orchestrate --use-demo-memory --execute-demo-experts
```

`--execute-demo-experts` implies orchestration if `--orchestrate` is omitted.

## Run Tests

```bash
pytest
```

Optional linting:

```bash
ruff check .
```

## Expert Execution Interface

`ExpertModule` remains routing metadata. `ExecutableExpert` is the execution contract:

```python
from grona import ContextBuilder, Orchestrator, Router
from grona import create_default_executor_registry, create_default_memory_modules, create_default_registry

router = Router(create_default_registry())
builder = ContextBuilder(memory_modules=create_default_memory_modules())
executors = create_default_executor_registry()
result = Orchestrator(router, builder, executors).run("Diagnose engine overheating")
print(result.to_text())
```

Future real experts could be local LLM wrappers, scripts, shell tools, retrievers, media analyzers, code analyzers, or cybersecurity scanners. They should implement the same interface and return `ExpertResult` objects.

## Current Limitations

- Demo executors are deterministic stubs, not real AI reasoning.
- No external tools are called.
- No OpenAI API, Ollama integration, web server, vector database, SQL database, or external APIs.
- Memory retrieval is keyword/domain overlap only.
- No embeddings or semantic search yet.
- No persistent memory graph yet.
- No production orchestration.

These limits are intentional. Grona is currently a research/prototype foundation for sparse modular AI architecture.
