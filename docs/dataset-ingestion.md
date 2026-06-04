# Dataset Ingestion

Dataset ingestion is a deterministic normalization layer for Growth Lab. It lets small structured dataset samples enter Grona as `KnowledgeSeed` values without downloading datasets, training models, or adding heavy dependencies.

The current flow is:

```text
DatasetSource -> DatasetSample -> KnowledgeSeed -> KnowledgeValidator
-> KnowledgeReviewPipeline -> GrapeClusterer -> GrowthEngine
```

## DatasetSource

`DatasetSource` describes where a dataset sample came from before Grona trusts or promotes it.

It carries:

- `id`
- `name`
- `source_type`
- `format`
- `license`
- `language`
- `reliability`
- `metadata`

License and language stay explicit because future training, memory, and expert-growth decisions must know what kind of material they are handling.

Supported source-type labels are small and local: instruction dataset, conversation dataset, web corpus, code dataset, log dataset, or unknown.

Supported format labels are also descriptive only: Alpaca, ShareGPT, JSONL, Parquet, text, or unknown. The prototype does not read files or Parquet yet.

## DatasetSample

`DatasetSample` is the normalized internal representation. It carries content, sample type, domains, keywords, source metadata, and provenance.

A dataset sample is not trusted memory. It may be an instruction, a conversation, a synthetic answer, a log snippet, or a writing example. That is why `sample_type` is preserved when the sample becomes a `KnowledgeSeed`.

## InstructionDatasetSample

`InstructionDatasetSample` models Alpaca-like records with:

- instruction
- optional input
- output

It converts to `DatasetSample` by building a deterministic text block with `Instruction`, `Input`, and `Output` sections. Missing input is allowed. Missing instruction or output is skipped by `AlpacaFormatAdapter`.

## ConversationDatasetSample

`ConversationDatasetSample` models ShareGPT/LMSYS-like records with simple role/content messages.

Roles are normalized conservatively:

- `human` and `user` become `user`
- `gpt`, `bot`, and `assistant` become `assistant`
- `system` stays `system`
- anything else becomes `unknown`

It converts to `DatasetSample` by rendering each useful message as `role: content`.

## AlpacaFormatAdapter

`AlpacaFormatAdapter` accepts in-memory dictionaries with `instruction`, `input`, and `output` fields.

It does not load files. It does not download `yahma/alpaca-cleaned` or any other dataset. It simply normalizes small dictionaries that tests or demos provide.

The adapter:

- tolerates missing `input`
- skips rows without instruction or output
- infers simple sample type, domains, and keywords
- preserves dataset metadata and license information

## ShareGPTFormatAdapter

`ShareGPTFormatAdapter` accepts in-memory dictionaries with either:

```python
{"conversations": [{"from": "human", "value": "..."}]}
```

or:

```python
{"messages": [{"role": "user", "content": "..."}]}
```

The adapter:

- normalizes role labels
- skips broken rows without useful messages
- infers simple sample type, domains, and keywords
- preserves dataset metadata and license information

## KnowledgeSeed Conversion

`knowledge_seed_from_dataset_sample(sample)` converts a normalized sample into a Growth Lab `KnowledgeSeed`.

The seed source is derived from `DatasetSource`, and the seed metadata preserves:

- dataset source id
- dataset source type
- dataset format
- dataset license
- dataset language
- sample type

This is intentionally cautious. A dataset row is not automatically factual knowledge, trusted memory, model weights, or expert behavior.

## Demo Sources

The repository includes tiny demo helpers:

- `create_demo_dataset_sources()`
- `create_demo_alpaca_samples()`
- `create_demo_sharegpt_samples()`

Demo source styles include `yahma/alpaca-cleaned`, `lmsys-chat-1m` / ShareGPT, and UA-Alpaca-like instruction data. These are tiny hand-written examples only.

## Running The Demo

```bash
python -m grona --dataset-demo
python examples/dataset_ingestion_demo.py
```

The demo prints counts for dataset samples, instruction samples, conversation samples, generated `KnowledgeSeed` values, validation statuses, clusters, assignments, and GrowthEngine decisions.

## Why Samples Become Seeds

Future datasets such as `yahma/alpaca-cleaned`, UA-Alpaca, OpenHermes, LMSYS / ShareGPT, Loghub, C4 slices, and Wikipedia-derived samples may contain useful material, but they also carry licensing, provenance, quality, duplication, and factuality risks.

Converting samples into `KnowledgeSeed` values makes those risks visible. Seeds can be validated, deduplicated, reviewed, clustered, and evaluated by GrowthEngine before anything becomes durable memory, benchmark material, expert behavior, or training data.

## Current Limitations

- No real dataset downloads.
- No Hugging Face integration.
- No `datasets` dependency.
- No JSONL file loader.
- No Parquet reader.
- No C4, Wikipedia, Loghub, OpenHermes, LMSYS, ShareGPT, Alpaca, or UA-Alpaca download path.
- No large dataset files.
- No generated dataset artifacts.
- No embeddings or vector database.
- No model training or training-data export.
- No automatic promotion from dataset sample to trusted memory.

This layer is a deterministic foundation for future research, not a production data pipeline.
