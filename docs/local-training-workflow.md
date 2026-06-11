# Local Training Workflow

This workflow is Windows PowerShell-first and local-only. Heavy ML dependencies live in `.venv-train`; normal Grona tests and CI do not import `torch`, `transformers`, or `peft`.

## Environment

Activate the local training venv when running tools directly:

```powershell
.\.venv-train\Scripts\Activate.ps1
```

Prepare repo-local folders and force Hugging Face caches to `F:\Grona\hf-cache`:

```powershell
.\grona.ps1 train-env
```

This sets:

- `HF_HOME=F:\Grona\hf-cache`
- `HF_HUB_CACHE=F:\Grona\hf-cache\hub`
- `HF_DATASETS_CACHE=F:\Grona\hf-cache\datasets`
- `TRANSFORMERS_CACHE=F:\Grona\hf-cache\transformers`
- `HF_HUB_DISABLE_SYMLINKS_WARNING=1`

It creates `data/`, `outputs/`, `logs/`, and the cache directories. It does not download anything.

## Build Dataset

```powershell
.\grona.ps1 build-ultimate-dataset
```

This runs `tools/make_big_hf_mix_dataset.py`, writes `data/ultimate_grona_mix_001.jsonl`, verifies more than 100 rows, and logs to `logs/build_ultimate_dataset_<timestamp>.log`.

## Train Ultimate LoRA

```powershell
.\grona.ps1 train-ultimate
```

This runs `tools/train_lora_local.py` against `Qwen/Qwen2.5-Coder-3B-Instruct` and writes:

```text
outputs/qwen25-coder-3b-grona-ultimate-001
```

Training is explicit, local, logged, and guarded by the local training confirmation token inside the wrapper. It may download the base model only because the wrapper passes `--allow-model-download`.

## Chat

```powershell
.\grona.ps1 chat-3b-donor
.\grona.ps1 chat-3b-ultimate
```

The chat tool loads the base model, adapter, and tokenizer from local paths, then starts an interactive prompt. Optional persistent notes can be supplied when running the Python tool directly:

```powershell
.\.venv-train\Scripts\python.exe tools\chat_lora_adapter.py `
  --model-id Qwen/Qwen2.5-Coder-3B-Instruct `
  --adapter-dir outputs\qwen25-coder-3b-grona-ultimate-001\adapter `
  --tokenizer-dir outputs\qwen25-coder-3b-grona-ultimate-001\tokenizer `
  --memory-file data\local_notes.md `
  --confirmation-token I_UNDERSTAND_THIS_LOADS_LOCAL_MODEL
```

## Eval

```powershell
.\grona.ps1 eval-3b-donor
.\grona.ps1 eval-3b-ultimate
```

The eval script runs a fixed Ukrainian/English prompt suite and writes JSONL results to `logs/eval_<timestamp>.jsonl`. Scoring is deterministic substring checking, not LLM judging and not a quality guarantee.

## Do Not Commit

Do not commit:

- `data/`
- `outputs/`
- `logs/`
- `.venv-train/`
- `hf-cache/`
- model weights, adapter weights, checkpoints, or GGUF files

These are ignored by `.gitignore`.

## Known Limitations

- LoRA does not magically add perfect reasoning.
- A 3B model has real capacity limits.
- Large generic datasets can make hallucinations worse if they dilute local corrections.
- The eval suite is deterministic and heuristic only.
- These tools are not production training or serving infrastructure.
