# Changelog

## Unreleased

### Added

- Deterministic GrowthEngine MVP for Growth Lab recommendations.
- `GrowthDecision`, `GrowthPlan`, `GrowthEngineConfig`, and `GrowthEngine`.
- `memory_records_from_growth_plan()` bridge from GrowthPlan decisions into memory records.
- Demo GrowthEngine seeds and `create_demo_growth_plan()` helper.
- CLI `--growth-engine-demo` for deterministic growth planning output.
- `examples/growth_engine_demo.py`.
- GrowthEngine deterministic tests and documentation updates.
- Growth Lab deterministic GrapeNode and GrapeCluster structures.
- `GrapeAssignment` traces and deterministic `GrapeClusterer` confidence scoring.
- `memory_records_from_grape_clusters()` bridge from reviewed clusters into memory records.
- CLI `--grape-demo` for deterministic Growth Lab cluster creation output.
- `examples/grape_cluster_demo.py`.
- Growth Lab deterministic KnowledgeSeed review pipeline.
- `NormalizedKnowledge`, `DuplicateCheckResult`, `ConflictCheckResult`, and `SeedReviewDecision`.
- `KnowledgeDeduplicator`, `KnowledgeConflictDetector`, and `KnowledgeReviewPipeline`.
- CLI `--growth-review-demo` for deterministic validation, duplicate, conflict, and review output.
- `examples/knowledge_review_demo.py`.
- Growth Lab KnowledgeSeed validation foundation.
- `KnowledgeSource`, `KnowledgeSeed`, `ValidationResult`, and `KnowledgeValidator`.
- Deterministic demo knowledge sources and seeds.
- Conversion helpers from `DocumentChunk` and `ToolResult` into raw knowledge seeds.
- CLI `--growth-demo` for deterministic seed validation output.
- `examples/knowledge_seed_demo.py`.
- Growth Lab documentation.
- Public project polish for the v0.1.0 prototype preparation pass.
- README landing-page structure with badges, architecture diagram, quickstart, feature map, and documentation links.
- Project vision document for Growth Lab, KnowledgeSeed, GrapeCluster, GrowthEngine, and related research directions.
- Future v0.1.0-prototype release notes.
- Contributing guide, security note, issue templates, and pull request template.
- Explicit MIT license file.

## v0.1.0-prototype

Planned first public prototype milestone. See `docs/release-notes-v0.1.0-prototype.md`.
