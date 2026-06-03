# Grona

Grona is a lightweight research prototype for a modular sparse AI architecture inspired by grape-cluster-like expert activation.

The core idea is simple: do not activate every capability for every task. Route a task to relevant expert modules, gather focused context from stubs or memory modules, optionally run deterministic demo experts or execution adapters, evaluate planned tool and mock tool actions with safety policy, and keep the trace visible.

## Architecture Metaphor

- The router chooses relevant branches and grapes.
- Memory modules are small knowledge pockets attached to parts of the cluster.
- The context builder gathers only the information needed by selected grapes.
- The orchestrator coordinates the selected path.
- Demo expert executors are the first tiny working grapes that can return structured results.
- Execution adapters are bridges from selected grapes to future execution backends.
- Tool adapters are safe mock grapes for testing future tool boundaries.
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
- `ToolSpec`, `ToolRequest`, and `ToolResult`: structured mock tool contracts.
- `ToolAdapter`, `MockToolAdapter`, `ToolRegistry`, and `SafeToolRunner`: deterministic tool adapter prototype with policy checks.
- `ExpertResult`: structured deterministic output from executors, adapters, and tool summaries.
- deterministic demo executors, deterministic demo adapters, and deterministic mock tool adapters for default modules.
- `Router`, `RoutingDecision`, feedback, adaptive routing, memory modules, context building, orchestration, CLI, examples, tests, and CI.

The demo executors, adapters, tool adapters, and safety layer are not real AI, real tooling, or sandboxing. They are deterministic proof-of-contract implementations.

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
python examples/tool_adapter_demo.py
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

Run deterministic mock tool adapters through selected demo adapters:

```bash
python -m grona "Analyze engine overheating symptoms" --use-demo-tools
```

`--execute-demo-experts`, `--use-demo-adapters`, and `--use-demo-tools` imply orchestration if `--orchestrate` is omitted. If both execution options are supplied, explicit demo experts take precedence over adapters. `--use-demo-tools` enables demo adapters, creates the default mock tool registry, and evaluates mock tool plans with the default safety policy.

## Safety Policy Layer

The safety layer prepares Grona for future local tools without adding real tool execution yet.

- `ToolAction` describes a planned action such as `read_file`, `write_file`, `run_command`, `network_request`, `delete_file`, `modify_system`, or `unknown`.
- `PolicyDecision` explains whether that action is allowed, blocked, dry-run only, or requires confirmation.
- `SafetyPolicy` evaluates actions with conservative defaults.
- `ExecutionPlan` groups a request, planned actions, and policy decisions.
- `SafeExecutionAdapter` wraps an adapter, evaluates planned actions, and returns an `ExpertResult` explaining the safety outcome.
- `SafeToolRunner` evaluates a `ToolAdapter` plan before returning a deterministic `ToolResult`.

Dry-run means Grona produced and evaluated a plan. It does not mean any shell command, subprocess, external API, scanner, file processor, real filesystem tool, network operation, or sandboxed process ran.

## Tool Adapter Prototype

The tool adapter layer is intentionally small and safe:

- `ToolSpec` describes a mock tool name, action type, risk, read-only status, and metadata.
- `ToolRequest` describes a selected expert module asking for mock tool help.
- `ToolResult` returns deterministic mock output and includes `to_text()` for display.
- `MockToolAdapter` never touches files, networks, subprocesses, or external APIs.
- `ToolRegistry` supports registration, lookup, listing, action-type search, and metadata search.
- `create_default_tool_registry()` creates mock tools for code, car diagnostics, cybersecurity, media/video, and document search.

This is a boundary prototype for future tool use, not real tool use.

## Run Tests

```bash
pytest
```

Optional linting:

```bash
ruff check .
```

## Current Limitations

- Demo executors, adapters, and mock tool adapters are deterministic stubs, not real AI reasoning.
- The router is keyword/domain based.
- The safety layer is policy/planning only, not a real sandbox.
- No process isolation is implemented.
- No shell commands, subprocess execution, sandboxing, real filesystem tools, or unsafe tools are implemented.
- No external tools, network requests, or external APIs are called.
- No OpenAI API, Ollama integration, web server, vector database, SQL database, or external APIs.
- No learning, adaptive tool execution, or real memory graph yet.
- Memory retrieval is keyword/domain overlap only.
- No embeddings or semantic search yet.
- No production orchestration.

These limits are intentional. Grona is currently a research/prototype foundation for sparse modular AI architecture.
