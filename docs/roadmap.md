# Roadmap

Grona should begin as a clear research/prototype project. The roadmap keeps the early system readable before adding heavier infrastructure.

## Phase 0: Concept and Documentation

- Define the grape-cluster architecture metaphor.
- Explain how Grona differs from monolithic AI systems.
- Document the relationship to MoE, sparse activation, RAG, modular agents, and local-first orchestration.
- Establish a lightweight repository structure.

## Phase 1: Mock Router and Module Registry

- Implement `ExpertModule`, `ModuleRegistry`, `Router`, and `RoutingDecision`.
- Use simple keyword/domain matching for the first router.
- Show selected modules, skipped modules, scores, and reasons.
- Add demo tasks across multiple domains.
- Keep the prototype dependency-free.

## Phase 2: Real Local Tools and Modules

- Replace selected mock modules with simple local tools.
- Add scripts for code inspection, file search, document parsing, or media metadata extraction.
- Keep tool interfaces small and explicit.
- Track module cost, latency, and failure modes.

## Phase 3: Memory and Feedback

- Add basic route traces.
- Introduce module-specific memory stores.
- Experiment with local text indexes, SQL, or structured notes.
- Store which routes worked, failed, or needed human correction.
- Use feedback to improve routing rules without hiding decisions.

## Phase 4: Local LLM Integration

- Add optional local LLM modules.
- Route only selected tasks to LLM-backed experts.
- Compare local model behavior against script/tool modules.
- Keep prompts scoped to route-relevant context.

## Phase 5: Adaptive Routing

- Experiment with learned or semi-learned routing scores.
- Add route confidence calibration.
- Penalize repeated over-selection of the same modules when diversity matters.
- Explore hierarchical routing: branch first, grape second.
- Evaluate whether feedback improves module selection over time.

## Phase 6: UI and API Layer

- Add a minimal API for submitting tasks and viewing route traces.
- Add a small UI only after the routing and module concepts are stable.
- Show activated modules, skipped modules, context sources, and feedback signals.
- Keep the interface explainable rather than hiding the route.
