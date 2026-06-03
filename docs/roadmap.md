# Roadmap

Grona should stay readable before adding heavier infrastructure. The roadmap is intentionally staged so public polish, tests, safety boundaries, and research questions stay ahead of larger integrations.

## Documentation Map

- [Project vision](project-vision.md)
- [Architecture](architecture.md)
- [Growth Lab](growth-lab.md)
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
- Growth Lab seed validation and deterministic review primitives
- public README polish and project documentation
- examples, tests, and CI

## v0.1.0-prototype Polish

Goal: make the public repository coherent, inspectable, and easy to evaluate.

Status: complete as public project preparation.

- Polish README as a public landing page.
- Add architecture diagrams and documentation navigation.
- Add project vision and future release notes.
- Add contribution, security, changelog, issue template, and PR template files.
- Keep the prototype honest about what is not implemented.

## Growth Lab: KnowledgeSeed Validation Foundation

Goal: create the first deterministic layer for raw knowledge before promotion.

Current foundation:

- `KnowledgeSource`
- `KnowledgeSeed`
- `ValidationResult`
- `KnowledgeValidator`
- conversions from `DocumentChunk` and `ToolResult`
- deterministic demo seeds
- CLI `--growth-demo`
- example and tests

This layer does not fact-check, train models, persist seeds, or grow clusters automatically.

## Growth Lab: KnowledgeSeed Review Foundation

Goal: stop raw seeds from being blindly promoted or clustered.

Current foundation:

- `NormalizedKnowledge`
- `DuplicateCheckResult`
- `ConflictCheckResult`
- `SeedReviewDecision`
- `KnowledgeDeduplicator`
- `KnowledgeConflictDetector`
- `KnowledgeReviewPipeline`
- CLI `--growth-review-demo`
- `examples/knowledge_review_demo.py`
- deterministic tests

This layer detects exact duplicates, simple near duplicates, and conservative potential conflicts. It does not perform semantic embedding search, LLM contradiction detection, web fact-checking, external evidence lookup, or automatic truth resolution.

## KnowledgeSeed Next Steps

Goal: represent external structured knowledge before it becomes training data or durable expert behavior.

Next possible work:

- deterministic seed stores
- seed versioning
- source provenance summaries
- workspace relevance scoring
- promotion rules from reviewed seed to memory candidate
- persisted review traces

## KnowledgeValidator

Goal: test whether imported or generated knowledge should influence a workspace.

Possible next checks:

- source visibility
- temporal freshness flags
- usefulness for routing or context
- safety concerns
- benchmark impact
- human review status

## GrapeCluster

Goal: group related expert modules, memory sources, tool profiles, safety defaults, and routing behavior into a coherent cluster.

This would extend workspace profiles into richer modular arrangements while keeping the current deterministic profile layer as the simple foundation.

Reviewed seeds can later become candidates for cluster nutrients, but the current review pipeline only recommends next steps.

## GrowthEngine

Goal: propose controlled changes to modules, seeds, routing metadata, or feedback rules.

The GrowthEngine should be conservative and auditable. It should produce proposals and traces, not silently mutate core behavior.

## BenchmarkSuite

Goal: make route quality and orchestration behavior measurable.

Potential benchmark types:

- routing selection tests
- workspace profile comparison tests
- seed validation tests
- seed deduplication and potential conflict tests
- context assembly relevance tests
- safety policy edge cases
- mock tool planning tests
- regression tests for Growth Lab experiments

## DonorModelAdapter / LMStudioAdapter

Goal: optionally use model outputs as proposal sources.

A donor model or local LM Studio model could suggest labels, summaries, seeds, or examples. Those outputs should be validated and reviewed before they become durable knowledge or training data.

## TrainingDataExporter

Goal: export validated traces, corrections, examples, and knowledge seeds for future specialized expert training.

This should preserve provenance and validation metadata instead of flattening everything into opaque text.

## Future Local LLM Integration

Goal: add optional local LLM-backed modules only after routing, safety, context, validation, review, and evaluation contracts are strong enough.

Near-term boundaries:

- no production claims
- no hidden network calls
- no secrets in workspace profiles or seeds
- no unrestricted tool use
- prompt/context should remain route-scoped and inspectable

## Later Product Surfaces

UI/API layers should come after the architecture contracts are stable enough to display useful traces:

- active workspace profile
- selected modules and scores
- knowledge seed validation and review status
- context sources
- expert results
- mock tool results
- safety decisions
- feedback signals
