# Roadmap

Grona should stay readable before adding heavier infrastructure. The roadmap is intentionally staged so public polish, tests, safety boundaries, and research questions stay ahead of larger integrations.

## Documentation Map

- [Project vision](project-vision.md)
- [Architecture](architecture.md)
- [Workspace profiles](workspaces.md)
- [Research notes](research-notes.md)
- [v0.1.0 prototype release notes](release-notes-v0.1.0-prototype.md)

## Completed Prototype Foundation

The repository already has the first deterministic foundation:

- `ExpertModule`, `ModuleRegistry`, `Router`, and `RoutingDecision`
- feedback records and adaptive routing
- memory modules and keyword memory
- in-memory document ingestion
- `ContextBuilder`, `Orchestrator`, and `OrchestrationResult`
- deterministic expert executors
- execution adapters
- safety policy planning
- mock tool adapters and safe mock runner
- workspace profiles and workspace-aware CLI
- examples, tests, CI, and documentation

## v0.1.0-prototype Polish

Goal: make the public repository coherent, inspectable, and easy to evaluate.

- Polish README as a public landing page.
- Add architecture diagrams and documentation navigation.
- Add project vision and future release notes.
- Add contribution, security, changelog, issue template, and PR template files.
- Keep the prototype honest about what is not implemented.

## Growth Lab

Goal: create a controlled environment for experimenting with growth of modular AI systems.

Potential work:

- scenario fixtures for routing, memory, workspaces, and safety decisions
- repeatable traces for how tasks move through the cluster
- clear experiment records for what changed and why
- no real tool execution until safety design is stronger

## KnowledgeSeed

Goal: represent external structured knowledge before it becomes training data or durable expert behavior.

Potential fields:

- source and provenance
- domain and workspace relevance
- content summary or structured facts
- confidence and validation status
- links to feedback, routes, or examples

## KnowledgeValidator

Goal: test whether imported or generated knowledge should influence a workspace.

Possible checks:

- source visibility
- consistency with existing seeds
- usefulness for routing or context
- safety concerns
- benchmark impact
- human review status

## GrapeCluster

Goal: group related expert modules, memory sources, tool profiles, safety defaults, and routing behavior into a coherent cluster.

This would extend workspace profiles into richer modular arrangements while keeping the current deterministic profile layer as the simple foundation.

## GrowthEngine

Goal: propose controlled changes to modules, seeds, routing metadata, or feedback rules.

The GrowthEngine should be conservative and auditable. It should produce proposals and traces, not silently mutate core behavior.

## BenchmarkSuite

Goal: make route quality and orchestration behavior measurable.

Potential benchmark types:

- routing selection tests
- workspace profile comparison tests
- context assembly relevance tests
- safety policy edge cases
- mock tool planning tests
- regression tests for Growth Lab experiments

## DonorModelAdapter / LMStudioAdapter

Goal: optionally use model outputs as proposal sources.

A donor model or local LM Studio model could suggest labels, summaries, seeds, or examples. Those outputs should be validated before they become durable knowledge or training data.

## TrainingDataExporter

Goal: export validated traces, corrections, examples, and knowledge seeds for future specialized expert training.

This should preserve provenance and validation metadata instead of flattening everything into opaque text.

## Future Local LLM Integration

Goal: add optional local LLM-backed modules only after routing, safety, context, and evaluation contracts are strong enough.

Near-term boundaries:

- no production claims
- no hidden network calls
- no secrets in workspace profiles
- no unrestricted tool use
- prompt/context should remain route-scoped and inspectable

## Later Product Surfaces

UI/API layers should come after the architecture contracts are stable enough to display useful traces:

- active workspace profile
- selected modules and scores
- context sources
- expert results
- mock tool results
- safety decisions
- feedback signals
