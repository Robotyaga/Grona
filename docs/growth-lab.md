# Growth Lab

Growth Lab is the research foundation for future self-growing modular intelligence in Grona.

The long-term idea is:

```text
DatasetSource -> DatasetSample -> KnowledgeSeed -> validation
-> deduplication/conflict checks -> review decision -> grape cluster assignment
-> GrowthEngine recommendations -> memory bridge / expert proposal review
-> feedback -> benchmarks -> optional training data export
```

The current implementation adds deterministic local-first foundations for dataset ingestion, knowledge seeds, validation, review, grape clustering, GrowthEngine recommendations, and BenchmarkSuite measurement.

## Current Structures

Dataset ingestion:

- `DatasetSource`
- `DatasetSample`
- `InstructionDatasetSample`
- `ConversationDatasetSample`
- `AlpacaFormatAdapter`
- `ShareGPTFormatAdapter`

Knowledge review:

- `KnowledgeSource`
- `KnowledgeSeed`
- `ValidationResult`
- `KnowledgeValidator`
- `NormalizedKnowledge`
- `KnowledgeDeduplicator`
- `KnowledgeConflictDetector`
- `KnowledgeReviewPipeline`
- `SeedReviewDecision`

Grape growth:

- `GrapeNode`
- `GrapeCluster`
- `GrapeAssignment`
- `GrapeClusterer`
- `GrowthDecision`
- `GrowthPlan`
- `GrowthEngineConfig`
- `GrowthEngine`

Measurement:

- `BenchmarkCase`
- `BenchmarkRunConfig`
- `BenchmarkResult`
- `BenchmarkReport`
- `BenchmarkSuite`

## BenchmarkSuite In Growth Lab

BenchmarkSuite gives Growth Lab a deterministic way to compare before/after states. It can run small demo tasks against baseline routing, demo memory, dataset-derived seeds, grape cluster memory, GrowthEngine decisions, and orchestration.

This helps answer local prototype questions:

- Did Grona select the expected modules?
- Did route-scoped context contain expected keywords?
- Did GrowthEngine produce relevant traces?
- Did dataset ingestion and grape clusters improve available context?
- Can a change be compared against baseline routing?

It does not judge natural-language answers or prove model quality.

## CLI Demos

```bash
python -m grona --growth-demo
python -m grona --growth-review-demo
python -m grona --grape-demo
python -m grona --growth-engine-demo
python -m grona --dataset-demo
python -m grona --benchmark-demo
```

## Examples

```bash
python examples/knowledge_seed_demo.py
python examples/knowledge_review_demo.py
python examples/grape_cluster_demo.py
python examples/growth_engine_demo.py
python examples/dataset_ingestion_demo.py
python examples/benchmark_demo.py
```

## Current Limitations

- No autonomous self-training.
- No automatic expert creation.
- No model weights.
- No real dataset downloads.
- No Hugging Face integration or `datasets` dependency.
- No JSONL file loader or Parquet reader.
- No large dataset files or generated dataset artifacts.
- No web fact-checking.
- No temporal freshness checks.
- No semantic embeddings.
- No vector database.
- No LLM-based contradiction detection.
- No external judge model.
- No external evidence lookup.
- No automatic truth resolution.
- No real donor model integration.
- No persisted seed, cluster, growth plan, or benchmark store.
- No semantic clustering.
- No automatic promotion from cluster to trusted memory or expert behavior.
- No production knowledge-quality or benchmark-accuracy claims.

The current Growth Lab layer is a deterministic heuristic prototype for future experiments.
