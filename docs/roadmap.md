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
- Growth Lab grape node, grape cluster, assignment, and memory bridge primitives
- Growth Lab deterministic `GrowthEngine` recommendation MVP
- public README polish and project documentation
- examples, tests, and CI

## v0.1.0-prototype Polish

Goal: make the public repository coherent, inspectable, and easy to evaluate.

Status: complete as public project preparation.

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

## Growth Lab: GrapeCluster Foundation

Goal: represent candidate groupings after reviewed seeds become safe enough to organize.

Current foundation:

- `GrapeNode`
- `GrapeCluster`
- `GrapeAssignment`
- `GrapeClusterer`
- deterministic cluster confidence
- explicit assignment and skip reasons
- `memory_records_from_grape_clusters()` bridge
- CLI `--grape-demo`
- `examples/grape_cluster_demo.py`
- deterministic tests

This layer is deterministic keyword/domain grouping only. It does not add embeddings, vector search, autonomous expert growth, persisted clusters, training, or model weights.

## Growth Lab: GrowthEngine MVP

Goal: recommend controlled next actions after seed review and grape clustering.

Current foundation:

- `GrowthDecision`
- `GrowthPlan`
- `GrowthEngineConfig`
- `GrowthEngine`
- `memory_records_from_growth_plan()` bridge
- CLI `--growth-engine-demo`
- `examples/growth_engine_demo.py`
- deterministic tests

The MVP recommends actions such as seed promotion, duplicate merge, quarantine, rejection, candidate cluster creation, cluster strengthening, cluster review, memory-record preparation, and expert-candidate suggestion.

It does not mutate inputs, persist plans, train models, create experts, resolve truth, use embeddings, call LLMs, call the web, or change model weights.

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

## GrapeCluster Next Steps

Goal: connect candidate clusters to richer modular arrangements while preserving review traces.

Possible next work:

- persisted cluster stores
- cluster versioning
- manual cluster review status
- workspace relevance scoring for clusters
- benchmark impact checks before promotion
- controlled promotion from cluster summaries into durable memory candidates

## GrowthEngine Next Steps

Goal: make growth proposals more reviewable and measurable while keeping the engine conservative.

Possible next work:

- persisted growth plan traces
- manual approval status for growth decisions
- workspace-scoped growth plans
- benchmark impact checks before accepting recommendations
- stricter policy gates for expert-candidate proposals
- export of approved decisions into future training-data candidates

GrowthEngine should keep producing proposals and traces, not silently mutate core behavior.

## BenchmarkSuite

Goal: make route quality and orchestration behavior measurable.

Potential benchmark types:

- routing selection tests
- workspace profile comparison tests
- seed validation tests
- seed deduplication and potential conflict tests
- grape cluster assignment tests
- GrowthEngine decision tests
- context assembly relevance tests
- safety policy edge cases
- mock tool planning tests
- regression tests for Growth Lab experiments

## DonorModelAdapter / LMStudioAdapter

Goal: optionally use model outputs as proposal sources.

A donor model or local LM Studio model could suggest labels, summaries, seeds, or examples. Those outputs should be validated, reviewed, optionally assigned to candidate clusters, and evaluated by GrowthEngine before they become durable knowledge or training data.

## TrainingDataExporter

Goal: export validated traces, corrections, examples, and knowledge seeds for future specialized expert training.

This should preserve provenance and validation metadata instead of flattening everything into opaque text.

## Future Local LLM Integration

Goal: add optional local LLM-backed modules only after routing, safety, context, validation, review, clustering, growth planning, and evaluation contracts are strong enough.

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
- grape cluster assignment status
- GrowthEngine decision status
- context sources
- expert results
- mock tool results
- safety decisions
- feedback signals
