# Research Notes

Grona explores sparse modular AI systems inspired by grape-cluster-like expert activation. These notes are conceptual and intentionally honest about what the project does not solve yet.

For the longer direction, see [Project vision](project-vision.md). For implementation boundaries, see [Architecture](architecture.md), [Growth Lab](growth-lab.md), [Dataset ingestion](dataset-ingestion.md), [Development notes](development.md), and [Roadmap](roadmap.md).

## Working Hypothesis

A useful AI assistant does not need to activate every capability for every request. If modules have clear metadata, scoped memory, inspectable context boundaries, visible orchestration, typed execution contracts, backend adapters, tool boundaries, deterministic ingestion, workspace profiles, dataset provenance, raw knowledge validation, seed review, candidate cluster grouping, growth recommendations, and safety policy checks, a router can activate a small relevant subset and keep the rest dormant.

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
- which safety policy decisions were made
- which feedback might alter future routing

The current prototype is deterministic so these questions can be inspected before adding model uncertainty.

## Workspace Profiles

A workspace profile describes a configured vineyard for a specific use case.

- Workspace is the environment.
- Profile is how the cluster is arranged.
- Enabled modules are active grapes.
- Dataset samples are structured nutrients with provenance and license metadata.
- Knowledge seeds are raw nutrients.
- Grape nodes are organized candidate nutrients.
- Grape clusters are deterministic candidate groupings.
- GrowthEngine is the recommendation layer for what should grow next.
- Memory sources are knowledge nutrients that entered the context path.
- Safety policy is the protective layer.
- Routing mode is the activation rule set.

`WorkspaceProfile` and `WorkspaceConfig` are intentionally small dataclass-based structures. Built-in profiles cover default, code, cybersecurity, media, automotive, and document research workflows.

This is not production config management. There is no persisted workspace directory, no disk-loaded config file, no secrets handling, no external API, and no database-backed profile system.

## Knowledge Before Weights

Grona assumes that some knowledge should remain external, structured, source-aware, license-aware, and validated before it ever becomes training data or expert behavior.

`DatasetSource`, `DatasetSample`, `KnowledgeSeed`, `KnowledgeValidator`, `KnowledgeReviewPipeline`, `GrapeClusterer`, and `GrowthEngine` now provide the first deterministic version of this idea: collect dataset-like material with provenance, normalize it into seeds, score it, warn about weak signals, detect repeated claims, mark potential conflicts, organize promote candidates into candidate clusters, and recommend a next step before anything becomes durable.

This does not prove factual truth. It makes uncertainty explicit.

## Dataset Questions

Dataset rows are not all the same kind of knowledge. An Alpaca-like record may be an instruction and answer. A ShareGPT-like row may be a conversational trace. A web-corpus row may be text with unclear provenance. A log row may be operational evidence.

The current dataset ingestion foundation asks conservative questions:

- What dataset source produced this sample?
- What license, language, and format metadata should follow it?
- Is the sample an instruction, conversation, factual QA, reasoning sample, code sample, or something else?
- Which domains and keywords can be inferred deterministically?
- Can the sample become a `KnowledgeSeed` without becoming trusted memory or weights?

This prepares future use of sources such as `yahma/alpaca-cleaned`, UA-Alpaca, OpenHermes, LMSYS / ShareGPT, Loghub, C4 slices, and Wikipedia-derived samples without implementing downloads yet.

## GrowthEngine Questions

The current GrowthEngine MVP asks conservative questions:

- Should this reviewed seed be promoted, merged, quarantined, or rejected?
- Is this cluster strong enough to prepare a memory bridge?
- Does this cluster need review before memory or expert growth?
- Does this cluster have enough reviewed seeds and domain consistency to suggest a future expert candidate?
- Which reasons and metadata should be visible to a human reviewer?

GrowthEngine is a recommendation engine. It is not autonomous self-training, automatic truth resolution, or automatic expert creation.

## Execution and Tool Boundaries

The execution interface separates routing metadata from runnable behavior. Execution adapters add a backend-oriented layer. Tool adapters model future tool use without performing it.

The current mock tools do not read files, write files, run commands, start subprocesses, call networks, use external APIs, or invoke real scanners. They make future integration points visible and testable.

## Safety Policy Layer

The safety layer asks policy questions before future tools exist:

- Is this action allowed?
- Is it risky, destructive, or unknown?
- Is it read-only?
- Should it remain dry-run only?
- What confirmation would be required?
- Why was it allowed or blocked?

`ToolAction` is a planned action, not execution. `PolicyDecision` is the reasoned result of policy evaluation. `ExecutionPlan` groups planned actions and decisions for an `ExecutionRequest`. `SafeExecutionAdapter` wraps an adapter and turns policy outcomes into `ExpertResult` values. `SafeToolRunner` applies the same policy idea to mock tool adapters.

## Future Growth Questions

- Can workspace profiles reliably constrain routing behavior?
- Can feedback improve routing without turning into opaque learning?
- Can external knowledge seeds improve modules without being baked into weights too early?
- Can dataset material remain source-aware and license-aware before future training use?
- Can deterministic grape clusters organize reviewed seeds without hiding provenance?
- Can GrowthEngine proposals stay useful while preserving human review?
- Can donor model outputs be validated and reviewed before becoming durable knowledge?
- Can benchmark traces expose regressions in routing, context, dataset ingestion, seed validation, seed review, cluster assignment, growth planning, and safety behavior?

## Current Limits

- No persisted workspace directory yet.
- No persisted dataset store yet.
- No persisted seed store yet.
- No persisted cluster store yet.
- No persisted growth plan store yet.
- No dataset downloads, Hugging Face integration, or `datasets` dependency yet.
- No JSONL loader, Parquet reader, or large dataset artifact handling yet.
- No external config files loaded from disk.
- No secrets or user-specific private settings.
- No production config management.
- No real AI expert execution yet.
- No real RAG yet.
- No PDF parsing, OCR, embeddings, vector search, or filesystem crawling yet.
- No semantic clustering yet.
- No web fact-checking or temporal freshness checks yet.
- No LLM-based contradiction detection or automatic truth resolution yet.
- No autonomous self-training, model weights, or automatic expert creation yet.
- No shell execution, subprocess usage, network calls, or sandboxing yet.
- No process isolation or filesystem isolation.
- No OpenAI API, donor model adapter, or Ollama integration.
- No vector database, SQL database, web server, or external API.
- No production orchestration.

## Future Work

Before adding real dataset workflows, Grona needs explicit designs for download boundaries, local file loading, licensing policy, dataset manifests, sampling, filtering, provenance, deletion semantics, and benchmark impact.

Before adding real document workflows, Grona needs explicit designs for file selection, parser dependencies, citation tracking, content updates, embeddings, vector search, privacy boundaries, and deletion semantics.

Before adding real execution, Grona needs explicit designs for subprocess control, sandboxing, file access boundaries, network access boundaries, secrets handling, audit logs, user confirmation flows, and rollback or recovery expectations.

Before adding model-backed growth, Grona needs explicit designs for donor model reliability, validation, review decisions, cluster assignment, GrowthEngine approval, provenance, benchmark impact, training data export, and human review.
