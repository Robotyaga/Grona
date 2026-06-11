import argparse
import json
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path

REMOTE_PREFIXES = ("http://", "https://", "s3://", "gs://", "hf://", "git://")
CONFIRMATION = "I_UNDERSTAND_THIS_RUNS_LOCAL_TRAINING"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def refuse(message: str) -> None:
    print("REFUSED:")
    print(message)
    raise SystemExit(2)


def load_jsonl_dataset(path: Path, max_rows: int, seed: int) -> list[dict]:
    path_text = str(path)
    if path_text.startswith(REMOTE_PREFIXES):
        refuse("dataset_path must be a local .jsonl file, not a remote URL/path")

    if not path.exists():
        refuse(f"dataset_path does not exist: {path}")

    if path.suffix.lower() != ".jsonl":
        refuse("dataset_path must end with .jsonl")

    rows: list[dict] = []

    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                refuse(f"invalid JSONL at line {line_no}: {e}")

            if not isinstance(obj, dict):
                refuse(f"line {line_no} must be a JSON object")

            instruction = str(obj.get("instruction", "")).strip()
            input_text = str(obj.get("input", "")).strip()
            output = str(obj.get("output", "")).strip()

            if not instruction:
                refuse(f"line {line_no} has empty instruction")
            if not output:
                refuse(f"line {line_no} has empty output")

            rows.append(
                {
                    "instruction": instruction,
                    "input": input_text,
                    "output": output,
                    "line_no": line_no,
                }
            )

            if len(rows) > max_rows:
                refuse(f"dataset has more than max_rows={max_rows} non-empty rows")

    if not rows:
        refuse("dataset has no valid rows")

    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows


def format_example(row: dict) -> str:
    instruction = row["instruction"]
    input_text = row["input"]
    output = row["output"]

    if input_text:
        return (
            "<|im_start|>system\n"
            "You are Grona, a concise technical assistant for modular sparse AI architecture.\n"
            "<|im_end|>\n"
            "<|im_start|>user\n"
            f"{instruction}\n\nInput:\n{input_text}\n"
            "<|im_end|>\n"
            "<|im_start|>assistant\n"
            f"{output}\n"
            "<|im_end|>"
        )

    return (
        "<|im_start|>system\n"
        "You are Grona, a concise technical assistant for modular sparse AI architecture.\n"
        "<|im_end|>\n"
        "<|im_start|>user\n"
        f"{instruction}\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
        f"{output}\n"
        "<|im_end|>"
    )


def choose_target_modules(model) -> list[str]:
    module_names = set()
    for name, _module in model.named_modules():
        last = name.split(".")[-1]
        module_names.add(last)

    qwen_like = [
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ]
    gpt2_like = ["c_attn", "c_proj", "c_fc"]

    selected = [name for name in qwen_like if name in module_names]
    if selected:
        return selected

    selected = [name for name in gpt2_like if name in module_names]
    if selected:
        return selected

    refuse(
        "could not auto-detect LoRA target modules. "
        "Expected Qwen-like q_proj/v_proj/etc or GPT2-like c_attn/c_proj/c_fc."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Local explicit-only LoRA trainer for Grona JSONL datasets."
    )
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--max-rows", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--sequence-length", type=int, default=512)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--allow-model-download", action="store_true")
    parser.add_argument("--overwrite-output", action="store_true")
    parser.add_argument("--confirmation-token", required=True)
    args = parser.parse_args()

    if args.confirmation_token != CONFIRMATION:
        refuse(f"confirmation token must be exactly: {CONFIRMATION}")

    if args.max_steps < 1 or args.max_steps > 5000:
        refuse("max_steps must be between 1 and 5000")

    if args.max_rows < 1 or args.max_rows > 20000:
        refuse("max_rows must be between 1 and 20000")

    if args.batch_size < 1 or args.batch_size > 2:
        refuse("batch_size must be between 1 and 2")

    if args.grad_accum < 1 or args.grad_accum > 16:
        refuse("grad_accum must be between 1 and 16")

    if args.sequence_length < 64 or args.sequence_length > 1024:
        refuse("sequence_length must be between 64 and 1024")

    if args.learning_rate < 1e-6 or args.learning_rate > 1e-3:
        refuse("learning_rate must be between 1e-6 and 1e-3")

    dataset_path = Path(args.dataset_path)
    output_dir = Path(args.output_dir)
    adapter_dir = output_dir / "adapter"
    tokenizer_dir = output_dir / "tokenizer"
    manifest_path = output_dir / "training_manifest.json"

    if output_dir.exists():
        if not args.overwrite_output:
            refuse(
                f"output_dir already exists: {output_dir}. "
                "Pass --overwrite-output to replace it."
            )
        shutil.rmtree(output_dir)

    rows = load_jsonl_dataset(dataset_path, max_rows=args.max_rows, seed=args.seed)

    print("Local Grona LoRA training")
    print(f"Model:        {args.model_id}")
    print(f"Dataset:      {dataset_path}")
    print(f"Rows:         {len(rows)}")
    print(f"Output:       {output_dir}")
    print(f"Max steps:    {args.max_steps}")
    print(f"Batch size:   {args.batch_size}")
    print(f"Grad accum:   {args.grad_accum}")
    print(f"Seq length:   {args.sequence_length}")
    print(f"LR:           {args.learning_rate}")
    print("")

    started_at = utc_now()

    try:
        import torch
        from peft import LoraConfig, get_peft_model
        from torch.utils.data import DataLoader, Dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as e:
        refuse(f"failed to import ML dependencies: {type(e).__name__}: {e}")

    cuda_available = torch.cuda.is_available()
    device = "cuda" if cuda_available else "cpu"
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else ""

    print(f"CUDA:         {cuda_available}")
    if gpu_name:
        print(f"GPU:          {gpu_name}")

    local_files_only = not args.allow_model_download

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_id,
        local_files_only=local_files_only,
        trust_remote_code=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.float16 if cuda_available else torch.float32

    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        local_files_only=local_files_only,
        trust_remote_code=True,
        torch_dtype=dtype,
    )

    model.to(device)
    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()

    if hasattr(model.config, "use_cache"):
        model.config.use_cache = False

    target_modules = choose_target_modules(model)
    print(f"LoRA targets: {target_modules}")

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=target_modules,
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    model.train()

    class TextDataset(Dataset):
        def __init__(self, examples: list[dict]):
            self.examples = examples

        def __len__(self) -> int:
            return len(self.examples)

        def __getitem__(self, idx: int) -> dict:
            text = format_example(self.examples[idx])
            encoded = tokenizer(
                text,
                truncation=True,
                max_length=args.sequence_length,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = encoded["input_ids"].squeeze(0)
            attention_mask = encoded["attention_mask"].squeeze(0)

            labels = input_ids.clone()
            labels[attention_mask == 0] = -100

            return {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels,
            }

    dataset = TextDataset(rows)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    step = 0
    optimizer_step = 0
    last_loss = None
    model.zero_grad(set_to_none=True)

    while step < args.max_steps:
        for batch in dataloader:
            step += 1

            batch = {k: v.to(device) for k, v in batch.items()}

            outputs = model(**batch)
            loss = outputs.loss / args.grad_accum
            loss.backward()

            last_loss = float((loss.detach() * args.grad_accum).cpu())

            if step % args.grad_accum == 0 or step == args.max_steps:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                optimizer_step += 1

            print(
                f"step {step:04d}/{args.max_steps} "
                f"loss={last_loss:.4f} "
                f"optimizer_step={optimizer_step}"
            )

            if step >= args.max_steps:
                break

    output_dir.mkdir(parents=True, exist_ok=True)
    adapter_dir.mkdir(parents=True, exist_ok=True)
    tokenizer_dir.mkdir(parents=True, exist_ok=True)

    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(tokenizer_dir)

    finished_at = utc_now()

    manifest = {
        "kind": "grona_local_lora_training_manifest",
        "model_id": args.model_id,
        "dataset_path": str(dataset_path),
        "output_dir": str(output_dir),
        "adapter_dir": str(adapter_dir),
        "tokenizer_dir": str(tokenizer_dir),
        "train_examples": len(rows),
        "max_steps": args.max_steps,
        "steps_run": step,
        "optimizer_steps": optimizer_step,
        "batch_size": args.batch_size,
        "gradient_accumulation_steps": args.grad_accum,
        "learning_rate": args.learning_rate,
        "sequence_length": args.sequence_length,
        "lora_r": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "target_modules": target_modules,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "last_loss": last_loss,
        "started_at": started_at,
        "finished_at": finished_at,
        "production_trainer": False,
    }

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("")
    print("Training completed")
    print(f"Adapter:   {adapter_dir}")
    print(f"Tokenizer: {tokenizer_dir}")
    print(f"Manifest:  {manifest_path}")
    print(f"Last loss: {last_loss}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
