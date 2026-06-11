import argparse
import json
import random
from pathlib import Path

CONFIRMATION = "I_UNDERSTAND_THIS_GENERATES_SYNTHETIC_DATASET"


PROMPT_TEMPLATES = [
    # Grona architecture
    "Explain what Grona is in practical technical terms.",
    "Explain why Grona should route tasks to selected modules instead of activating everything.",
    "Describe the grape-cluster metaphor for Grona.",
    "Explain what an ExpertModule is in a modular sparse AI system.",
    "Explain how a Router should choose between code, docs, training, safety, and general modules.",
    "Write a conceptual Python route_task(task: str) function for Grona.",
    "Write a small ExpertModule class and Router class for a modular sparse AI prototype.",
    "Explain what Grona should refuse to do by default.",
    "Explain why real training should require explicit confirmation tokens.",
    "Explain why outputs/, data/, and .venv-train/ should not be committed to Git.",

    # LoRA / local training
    "Explain the difference between GGUF models and HuggingFace transformer models for LoRA training.",
    "Explain how local LoRA training works using transformers and peft.",
    "Explain what a LoRA adapter is.",
    "Explain why QLoRA and bitsandbytes are separate from simple LoRA.",
    "Explain how to debug CUDA availability in PyTorch.",
    "Explain what to do if a LoRA training run hits CUDA out of memory.",
    "Explain what max_steps, batch_size, gradient_accumulation_steps, learning_rate, and sequence_length mean.",
    "Explain why a low training loss may mean overfitting.",
    "Explain why a small model may hallucinate facts.",
    "Explain how to create a JSONL instruction dataset.",

    # Code tasks
    "Write a robust Python function that classifies a task into code, docs, training, safety, or general.",
    "Write a Python function that validates JSONL rows with instruction, input, and output fields.",
    "Write a Python function that refuses remote dataset paths such as http://, https://, s3://, gs://, hf://.",
    "Write a Python function that writes a training_manifest.json file.",
    "Write a PowerShell command sequence for creating a Python venv and installing a package in editable mode.",
    "Write a small Python CLI using argparse for a local training script.",
    "Write a safe error message for a missing dataset_path.",
    "Write a safe error message for a missing adapter_dir.",
    "Write a short README section explaining a portable launcher with grona.ps1 work and grona.ps1 check.",

    # Honesty / anti-hallucination
    "What should an assistant do when it does not know a fact?",
    "Explain why an assistant must not invent APIs that are not present in a repository.",
    "Explain why an assistant should not claim permanent memory unless persistent memory is implemented.",
    "Answer safely: who wrote War and Peace?",
    "Answer safely: who was Taras Shevchenko?",
    "Correct this false claim: Taras Shevchenko wrote War and Peace.",
    "Correct this false claim: Grona has a public Grona() class with add_task() and run() methods.",
    "Write rules for a local assistant that must avoid hallucinating facts.",

    # Ukrainian technical answers
    "Відповідай українською. Поясни, що таке Grona.",
    "Відповідай українською. Чим Grona відрізняється від монолітної AI-моделі?",
    "Відповідай українською. Що таке LoRA adapter?",
    "Відповідай українською. Чому GGUF не підходить напряму для LoRA training через transformers?",
    "Відповідай українською. Як підготувати JSONL датасет для локального навчання?",
    "Відповідай українською. Що робити, якщо модель не знає точну відповідь?",
    "Відповідай українською. Хто такий Тарас Шевченко?",
    "Відповідай українською. Хто написав роман 'Війна і мир'?",
    "Відповідай українською. Напиши концептуальну функцію route_task для Grona.",
]


def build_instruction(prompt: str) -> str:
    return prompt.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--adapter-dir", default="")
    parser.add_argument("--tokenizer-dir", default="")
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--samples", type=int, default=500)
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--temperature", type=float, default=0.45)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--confirmation-token", required=True)
    args = parser.parse_args()

    if args.confirmation_token != CONFIRMATION:
        raise SystemExit(f"confirmation token must be exactly: {CONFIRMATION}")

    random.seed(args.seed)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    use_adapter = bool(args.adapter_dir)

    if use_adapter:
        from peft import PeftModel

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    tokenizer_source = args.tokenizer_dir if args.tokenizer_dir else args.model_id

    print(f"Loading tokenizer: {tokenizer_source}")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, trust_remote_code=True)

    print(f"Loading model: {args.model_id}")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=dtype,
        trust_remote_code=True,
    ).to(device)

    if use_adapter:
        print(f"Loading adapter: {args.adapter_dir}")
        model = PeftModel.from_pretrained(base_model, args.adapter_dir).to(device)
    else:
        model = base_model

    model.eval()

    system = (
        "You are a careful technical teacher. "
        "Give accurate, concise, useful answers. "
        "Do not invent APIs, facts, files, commands, or capabilities. "
        "If unsure, say that you are not sure."
    )

    out_path = Path(args.output_jsonl)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows_written = 0

    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        for _i in range(args.samples):
            instruction = build_instruction(random.choice(PROMPT_TEMPLATES))

            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": instruction},
            ]

            if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
                prompt = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            else:
                prompt = (
                    "<|im_start|>system\n"
                    f"{system}\n"
                    "<|im_end|>\n"
                    "<|im_start|>user\n"
                    f"{instruction}\n"
                    "<|im_end|>\n"
                    "<|im_start|>assistant\n"
                )

            inputs = tokenizer(prompt, return_tensors="pt").to(device)

            with torch.no_grad():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=True,
                    temperature=args.temperature,
                    top_p=0.9,
                    repetition_penalty=1.12,
                    no_repeat_ngram_size=4,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )

            output = tokenizer.decode(
                output_ids[0][inputs["input_ids"].shape[-1]:],
                skip_special_tokens=True,
            ).strip()

            if not output:
                continue

            row = {
                "instruction": instruction,
                "input": "",
                "output": output,
                "source": "donor-qwen3b",
            }

            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows_written += 1

            print(f"[{rows_written}/{args.samples}] {instruction[:80]}")

    print("")
    print(f"Created donor dataset: {out_path}")
    print(f"Rows: {rows_written}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
