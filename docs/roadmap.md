# Roadmap

Grona should stay readable before adding heavier infrastructure.

## Phase 0: Concept and Documentation

- Define the grape-cluster architecture metaphor.
- Explain sparse modular activation.
- Establish a lightweight repository structure.

## Phase 1: Mock Router and Module Registry

- Implement `ExpertModule`, `ModuleRegistry`, `Router`, and `RoutingDecision`.
- Use simple keyword/domain matching.
- Show selected modules, skipped modules, scores, and reasons.

## Phase 2: Feedback Layer and Route History

- Add `FeedbackRecord` and simple route history stores.
- Summarize selected modules, confidence, and success/failure counts.

## Phase 3: Feedback-Informed Adaptive Routing

- Add opt-in adaptive routing configuration.
- Apply small bounded boosts or penalties from feedback history.
- Keep this deterministic, not neural learning.

## Phase 4: Context Builder and Orchestration Foundation

- Add `ContextItem`, `ContextBuilder`, `Orchestrator`, and `OrchestrationResult`.
- Keep orchestration as a structured handoff.

## Phase 5: Memory Modules and Retrieval Stubs

- Add `MemoryRecord`, `MemoryModule`, and deterministic keyword memory.
- Allow `ContextBuilder` to query relevant memory modules only.
- Keep this keyword retrieval, not embeddings or semantic search.

## Phase 6: Expert Execution Interface

- Add `ExpertResult` and `ExecutableExpert`.
- Add `ExpertExecutorRegistry`.
- Add deterministic demo executors for default modules.
- Allow `Orchestrator` to optionally execute selected demo experts.
- Keep this as proof of contract, not real AI execution.

## Phase 7: Real Local Tools and Modules

- Replace selected mock/demo modules with simple local tools.
- Add scripts for code inspection, file search, document parsing, or media metadata extraction.
- Keep tool interfaces small and explicit.

## Phase 8: Memory and Feedback Integration

- Introduce module-specific local memory stores.
- Experiment with local text indexes or structured notes.
- Use feedback to evaluate routes and execution results.

## Phase 9: Local LLM Integration

- Add optional local LLM modules.
- Route only selected tasks to LLM-backed experts.
- Keep prompts scoped to route-relevant context.

## Phase 10: Learned Routing Experiments

- Experiment with learned routing only after deterministic baselines are understood.
- Add route confidence calibration.
- Explore hierarchical routing: branch first, grape second.

## Phase 11: UI and API Layer

- Add UI/API only after routing, context, memory, and execution contracts are stable.
- Show route traces, context sources, expert results, and feedback signals.
