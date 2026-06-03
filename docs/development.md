# Development Notes

Grona is an early research prototype. Keep the code small, readable, deterministic, and honest about what it does.

## Repository Structure

```text
src/grona/
|-- adaptive.py      Feedback-informed score adjustment helpers
|-- adapters.py      ExecutionRequest, adapters, and adapter registry
|-- cli.py           Routing, orchestration, memory, execution, and safety CLI
|-- context.py       ContextItem and ContextBuilder
|-- decision.py      Routing decision data structures
|-- executor.py      ExpertResult, ExecutableExpert, demo executors
|-- feedback.py      Feedback records and route history stores
|-- memory.py        MemoryRecord and deterministic keyword memory
|-- module.py        ExpertModule routing metadata
|-- orchestrator.py  Orchestrator and OrchestrationResult
|-- registry.py      ModuleRegistry
|-- router.py        Keyword/domain router
`-- safety.py        ToolAction, SafetyPolicy, ExecutionPlan, SafeExecutionAdapter
```

## Metadata vs Execution vs Safety

`ExpertModule` is metadata for routing. `ExecutableExpert` is a direct runnable contract. `ExecutionAdapter` is a bridge from a selected module to a backend. `SafetyPolicy` evaluates planned future tool actions before an adapter backend becomes real.

Keep them separate:

- metadata helps the router select modules
- direct executors produce `ExpertResult` values from a task and context
- adapters normalize backend integration through `ExecutionRequest`
- safety policy evaluates `ToolAction` plans without executing anything
- real tools or models can be added later without changing routing metadata

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

## Add a Safety Plan

Adapters may later expose planned actions. Today, `SafeExecutionAdapter` can evaluate deterministic default plans:

```python
from grona import ExecutionRequest, SafeExecutionAdapter, create_default_adapter_registry
from grona import create_default_safety_policy

adapter = create_default_adapter_registry().get("code-assistant")
safe_adapter = SafeExecutionAdapter(adapter, create_default_safety_policy())
result = safe_adapter.execute(ExecutionRequest("Review code", "code-assistant"))
```

A dry-run plan is only a plan. It must not run shell commands, subprocesses, scanners, file processors, or external APIs.

## Run Demo Execution

```bash
python -m grona "Diagnose engine overheating" --orchestrate --use-demo-memory --execute-demo-experts
python -m grona "Review security logs" --orchestrate --use-demo-adapters
python -m grona "Review security logs" --orchestrate --use-demo-adapters --safe
python -m grona "Review code" --use-demo-adapters --dry-run-tools
```

## Run Tests

```bash
pip install -e .[dev]
pytest
ruff check .
```

## What Not to Add Yet

Do not add these until the execution and safety interfaces have stronger tests and real requirements:

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
- claims that policy evaluation is real isolation
- claims that deterministic demo executors or adapters are real AI reasoning

The current safety layer is policy and planning only, not production execution or sandboxing.
