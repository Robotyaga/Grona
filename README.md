# Grona

Grona is a lightweight research prototype for a modular sparse AI architecture inspired by grape-cluster-like expert activation.

The core idea is simple: do not activate every capability for every task. Route a task to relevant expert modules, gather focused context from stubs or memory modules, optionally run deterministic demo experts or execution adapters, and keep the trace visible.

## Architecture Metaphor

- The router chooses relevant branches and grapes.
- Memory modules are small knowledge pockets attached to parts of the cluster.
- The context builder gathers only the information needed by selected grapes.
- The orchestrator coordinates the selected path.
- Demo expert executors are the first tiny working grapes that can return structured results.
- Execution adapters are bridges from selected grapes to future execution backends.
- The feedback layer remembers which paths worked.
- Adaptive routing slightly adjusts future activation from previous outcomes.

## Current Prototype

The current prototype includes:

- `ExpertModule`: metadata used for routing and module identity.
- `ExecutableExpert`: a lightweight direct execution contract for runnable experts.
- `ExecutionAdapter`: a bridge from selected modules to future execution backends.
- `ExecutionRequest`: normalized task, module, context, and metadata input for adapters.
- `ExpertResult`: structured deterministic output from executors or adapters.
- `ExpertExecutorRegistry` and `ExecutionAdapterRegistry`.
- deterministic demo executors and deterministic demo adapters for default modules.
- `Router`, `RoutingDecision`, feedback, adaptive routing, memory modules, context building, orchestration, CLI, examples, tests, and CI.

The demo executors and adapters are not real AI. They are deterministic proof-of-contract implementations that produce summaries and detail bullets from the task and prepared context.

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
python examples/execution_adapters_demo.py
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

Run deterministic demo adapters:

```bash
python -m grona "Review this Python script for security issues" --orchestrate --use-demo-adapters
```

`--execute-demo-experts` and `--use-demo-adapters` imply orchestration if `--orchestrate` is omitted. If both execution options are supplied, explicit demo experts take precedence over adapters.

## Run Tests

```bash
pytest
```

Optional linting:

```bash
ruff check .
```

## Expert Execution Interface

`ExpertModule` remains routing metadata. `ExecutableExpert` is the direct execution contract:

```python
from grona import ContextBuilder, Orchestrator, Router
from grona import create_default_executor_registry, create_default_memory_modules, create_default_registry

router = Router(create_default_registry())
builder = ContextBuilder(memory_modules=create_default_memory_modules())
executors = create_default_executor_registry()
result = Orchestrator(router, builder, executors).run("Diagnose engine overheating")
print(result.to_text())
```

## Execution Adapters

Execution adapters are separate from both routing metadata and direct demo executors. They receive an `ExecutionRequest` and return an `ExpertResult`:

```python
from grona import Orchestrator, Router, create_default_adapter_registry, create_default_registry

router = Router(create_default_registry())
adapters = create_default_adapter_registry()
result = Orchestrator(router, adapter_registry=adapters).run("Review exposed secrets")
print(result.to_text())
```

Future adapters could connect selected modules to local Python functions, local scripts, shell tools, local LLM wrappers, code analyzers, document processors, media analyzers, or security scanners. Those backends are intentionally not implemented yet.

## Current Limitations

- Demo executors and adapters are deterministic stubs, not real AI reasoning.
- No shell commands, subprocess execution, sandboxing, or unsafe tools are implemented.
- No external tools are called.
- No OpenAI API, Ollama integration, web server, vector database, SQL database, or external APIs.
- Memory retrieval is keyword/domain overlap only.
- No embeddings or semantic search yet.
- No persistent memory graph yet.
- No production orchestration.

These limits are intentional. Grona is currently a research/prototype foundation for sparse modular AI architecture.
