# v0.1.0-prototype Release Notes

These notes describe the intended first public prototype milestone. They do not create a GitHub release by themselves.

## Included

- Explainable module routing with selected and skipped modules.
- `ExpertModule`, `ModuleRegistry`, `Router`, and `RoutingDecision`.
- Feedback records and feedback-informed adaptive routing.
- Memory modules and deterministic keyword memory.
- In-memory document ingestion into chunks and memory records.
- Growth Lab seed validation foundation with `KnowledgeSource`, `KnowledgeSeed`, `ValidationResult`, and `KnowledgeValidator`.
- Growth Lab seed review foundation with deterministic normalization, duplicate checks, potential conflict checks, and review decisions.
- Growth Lab grape cluster foundation with `GrapeNode`, `GrapeCluster`, `GrapeAssignment`, and `GrapeClusterer`.
- Growth Lab GrowthEngine MVP with `GrowthDecision`, `GrowthPlan`, `GrowthEngineConfig`, and `GrowthEngine`.
- Deterministic bridge from grape clusters and growth plans into memory records.
- Expert-candidate recommendations for sufficiently strong deterministic clusters.
- Conversion helpers from document chunks and mock tool results into raw knowledge seeds.
- `ContextBuilder`, `Orchestrator`, and `OrchestrationResult`.
- Deterministic demo expert executors.
- Execution adapter contracts and deterministic demo adapters.
- Safety policy planning for future tool actions.
- Mock tool adapters and safe mock tool runner.
- Workspace profiles and lightweight workspace config objects.
- CLI examples, demo scripts, tests, CI, and public documentation.

## Intentionally Not Included

- Real LLM integration.
- Real donor model integration.
- Real tool execution.
- Shell commands, subprocesses, filesystem tools, network tools, or external APIs.
- Real sandboxing or process isolation.
- Filesystem crawling, PDF parsing, OCR, embeddings, vector search, or database-backed memory.
- Semantic clustering or embedding-backed cluster assignment.
- Web fact-checking, temporal freshness checks, semantic deduplication, or automatic truth resolution.
- LLM-based contradiction detection or external evidence lookup.
- Autonomous self-training, automatic expert growth, training, model weights, or training-data export.
- Automatic mutation from GrowthEngine decisions into memory, modules, clusters, routing, or tools.
- Persisted workspace directories, seed stores, cluster stores, growth plan stores, or external config files.
- Production orchestration, production config management, or deployment guidance.

## Try the CLI

```bash
pip install -e .
python -m grona "Review firewall logs for suspicious port scans"
python -m grona "Diagnose engine overheating" --workspace automotive
python -m grona "Review this Python script for security issues" --workspace cybersecurity
python -m grona "Plan MotionCam RAW workflow" --workspace media
python -m grona --growth-demo
python -m grona --growth-review-demo
python -m grona --grape-demo
python -m grona --growth-engine-demo
```

Run tests:

```bash
pip install -e .[dev]
pytest
ruff check .
```

## Known Limitations

- Routing and memory retrieval are deterministic keyword/domain prototypes.
- Demo executors and adapters are not real AI.
- Safety policy is a planning layer, not a sandbox.
- Mock tools return deterministic mock output only.
- Workspaces are built in and in memory.
- KnowledgeSeed validation is deterministic scoring, not truth verification.
- KnowledgeSeed review is deterministic duplicate and potential conflict detection, not fact-checking.
- GrapeCluster creation is deterministic domain and keyword-overlap grouping, not semantic clustering.
- GrowthEngine is deterministic recommendation logic, not autonomous learning or automatic mutation.
- Feedback adjusts scores in small bounded ways; it is not model training.

## Next Planned Areas

- Growth Lab seed storage and review trace persistence.
- KnowledgeSeed promotion rules into memory candidates.
- GrapeCluster persistence and manual cluster review status.
- GrowthEngine plan persistence and human approval status.
- KnowledgeValidator freshness and workspace relevance checks.
- BenchmarkSuite for repeatable routing, seed validation, seed review, cluster assignment, growth decision, and orchestration evaluation.
- Optional DonorModelAdapter and LMStudioAdapter experiments.
- TrainingDataExporter for validated traces and specialized expert data.
