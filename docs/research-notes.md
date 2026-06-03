# Research Notes

Grona explores sparse modular AI systems inspired by grape-cluster-like expert activation. These notes are conceptual and intentionally honest about what the project does not solve yet.

## Working Hypothesis

A useful AI assistant does not need to activate every capability for every request. If modules have clear metadata, scoped memory, inspectable context boundaries, visible orchestration, typed execution contracts, backend adapters, tool boundaries, and safety policy checks, a router can activate a small relevant subset and keep the rest dormant.

## Expert Execution Interface

The execution interface separates routing metadata from runnable behavior.

- `ExpertModule` describes an available grape for routing.
- `ExecutableExpert` is a direct contract for a working grape that can respond to a task and focused context.
- `ExpertResult` gives the orchestrator a consistent result shape.

The current executors are deterministic demos. They produce summaries and detail bullets from the task and context. They are not real AI reasoning, tool use, scanning, retrieval, or media analysis.

## Execution Adapters

Execution adapters add a backend-oriented layer.

- `ExecutionRequest` normalizes task, module, context, and metadata.
- `ExecutionAdapter` bridges a selected module to a backend.
- `ExecutionAdapterRegistry` lets orchestration find an adapter by module name.

Future adapters may wrap local Python functions, scripts, shell tools, local LLMs, code analyzers, document processors, media analyzers, or security scanners.

## Tool Adapter Prototype

Tool adapters model future tool use without performing it.

- `ToolSpec` describes the mock tool and its safety-relevant metadata.
- `ToolRequest` captures the selected task, inputs, request source, and metadata.
- `ToolResult` provides a deterministic result shape for demos, tests, and CLI display.
- `ToolAdapter` defines how an adapter plans a `ToolAction` and returns a result.
- `MockToolAdapter` provides deterministic mock behavior only.
- `ToolRegistry` makes tool discovery explicit.
- `SafeToolRunner` evaluates the planned action through `SafetyPolicy` before returning a result.

The current mock tools do not read files, write files, run commands, start subprocesses, call networks, use external APIs, or invoke real scanners. They make future integration points visible and testable.

## Safety Policy Layer

The safety layer asks policy questions before future tools exist:

- Is this action allowed?
- Is it risky, destructive, or unknown?
- Is it read-only?
- Should it remain dry-run only?
- What confirmation would be required?
- Why was it allowed or blocked?

`ToolAction` is a planned action, not execution. `PolicyDecision` is the reasoned result of policy evaluation. `ExecutionPlan` groups planned actions and decisions for an `ExecutionRequest`. `SafeExecutionAdapter` wraps an adapter and turns policy outcomes into `ExpertResult` values. `SafeToolRunner` applies the same policy idea to mock tool adapters.

This fits the grape-cluster metaphor as protective skin around risky grapes. A module being selected should not automatically grant permission to run tools.

## Why Deterministic Safety Planning Matters

Safety planning makes future execution testable before real tools are introduced. It lets Grona validate questions such as:

- Did the adapter plan the expected action type?
- Did the policy block destructive or critical actions?
- Did medium-risk actions become dry-run plans?
- Were required confirmations visible?
- Did orchestrator metadata expose planned, allowed, blocked, dry-run, and mock tool counts?
- Did a selected module get a suitable mock tool result without hidden side effects?

## Current Limits

- No real AI expert execution yet.
- No external tools yet.
- No shell execution, subprocess usage, network calls, or sandboxing yet.
- No process isolation or filesystem isolation.
- No real filesystem tool execution.
- No OpenAI API or Ollama integration.
- No vector database, SQL database, web server, or external API.
- No production orchestration.
- Demo executors, adapters, tool adapters, and safety policies are deterministic proof-of-contract implementations.

## Future Safety Work

Before adding real execution, Grona needs explicit designs for subprocess control, sandboxing, file access boundaries, network access boundaries, secrets handling, audit logs, user confirmation flows, and rollback or recovery expectations.

## Near-Term Experiments

### Execution Trace Review

Compare selected modules, context items, expert results, adapter backend metadata, mock tool results, and safety decisions for the same task. Use mismatches to improve routing metadata, memory records, executor details, adapter contracts, tool specs, or policy defaults.

### Missing Backend Handling

Keep missing executors, adapters, and tool adapters visible and non-fatal. A sparse system should degrade clearly rather than hiding gaps.

### Feedback on Safety Outcomes

Later feedback records may include whether safety decisions were useful, too strict, or too permissive.
