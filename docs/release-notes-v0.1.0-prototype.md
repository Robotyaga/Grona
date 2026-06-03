# v0.1.0-prototype Release Notes

These notes describe the intended first public prototype milestone. They do not create a GitHub release by themselves.

## Included

- Explainable module routing with selected and skipped modules.
- `ExpertModule`, `ModuleRegistry`, `Router`, and `RoutingDecision`.
- Feedback records and feedback-informed adaptive routing.
- Memory modules and deterministic keyword memory.
- In-memory document ingestion into chunks and memory records.
- `ContextBuilder`, `Orchestrator`, and `OrchestrationResult`.
- Deterministic demo expert executors.
- Execution adapter contracts and deterministic demo adapters.
- Safety policy planning for future tool actions.
- Mock tool adapters and safe mock tool runner.
- Workspace profiles and lightweight workspace config objects.
- CLI examples, demo scripts, tests, CI, and public documentation.

## Intentionally Not Included

- Real LLM integration.
- Real tool execution.
- Shell commands, subprocesses, filesystem tools, network tools, or external APIs.
- Real sandboxing or process isolation.
- Filesystem crawling, PDF parsing, OCR, embeddings, vector search, or database-backed memory.
- Persisted workspace directories or external config files.
- Production orchestration, production config management, or deployment guidance.

## Try the CLI

```bash
pip install -e .
python -m grona "Review firewall logs for suspicious port scans"
python -m grona "Diagnose engine overheating" --workspace automotive
python -m grona "Review this Python script for security issues" --workspace cybersecurity
python -m grona "Plan MotionCam RAW workflow" --workspace media
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
- Feedback adjusts scores in small bounded ways; it is not model training.

## Next Planned Areas

- Public v0.1.0-prototype polish and repository hygiene.
- Growth Lab for controlled architecture experiments.
- KnowledgeSeed and KnowledgeValidator foundations.
- GrapeCluster and GrowthEngine research prototypes.
- BenchmarkSuite for repeatable routing and orchestration evaluation.
- Optional DonorModelAdapter and LMStudioAdapter experiments.
- TrainingDataExporter for validated traces and specialized expert data.