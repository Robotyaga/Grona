# Dataset Ingestion

Dataset ingestion is a deterministic normalization layer for Growth Lab. It lets small structured dataset samples enter Grona as `KnowledgeSeed` values without downloading datasets, training models, or adding heavy dependencies.

The current flow is:

```text
DatasetSource -> DatasetSample -> KnowledgeSeed -> KnowledgeValidator
-> KnowledgeReviewPipeline -> GrapeClusterer -> GrowthEngine -> BenchmarkSuite
```

## DatasetSource

`DatasetSource` describes where a dataset sample came from before Grona trusts or promotes it. It carries id, name, source type, format, license, language, reliability, and metadata.

License and language stay explicit because future training, memory, benchmark, and expert-growth decisions must know what kind of material they are handling.

## DatasetSample

`DatasetSample` is the normalized internal representation. It carries content, sample type, domains, keywords, source metadata, and provenance.

A dataset sample is not trusted memory. It may be an instruction, a conversation, a synthetic answer, a log snippet, or a writing example. That is why `sample_type` is preserved when the sample becomes a `KnowledgeSeed`.

## Adapters

`AlpacaFormatAdapter` accepts small in-memory dictionaries with instruction, optional input, and output fields.

`ShareGPTFormatAdapter` accepts small in-memory dictionaries with `conversations` or `messages` role/content data.

The adapters:

- normalize tiny in-memory records
- skip broken rows
- infer simple sample type, domains, and keywords
- preserve dataset metadata and license information

They do not load files, download datasets, call Hugging Face, parse Parquet, or create artifacts.

## KnowledgeSeed Conversion

`knowledge_seed_from_dataset_sample(sample)` converts a normalized sample into a Growth Lab `KnowledgeSeed`.

The seed metadata preserves:

- dataset source id
- dataset source type
- dataset format
- dataset license
- dataset language
- sample type

This is intentionally cautious. A dataset row is not automatically factual knowledge, trusted memory, model weights, or expert behavior.

## Benchmark Measurement

BenchmarkSuite can use dataset-derived seeds, grape clusters, and GrowthEngine memory bridges in deterministic demo configs. This lets Grona compare baseline routing with enhanced local context from dataset ingestion and growth decisions.

BenchmarkSuite does not prove dataset quality or model accuracy. It only scores deterministic traces such as selected modules, expected domains, context keyword coverage, and growth relevance.

See [Benchmarking](benchmarking.md).

## Running The Demo

```bash
python -m grona --dataset-demo
python -m grona --benchmark-demo
python examples/dataset_ingestion_demo.py
python examples/benchmark_demo.py
```

The dataset demo prints counts for dataset samples, generated `KnowledgeSeed` values, validation statuses, clusters, assignments, and GrowthEngine decisions. The benchmark demo compares baseline and enhanced deterministic configurations.

## Current Limitations

- No real dataset downloads.
- No Hugging Face integration.
- No `datasets` dependency.
- No JSONL file loader.
- No Parquet reader.
- No C4, Wikipedia, Loghub, OpenHermes, LMSYS, ShareGPT, Alpaca, or UA-Alpaca download path.
- No large dataset files.
- No generated dataset or benchmark artifacts.
- No embeddings or vector database.
- No model training or training-data export.
- No automatic promotion from dataset sample to trusted memory.
- No automatic benchmark accuracy claims from dataset-derived context.

This layer is a deterministic foundation for future research, not a production data pipeline.
