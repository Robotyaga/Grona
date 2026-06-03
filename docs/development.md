# Development Notes

Grona is an early research prototype. Keep the code small, readable, deterministic, and honest about what it does.

## Repository Structure

```text
src/grona/
|-- adaptive.py      Feedback-informed score adjustment helpers
|-- adapters.py      ExecutionRequest, adapters, and adapter registry
|-- cli.py           Routing, orchestration, memory, and execution CLI
|-- context.py       ContextItem and ContextBuilder
|-- decision.py      Routing decision data structures
|-- executor.py      ExpertResult, ExecutableExpert, demo executors
|-- feedback.py      Feedback records and route history stores
|-- memory.py        MemoryRecord and deterministic keyword memory
|-- module.py        ExpertModule routing metadata
|-- orchestrator.py  Orchestrator and OrchestrationResult
|-- registry.py      ModuleRegistry
`-- router.py        Keyword/domain router
```

## Metadata vs Execution

`ExpertModule` is metadata for routing. `ExecutableExpert` is a direct runnable contract. `ExecutionAdapter` is a bridge from a selected module to a backend.

Keep them separate:

- metadata helps the router select modules
- direct executors produce `ExpertResult` values from a task and context
- adapters normalize backend integration through `ExecutionRequest`
- real tools or models can be added later without changing routing metadata

## Add a Demo Executor

```python
from grona import ExpertResult

class MyExecutor:
    module_name = "my-module"

    def execute(self, task, context_items):
        return ExpertResult(
            module_name=self.module_name,
            task=task,
            summary="Prepared a deterministic demo outline.",
            details=("Inspect the focused context.",),
            confidence=0.7,
            metadata={"executor_kind": "deterministic_demo"},
        )
```

Register it with `ExpertExecutorRegistry` and pass the registry to `Orchestrator`.

## Add an Execution Adapter

Use an adapter when you want a backend bridge instead of a direct executor:

```python
from grona import ExecutionRequest, ExpertResult, PythonFunctionAdapter

def handler(request: ExecutionRequest) -> ExpertResult:
    return ExpertResult(
        module_name=request.module_name,
        task=request.task,
        summary="Prepared a deterministic adapter result.",
        details=("No external tools were called.",),
        confidence=0.6,
    )

adapter = PythonFunctionAdapter(
    name="my-function-adapter",
    supported_modules=("my-module",),
    handler=handler,
)
```

Register it with `ExecutionAdapterRegistry` and pass the registry to `Orchestrator`. If both an executor registry and adapter registry are provided, the executor registry takes precedence.

## Run Demo Execution

```bash
python -m grona "Diagnose engine overheating" --orchestrate --use-demo-memory --execute-demo-experts
python -m grona "Review security logs" --orchestrate --use-demo-adapters
```

## Run Tests

```bash
pip install -e .[dev]
pytest
ruff check .
```

## What Not to Add Yet

Do not add these until the execution and adapter interfaces have stronger tests and real requirements:

- OpenAI API calls
- Ollama integration
- external APIs
- web servers
- vector databases
- SQL databases
- production task queues
- subprocess or shell execution
- sandboxing claims
- real cybersecurity scanning
- real document or media processing
- hidden global memory
- claims that deterministic demo executors or adapters are real AI reasoning

The current execution layer is a proof of contract, not production execution.
