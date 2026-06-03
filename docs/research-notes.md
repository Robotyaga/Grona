# Research Notes

Grona explores sparse modular AI systems inspired by grape-cluster-like expert activation. These notes are conceptual and intentionally honest about what the project does not solve yet.

## Working Hypothesis

A useful AI assistant does not need to activate every capability for every request. If modules have clear metadata, scoped memory, inspectable context boundaries, visible orchestration, typed execution contracts, and backend adapters, a router can activate a small relevant subset and keep the rest dormant.

## Expert Execution Interface

The execution interface separates routing metadata from runnable behavior.

- `ExpertModule` describes an available grape for routing.
- `ExecutableExpert` is a direct contract for a working grape that can respond to a task and focused context.
- `ExpertResult` gives the orchestrator a consistent result shape.

The current executors are deterministic demos. They produce summaries and detail bullets from the task and context. They are not real AI reasoning, tool use, scanning, retrieval, or media analysis.

## Execution Adapters

Execution adapters add a second, more backend-oriented layer.

- `ExecutionRequest` normalizes task, module, context, and metadata.
- `ExecutionAdapter` bridges a selected module to a backend.
- `ExecutionAdapterRegistry` lets orchestration find an adapter by module name.

Adapters are separate from `ExpertModule` because routing metadata should not know how a backend runs. They are separate from demo `ExecutableExpert` classes because future backends may need different wrappers for local Python functions, scripts, shell tools, local LLMs, code analyzers, document processors, media analyzers, or security scanners.

The current adapters are deterministic. They do not run subprocesses, call shell commands, invoke LLMs, query external APIs, inspect local files, or perform real scanning.

## Why Deterministic Demo Executors and Adapters Matter

Demo executors and adapters make the orchestration path testable without pretending the system is production-ready. They let the project validate questions such as:

- Did the router select the expected modules?
- Did the context builder provide relevant context?
- Did the orchestrator call only selected executors or adapters?
- Was the backend choice visible in metadata and formatted output?
- Were missing executors or adapters reported clearly?
- Can results be formatted and inspected?

## Future Expert Backends

Future adapters could wrap local LLMs, scripts, shell tools, retrievers, media analyzers, code analyzers, or cybersecurity scanners. Each adapter should keep the same observable contract and return an `ExpertResult`.

Before adding real execution, Grona needs explicit safety design for subprocesses, sandboxing, file access, network access, secrets handling, and user consent.

## Current Limits

- No real AI expert execution yet.
- No external tools yet.
- No shell execution, subprocess usage, or sandboxing yet.
- No OpenAI API or Ollama integration.
- No vector database, SQL database, web server, or external API.
- No production orchestration.
- Demo executors and adapters are deterministic proof-of-contract implementations.

## Near-Term Experiments

### Execution Trace Review

Compare selected modules, context items, expert results, and adapter backend metadata for the same task. Use mismatches to improve routing metadata, memory records, executor details, or adapter contracts.

### Missing Backend Handling

Keep missing executors and adapters visible and non-fatal. A sparse system should degrade clearly rather than hiding gaps.

### Feedback on Results

Later feedback records may include whether expert results were useful, not only whether the route looked correct.
