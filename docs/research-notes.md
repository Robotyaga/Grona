# Research Notes

Grona explores sparse modular AI systems inspired by grape-cluster-like expert activation. These notes are conceptual and intentionally honest about what the project does not solve yet.

## Working Hypothesis

A useful AI assistant does not need to activate every capability for every request. If modules have clear metadata, scoped memory, inspectable context boundaries, visible orchestration, and a typed execution contract, a router can activate a small relevant subset and keep the rest dormant.

## Expert Execution Interface

The execution interface separates routing metadata from runnable behavior.

- `ExpertModule` describes an available grape for routing.
- `ExecutableExpert` is a contract for a working grape that can respond to a task and focused context.
- `ExpertResult` gives the orchestrator a consistent result shape.

The current executors are deterministic demos. They produce summaries and detail bullets from the task and context. They are not real AI reasoning, tool use, scanning, retrieval, or media analysis.

## Why Deterministic Demo Executors Matter

Demo executors make the orchestration path testable without pretending the system is production-ready. They let the project validate questions such as:

- Did the router select the expected modules?
- Did the context builder provide relevant context?
- Did the orchestrator call only selected executors?
- Were missing executors reported clearly?
- Can results be formatted and inspected?

## Future Expert Adapters

Future executors could wrap local LLMs, scripts, shell tools, retrievers, media analyzers, code analyzers, or cybersecurity scanners. Each adapter should keep the same observable contract and return an `ExpertResult`.

## Current Limits

- No real AI expert execution yet.
- No external tools yet.
- No OpenAI API or Ollama integration.
- No vector database, SQL database, web server, or external API.
- No production orchestration.
- Demo executors are deterministic proof-of-contract implementations.

## Near-Term Experiments

### Execution Trace Review

Compare selected modules, context items, and expert results for the same task. Use mismatches to improve routing metadata, memory records, or executor details.

### Missing Executor Handling

Keep missing executors visible and non-fatal. A sparse system should degrade clearly rather than hiding gaps.

### Feedback on Results

Later feedback records may include whether expert results were useful, not only whether the route looked correct.
