# Grona

Grona is a lightweight research prototype for a modular sparse AI architecture inspired by grape-cluster-like expert activation.

The core idea is simple: do not activate every capability for every task. Route a task to relevant expert modules, gather focused context from stubs or memory modules, optionally run deterministic demo experts or execution adapters, evaluate planned tool actions with safety policy, and keep the trace visible.

## Architecture Metaphor

- The router chooses relevant branches and grapes.
- Memory modules are small knowledge pockets attached to parts of the cluster.
- The context builder gathers only the information needed by selected grapes.
- The orchestrator coordinates the selected path.
- Demo expert executors are the first tiny working grapes that can return structured results.
- Execution adapters are bridges from selected grapes to future execution backends.
- Safety policy is protective skin around risky grapes before any future tool use.
- The feedback layer remembers which paths worked.
- Adaptive routing slightly adjusts future activation from previous outcomes.

## Current Prototype

The current prototype includes:

- `ExpertModule`: metadata used for routing and module identity.
- `ExecutableExpert`: a lightweight direct execution contract for runnable experts.
- `ExecutionAdapter`: a bridge from selected modules to future execution backends.
- `ExecutionRequest`: normalized task, module, context, and metadata input for adapters.
- `ToolAction`: a planned future tool action that is never executed by this prototype.
- `SafetyPolicy` and `PolicyDecision`: deterministic policy evaluation for planned actions.
- `ExecutionPlan` and `SafeExecutionAdapter`: dry-run planning around execution adapters.
- `ExpertResult`: structured deterministic output from executors or adapters.
- deterministic demo executors and deterministic demo adapters for default modules.
- `Router`, `RoutingDecision`, feedback, adaptive routing, memory modules, context building, orchestration, CLI, examples, tests, and CI.

The demo executors, adapters, and safety layer are not real AI or sandboxing. They are deterministic proof-of-contract implementations.

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
python examples/safety_policy_demo.py
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

Run deterministic demo adapters:

```bash
python -m grona "Review this Python script for security issues" --orchestrate --use-demo-adapters
```

Evaluate adapter planning with safety policy:

```bash
python -m grona "Review this project for security issues" --orchestrate --use-demo-adapters --safe
```

Force planned tool actions into dry-run mode:

```bash
python -m grona "Review this project" --use-demo-adapters --dry-run-tools
```

`--execute-demo-experts` and `--use-demo-adapters` imply orchestration if `--orchestrate` is omitted. If both execution options are supplied, explicit demo experts take precedence over adapters.

## Safety Policy Layer

The safety layer prepares Grona for future local tools without adding real tool execution yet.

- `ToolAction` describes a planned action such as `read_file`, `write_file`, `run_command`, `network_request`, `delete_file`, `modify_system`, or `unknown`.
- `PolicyDecision` explains whether that action is allowed, blocked, dry-run only, or requires confirmation.
- `SafetyPolicy` evaluates actions with conservative defaults.
- `ExecutionPlan` groups a request, planned actions, and policy decisions.
- `SafeExecutionAdapter` wraps an adapter, evaluates planned actions, and returns an `ExpertResult` explaining the safety outcome.

Dry-run means Grona produced and evaluated a plan. It does not mean any shell command, subprocess, external API, scanner, file processor, or sandboxed process ran.

## Run Tests

```bash
pytest
```

Optional linting:

```bash
ruff check .
```

## Current Limitations

- Demo executors and adapters are deterministic stubs, not real AI reasoning.
- The safety layer is policy/planning only, not a real sandbox.
- No process isolation is implemented.
- No shell commands, subprocess execution, sandboxing, or unsafe tools are implemented.
- No external tools are called.
- No OpenAI API, Ollama integration, web server, vector database, SQL database, or external APIs.
- Memory retrieval is keyword/domain overlap only.
- No embeddings or semantic search yet.
- No persistent memory graph yet.
- No production orchestration.

These limits are intentional. Grona is currently a research/prototype foundation for sparse modular AI architecture.
