# v0.1.0-prototype Release Notes

These notes describe the intended first public prototype milestone. They do not create a GitHub release by themselves.

## Included

- Explainable module routing with selected and skipped modules.
- `ExpertModule`, `ModuleRegistry`, `Router`, and `RoutingDecision`.
- Feedback records and feedback-informed adaptive routing.
- Memory modules and deterministic keyword memory.
- In-memory document ingestion into chunks and memory records.
- Growth Lab seed validation foundation with `KnowledgeSource`, `KnowledgeSeed`, `ValidationResult`, and `KnowledgeValidator`.
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
- Web fact-checking, temporal freshness checks, seed deduplication, or conflict resolution.
- Automatic cluster growth, training, model weights, or training-data export.
- Persisted workspace directories, persisted seed stores, or external config files.
- Production orchestration, production config management, or deployment guidance.

## Try the CLI

```bash
pip install -e .
python -m grona "Review firewall logs for suspicious port scans"
python -m grona "Diagnose engine overheating" --workspace automotive
python -m grona "Review this Python script for security issues" --workspace cybersecurity
python -m grona "Plan MotionCam RAW workflow" --workspace media
python -m grona --growth-demo
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
- Feedback adjusts scores in small bounded ways; it is not model training.

## Next Planned Areas

- Growth Lab seed storage, deduplication, and conflict checks.
- KnowledgeSeed promotion rules into memory candidates.
- KnowledgeValidator freshness and workspace relevance checks.
- GrapeCluster and GrowthEngine research prototypes.
- BenchmarkSuite for repeatable routing, seed validation, and orchestration evaluation.
- Optional DonorModelAdapter and LMStudioAdapter experiments.
- TrainingDataExporter for validated traces and specialized expert data.
