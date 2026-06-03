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

## Phase 2: Feedback Layer and Route History

- Add `FeedbackRecord` for storing route decisions and optional outcomes.
- Add in-memory and JSONL feedback stores.
- Add simple route history summaries by module, confidence, and success/failure counts.
- Keep feedback passive unless adaptive routing is explicitly enabled.
- Use route history to inspect which branches and modules appear useful.

## Phase 3: Feedback-Informed Adaptive Routing

- Add opt-in adaptive routing configuration.
- Build per-module feedback stats from route history.
- Apply small bounded boosts for positive history and penalties for negative history.
- Preserve base scores, final scores, and explanations in routing decisions.
- Prevent feedback history from selecting modules with no base relevance.
- Keep this as transparent deterministic scoring, not neural learning.

## Phase 4: Real Local Tools and Modules

- Replace selected mock modules with simple local tools.
- Add scripts for code inspection, file search, document parsing, or media metadata extraction.
- Keep tool interfaces small and explicit.
- Track module cost, latency, and failure modes.

## Phase 5: Memory and Feedback Integration

- Introduce module-specific memory stores.
- Experiment with local text indexes, SQL, or structured notes.
- Store which routes worked, failed, or needed human correction.
- Use feedback to design better routing rules without hiding decisions.

## Phase 6: Local LLM Integration

- Add optional local LLM modules.
- Route only selected tasks to LLM-backed experts.
- Compare local model behavior against script/tool modules.
- Keep prompts scoped to route-relevant context.

## Phase 7: Learned Routing Experiments

- Experiment with learned or semi-learned routing scores only after deterministic baselines are understood.
- Add route confidence calibration.
- Penalize repeated over-selection of the same modules when diversity matters.
- Explore hierarchical routing: branch first, grape second.
- Evaluate whether feedback improves module selection over time.

## Phase 8: UI and API Layer

- Add a minimal API for submitting tasks and viewing route traces.
- Add a small UI only after the routing and module concepts are stable.
- Show activated modules, skipped modules, context sources, and feedback signals.
- Keep the interface explainable rather than hiding the route.
