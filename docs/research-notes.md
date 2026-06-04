# Research Notes

Grona explores sparse modular AI systems inspired by grape-cluster-like expert activation. These notes are conceptual and intentionally honest about what the project does not solve yet.

For the longer direction, see [Project vision](project-vision.md). For implementation boundaries, see [Architecture](architecture.md), [Growth Lab](growth-lab.md), [Dataset ingestion](dataset-ingestion.md), [Benchmarking](benchmarking.md), [Development notes](development.md), and [Roadmap](roadmap.md).

## Working Hypothesis

A useful AI assistant does not need to activate every capability for every request. If modules have clear metadata, scoped memory, inspectable context boundaries, visible orchestration, typed execution contracts, backend adapters, tool boundaries, deterministic ingestion, workspace profiles, dataset provenance, raw knowledge validation, seed review, candidate cluster grouping, growth recommendations, deterministic benchmarks, and safety policy checks, a router can activate a small relevant subset and keep the rest dormant.

## Why This Differs From Monolithic Execution

A monolithic system often hides which capability, memory, prompt, or tool surface shaped the result. Grona explores visible routing instead:

- which modules were considered
- which modules were skipped
- which scores and reasons mattered
- which context was attached
- which dataset source, license, language, and sample type produced a seed
- which raw knowledge seeds were validated, weakened, quarantined, rejected, merged, or flagged
- which reviewed seeds were assigned or skipped by the grape clusterer
- which GrowthEngine decisions were recommended and why
- which benchmark cases improved or regressed under a config
- which safety policy decisions were made
- which feedback might alter future routing

The current prototype is deterministic so these questions can be inspected before adding model uncertainty.

## Benchmark Questions

BenchmarkSuite currently asks conservative local questions:

- Did the expected module names appear in the selected route?
- Did the expected high-level domains appear in the selected route?
- Did expected keywords appear in task context, memory, grape clusters, or growth traces?
- Did GrowthEngine produce relevant deterministic signals?
- Did an enhanced config improve the available context compared with baseline routing?

This is not answer grading. It is a deterministic rubric for trace behavior.

## Knowledge Before Weights

Grona assumes that some knowledge should remain external, structured, source-aware, license-aware, validated, reviewed, clustered, and benchmarked before it ever becomes training data or expert behavior.

`DatasetSource`, `DatasetSample`, `KnowledgeSeed`, `KnowledgeValidator`, `KnowledgeReviewPipeline`, `GrapeClusterer`, `GrowthEngine`, and `BenchmarkSuite` now provide the first deterministic version of this idea: collect material with provenance, normalize it into seeds, score it, warn about weak signals, detect repeated claims, mark potential conflicts, organize promote candidates into candidate clusters, recommend a next step, and measure whether the trace helped a small benchmark case.

This does not prove factual truth. It makes uncertainty explicit.

## Future Growth Questions

- Can workspace profiles reliably constrain routing behavior?
- Can feedback improve routing without turning into opaque learning?
- Can external knowledge seeds improve modules without being baked into weights too early?
- Can dataset material remain source-aware and license-aware before future training use?
- Can deterministic grape clusters organize reviewed seeds without hiding provenance?
- Can GrowthEngine proposals stay useful while preserving human review?
- Can BenchmarkSuite expose regressions in routing, context, dataset ingestion, seed validation, seed review, cluster assignment, growth planning, and safety behavior?
- Can donor model outputs be validated and reviewed before becoming durable knowledge?
- Can Grona-vs-monolith experiments be compared without hiding judge assumptions?

## Current Limits

- No persisted workspace directory yet.
- No persisted dataset store yet.
- No persisted seed store yet.
- No persisted cluster store yet.
- No persisted growth plan store yet.
- No persisted benchmark store yet.
- No dataset downloads, Hugging Face integration, or `datasets` dependency yet.
- No JSONL loader, Parquet reader, or large dataset artifact handling yet.
- No external config files loaded from disk.
- No secrets or user-specific private settings.
- No real AI expert execution yet.
- No real RAG yet.
- No PDF parsing, OCR, embeddings, vector search, or filesystem crawling yet.
- No semantic clustering yet.
- No web fact-checking or temporal freshness checks yet.
- No LLM-based contradiction detection or automatic truth resolution yet.
- No external benchmark judge model yet.
- No autonomous self-training, model weights, or automatic expert creation yet.
- No shell execution, subprocess usage, network calls, or sandboxing yet.
- No OpenAI API, donor model adapter, LM Studio adapter, or Ollama integration.
- No vector database, SQL database, web server, or external API.
- No production orchestration.

Before adding model-backed evaluation, Grona needs explicit designs for judge reliability, task outputs, human review, benchmark provenance, adapter comparison, score interpretation, and failure analysis.
