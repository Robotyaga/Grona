# Dataset Ingestion

Dataset ingestion is a deterministic normalization layer for Growth Lab. It lets small structured dataset samples enter Grona as explicit candidates without downloading datasets, training models, or adding heavy dependencies.

The current flow is:

```text
DatasetManifest -> DatasetLicensePolicy -> JsonlDatasetRecord -> DatasetSample
-> KnowledgeSeed candidate -> KnowledgeValidator -> KnowledgeReviewPipeline
-> GrapeClusterer -> GrowthEngine -> BenchmarkSuite -> TrainingDataExporter candidate
```

## DatasetManifest

`DatasetManifest` describes a local dataset source before Grona trusts or promotes any row from it. It records:

- name and description
- source label or path-like description
- format
- license
- allowed uses
- domains and capabilities
- whether review is required
- extra metadata

Allowed uses are explicit:

- `routing_eval`
- `knowledge_seed_candidate`
- `training_export_candidate`
- `benchmark_candidate`

A dataset is not automatically training-safe just because it can be parsed. License, provenance, allowed uses, and review policy stay attached.

## DatasetLicensePolicy

`DatasetLicensePolicy` is conservative by default. It can answer whether a manifest may create knowledge seed candidates, whether it may create training export candidates, whether review is required, and why a use was allowed or rejected.

Training export candidates are blocked for unknown, research-only, non-commercial, proprietary, and similar licenses. This is a simple deterministic policy, not legal advice.

## JSONL Reader

The JSONL foundation supports:

- `read_jsonl_records(text)`
- `read_jsonl_stream(stream)`
- `read_jsonl_file(path)` for explicit paths only

It skips empty lines, preserves line numbers, and raises clear errors for invalid JSON in strict mode. It does not scan directories, download files, or read arbitrary user filesystem paths in demos or tests.

`JsonlDatasetRecord` stores line number, parsed object data, and metadata.

## Normalization

`DatasetIngestor` accepts a `DatasetManifest` and parsed JSONL records. It applies `DatasetLicensePolicy`, normalizes supported record shapes, attaches manifest provenance metadata, and returns both normalized samples and a `DatasetIngestionReport`.

Supported MVP shapes:

- Alpaca-like: `instruction`, optional `input`, `output`
- ShareGPT-like: `conversations` or `messages`
- Generic text: `text`

Existing `AlpacaFormatAdapter` and `ShareGPTFormatAdapter` are reused for instruction and conversation shapes.

## DatasetSource And DatasetSample

`DatasetSource` describes where a normalized sample came from before Grona trusts or promotes it. It carries id, name, source type, format, license, language, reliability, and metadata.

`DatasetSample` is the normalized internal representation. It carries content, sample type, domains, keywords, source metadata, and provenance.

A dataset sample is not trusted memory. It may be an instruction, a conversation, a synthetic answer, a log snippet, or a writing example. That is why `sample_type` and manifest metadata are preserved when the sample becomes a `KnowledgeSeed` candidate.

## KnowledgeSeed Conversion

`knowledge_seed_from_dataset_sample(sample)` converts a normalized sample into a Growth Lab `KnowledgeSeed`.

The seed metadata preserves:

- dataset source id
- dataset source type
- dataset format
- dataset license
- dataset language
- manifest name and source when available
- allowed uses when available
- sample type

This is intentionally cautious. A dataset row is not automatically factual knowledge, trusted memory, model weights, or expert behavior.

## TrainingDataExporter Relationship

Manifest-aware ingestion can mark whether a dataset is allowed to become a `training_export_candidate`, but that does not export it directly. Records still need validation/review policy before `TrainingDataExporter` should emit future training example candidates.

Datasets are not assumed to be training-safe. Unknown or restricted licenses are rejected by the conservative policy for training export candidate use.

## DatasetIngestionReport

`DatasetIngestionReport` records:

- manifest name
- records read
- records accepted
- records rejected
- rejection reasons
- normalized sample count
- policy decision summary

The report is deterministic and printable for debugging.

## Benchmark Measurement

BenchmarkSuite can use dataset-derived seeds, grape clusters, and GrowthEngine memory bridges in deterministic demo configs. This lets Grona compare baseline routing with enhanced local context from dataset ingestion and growth decisions.

BenchmarkSuite does not prove dataset quality or model accuracy. It only scores deterministic traces such as selected modules, expected domains, context keyword coverage, and growth relevance.

See [Benchmarking](benchmarking.md).

## Running The Demo

```bash
python -m grona --dataset-demo
python -m grona --jsonl-dataset-demo
python -m grona --benchmark-demo
python examples/dataset_ingestion_demo.py
python examples/jsonl_dataset_ingestion_demo.py
python examples/benchmark_demo.py
```

The JSONL dataset demo uses a tiny in-memory JSONL string, a demo manifest, and the conservative policy. It prints policy decisions, report counts, rejection reasons, and normalized sample ids. It does not read or write external files.

## Current Limitations

- No real dataset downloads.
- No Hugging Face integration.
- No `datasets` dependency.
- No Parquet reader.
- No pandas, pyarrow, fastparquet, or heavy dependencies.
- No large dataset streaming.
- No C4, Wikipedia, Loghub, OpenHermes, LMSYS, ShareGPT, Alpaca, or UA-Alpaca download path.
- No large dataset files.
- No generated dataset or benchmark artifacts.
- No embeddings or vector database.
- No model training.
- No automatic training export.
- No automatic promotion from dataset sample to trusted memory.
- No automatic benchmark accuracy claims from dataset-derived context.
- No trust in donor/model-generated data without review.

This layer is a deterministic foundation for future research, not a production data pipeline.
