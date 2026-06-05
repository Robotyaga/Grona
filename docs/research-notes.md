# Research Notes

Grona explores sparse modular AI systems inspired by grape-cluster-like expert activation. These notes are conceptual and intentionally honest about what the project does not solve yet.

For the longer direction, see [Project vision](project-vision.md). For implementation boundaries, see [Architecture](architecture.md), [Growth Lab](growth-lab.md), [Dataset ingestion](dataset-ingestion.md), [Benchmarking](benchmarking.md), [Development notes](development.md), and [Roadmap](roadmap.md).

## Working Hypothesis

A useful AI assistant does not need to activate every capability for every request. If modules have clear metadata, scoped memory, inspectable context boundaries, visible orchestration, typed execution contracts, backend adapters, tool boundaries, deterministic ingestion, workspace profiles, dataset manifest provenance, license policy, dataset quality review, raw knowledge validation, donor proposal provenance, seed review, candidate cluster grouping, growth recommendations, deterministic benchmarks, benchmark run snapshots, experiment comparisons, training export provenance, and safety policy checks, a router can activate a small relevant subset and keep the rest dormant.

## Why This Differs From Monolithic Execution

A monolithic system often hides which capability, memory, prompt, or tool surface shaped the result. Grona explores visible routing instead:

- which modules were considered
- which modules were skipped
- which scores and reasons mattered
- which context was attached
- which dataset manifest, source, license, language, allowed use, and sample type produced a seed
- which dataset rows were parsed, normalized, accepted, rejected, or marked for human review
- which donor proposals were collected, which failed, and which became untrusted seed candidates
- which raw knowledge seeds were validated, weakened, quarantined, rejected, merged, or flagged
- which reviewed seeds were assigned or skipped by the grape clusterer
- which GrowthEngine decisions were recommended and why
- which benchmark cases improved or regressed under a config
- which benchmark run snapshots changed versus a saved baseline
- which experiment configs improved or regressed versus a baseline config
- which records were eligible or ineligible for future training export
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
- Did a candidate run snapshot regress against a prior baseline snapshot?
- Did one deterministic experiment config score higher than another under the current rubric?

This is not answer grading. It is a deterministic rubric for trace behavior.

## Experiment Comparison Hypothesis

Grona-vs-monolith comparisons should start as a transparent harness before any model-backed claim exists. `ExperimentRunner` compares deterministic configs side by side and keeps the output explicit:

- config names and modes
- benchmark run records
- score summaries
- deltas against a baseline config
- best config by deterministic overall score
- improved and regressed configs
- per-case score summaries

The current `MonolithBaseline` is intentionally only a stub. It provides weak broad coverage without explicit module trace, real context routing, GrowthEngine traces, LM Studio, external APIs, downloads, or training. It is useful for shaping future comparison reports, not for claiming that Grona beats a monolithic LLM.

## Dataset Quality Review Hypothesis

Dataset rows should not become knowledge seeds or training examples just because they parse successfully. A lightweight deterministic gate can catch obvious failures early:

- empty or tiny rows
- repeated normalized text
- missing answers in instruction or conversation samples
- suspicious prompt-injection or secret markers
- unsupported sample shapes
- license-policy mismatches
- low information density
- optional domain mismatch

This gate is intentionally modest. It is not semantic deduplication, legal analysis, factual verification, or an LLM judge. Its value is traceability: every accepted, rejected, or human-review decision carries reasons and score metadata before later validation or export layers see the sample.

## Benchmark Snapshot Hypothesis

Benchmark snapshots should make regressions visible before Grona has real model-backed evaluation. A small run record can preserve run id, creation time, config name, optional git commit, benchmark report data, metadata, and schema version.

A regression report can then compare two snapshots with deterministic score deltas and per-case status groups. This is useful for engineering discipline, but it is deliberately not a claim about real-world answer quality, statistical significance, or model intelligence.

## Knowledge Before Weights

Grona assumes that some knowledge should remain external, structured, source-aware, license-aware, reviewed, validated, clustered, benchmarked, snapshot-tested, experiment-compared, and exported with provenance before it ever becomes training data or expert behavior.

`DatasetManifest`, `DatasetLicensePolicy`, `DatasetQualityReviewer`, `DatasetSource`, `DatasetSample`, `DonorModelProposal`, `DonorProposalCollector`, `KnowledgeSeed`, `KnowledgeValidator`, `KnowledgeReviewPipeline`, `GrapeClusterer`, `GrowthEngine`, `BenchmarkSuite`, `BenchmarkRunRecord`, `BenchmarkRegressionReport`, `ExperimentRunner`, `ExperimentComparisonReport`, and `TrainingDataExporter` now provide the first deterministic version of this idea: describe material with explicit provenance, normalize it into proposals or seeds, review obvious quality problems, score it, warn about weak signals, detect repeated claims, mark potential conflicts, organize promote candidates into candidate clusters, recommend a next step, measure whether the trace helped a small benchmark case, preserve benchmark run snapshots, compare regressions, compare experiment configs, and export only conservative training example candidates.

The dataset manifest and review layers are intentionally conservative. JSONL rows can be parsed and normalized, but a row is still only a candidate. Unknown or restricted licenses block unsafe use by default. Review decisions remain visible.

The static donor adapter is intentionally offline and deterministic. The optional LM Studio adapter is only a standard-library integration point for explicitly configured local experiments. Donor output is not treated as trusted knowledge by default and raw donor proposals are not exported as training data by default.

Training export is not training. It is an explicit serialization boundary that keeps instruction, input, output, source, domains, capabilities, provenance, license, validation status, and metadata visible for future review.

This does not prove factual truth. It makes uncertainty explicit.

## Future Growth Questions

- Can workspace profiles reliably constrain routing behavior?
- Can feedback improve routing without turning into opaque learning?
- Can external knowledge seeds improve modules without being baked into weights too early?
- Can dataset material remain source-aware and license-aware before future training use?
- Can deterministic dataset review stop obvious bad rows without blocking useful review workflows?
- Can manifest license policy prevent unsafe dataset use without blocking useful review workflows?
- Can donor model outputs be reviewed, benchmarked, and rejected before becoming durable knowledge?
- Can deterministic grape clusters organize reviewed seeds without hiding provenance?
- Can GrowthEngine proposals stay useful while preserving human review?
- Can TrainingDataExporter preserve enough metadata for future specialized expert experiments?
- Can benchmark snapshots expose routing, context, growth, donor, dataset, and export regressions?
- Can experiment reports compare Grona configs and future monolith baselines without hiding judge assumptions?
- Can Grona-vs-monolith experiments remain honest when real local LLM adapters are added later?

## Current Limits

- No real monolithic LLM baseline yet.
- No persisted workspace directory yet.
- No persisted dataset store yet.
- No persisted dataset manifest files yet.
- No persisted donor proposal store yet.
- No persisted seed store yet.
- No persisted cluster store yet.
- No persisted growth plan store yet.
- No benchmark file writes by default.
- No persisted training dataset store yet.
- No dataset downloads, Hugging Face integration, or `datasets` dependency yet.
- No Parquet reader or large dataset artifact handling yet.
- No large JSONL streaming design yet.
- No JSONL file writing by default.
- No semantic dataset deduplication yet.
- No LLM dataset judging yet.
- No guarantee that accepted samples are good enough for real training.
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
- No shell execution, subprocess usage, network calls by default, or sandboxing yet.
- No default donor model network calls.
- No OpenAI API or Ollama integration.
- Optional LM Studio support is an adapter foundation only; CI and default demos do not use it.
- No trusted donor model workflow yet.
- No raw donor proposal training export by default.
- No vector database, SQL database, web server, or external API.
- No production orchestration.

Before adding model-backed evaluation, donor-backed growth, or training workflows, Grona needs explicit designs for judge reliability, task outputs, human review, benchmark provenance, adapter comparison, score interpretation, failure analysis, donor proposal trust boundaries, license policy, dataset manifest persistence, dataset review calibration, and training export quality review.
