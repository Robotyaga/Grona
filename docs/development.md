# Development Notes

Grona is an early research prototype. Keep the code small, readable, deterministic, and honest about what it does.

## Repository Structure

```text
src/grona/
|-- adaptive.py      Feedback-informed score adjustment helpers
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

`ExpertModule` is metadata for routing. `ExecutableExpert` is a runnable adapter contract.

Keep them separate:

- metadata helps the router select modules
- executors produce `ExpertResult` values from a task and context
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

## Run Demo Execution

```bash
python -m grona "Diagnose engine overheating" --orchestrate --use-demo-memory --execute-demo-experts
```

## Run Tests

```bash
pip install -e .[dev]
pytest
ruff check .
```

## What Not to Add Yet

Do not add these until the execution interface has stronger tests and real requirements:

- OpenAI API calls
- Ollama integration
- external APIs
- web servers
- vector databases
- SQL databases
- production task queues
- shell execution
- real cybersecurity scanning
- hidden global memory
- claims that deterministic demo executors are real AI reasoning

The current execution layer is a proof of contract, not production execution.
