import argparse
import json
from datetime import datetime
from pathlib import Path

CONFIRMATION = "I_UNDERSTAND_THIS_LOADS_LOCAL_MODEL"


def utc_timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def evaluation_cases() -> list[dict]:
    return [
        {
            "id": "shevchenko",
            "prompt": "Українською: ким був Тарас Шевченко?",
            "checks": ["шевчен", "поет"],
        },
        {
            "id": "war_and_peace",
            "prompt": "Who wrote War and Peace?",
            "checks": ["tolstoy"],
        },
        {
            "id": "what_is_grona",
            "prompt": "What is Grona in this repository?",
            "checks": ["grona", "modular"],
        },
        {
            "id": "route_task_concept",
            "prompt": (
                "Write conceptual Python pseudocode for routing a task to expert modules. "
                "Do not invent real Grona APIs."
            ),
            "checks": ["def", "route", "task"],
            "forbidden": ["grona.route_task(", "GronaRouter"],
        },
        {
            "id": "boolean_simplification",
            "prompt": "Simplify F(A,B)=(A AND NOT B) OR (A AND B).",
            "checks": ["a"],
            "forbidden": ["not b", "a and b"],
        },
        {
            "id": "truth_logic_uk",
            "prompt": (
                "Логічна задача: Андрій каже, що Богдан бреше. Богдан каже, що Віктор бреше. "
                "Віктор каже, що Андрій і Богдан кажуть правду. "
                "Якщо рівно один із них каже правду, "
                "перший рядок відповіді має бути НЕПРАВДУ."
            ),
            "checks": ["неправду"],
            "first_line": "неправду",
        },
        {
            "id": "vector_problem",
            "prompt": (
                "Given A(2,-1,3), B(1,2,0), C(4,-3,5), compute vectors AB and AC "
                "and their dot product."
            ),
            "checks": ["(-1", "3", "-3", "(2", "-2", "2", "-14"],
        },
    ]


def score_response(text: str, case: dict) -> dict:
    lowered = text.lower()
    checks = case.get("checks", ())
    matched = [check for check in checks if check.lower() in lowered]
    forbidden = [item for item in case.get("forbidden", ()) if item.lower() in lowered]
    first_line = str(case.get("first_line", "")).lower()
    first_line_ok = True
    if first_line:
        actual = lowered.strip().splitlines()[0] if lowered.strip() else ""
        first_line_ok = actual.startswith(first_line)
    passed = len(matched) == len(checks) and not forbidden and first_line_ok
    return {
        "passed": passed,
        "matched": matched,
        "missing": [check for check in checks if check not in matched],
        "forbidden_found": forbidden,
        "first_line_ok": first_line_ok,
    }


def build_prompt(tokenizer, system_prompt: str, user_prompt: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    return (
        "<|im_start|>system\n"
        f"{system_prompt}\n"
        "<|im_end|>\n"
        "<|im_start|>user\n"
        f"{user_prompt}\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a local Grona LoRA adapter heuristically."
    )
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--adapter-dir", default="")
    parser.add_argument("--tokenizer-dir", default="")
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--allow-model-download", action="store_true")
    parser.add_argument("--confirmation-token", required=True)
    args = parser.parse_args()

    if args.confirmation_token != CONFIRMATION:
        raise SystemExit(f"confirmation token must be exactly: {CONFIRMATION}")

    adapter_dir = Path(args.adapter_dir) if args.adapter_dir else None
    tokenizer_dir = Path(args.tokenizer_dir) if args.tokenizer_dir else None
    if adapter_dir is not None and not adapter_dir.exists():
        raise SystemExit(f"adapter_dir does not exist: {adapter_dir}")
    if tokenizer_dir is not None and not tokenizer_dir.exists():
        raise SystemExit(f"tokenizer_dir does not exist: {tokenizer_dir}")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    peft_model = None
    if adapter_dir is not None:
        from peft import PeftModel

        peft_model = PeftModel

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    local_files_only = not args.allow_model_download

    tokenizer_source = tokenizer_dir if tokenizer_dir is not None else args.model_id
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_source,
        local_files_only=local_files_only if tokenizer_dir is None else True,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        local_files_only=local_files_only,
        torch_dtype=dtype,
        trust_remote_code=True,
    ).to(device)

    if peft_model is not None:
        model = peft_model.from_pretrained(base_model, adapter_dir).to(device)
    else:
        model = base_model
    model.eval()

    logs_dir = Path(args.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    output_path = logs_dir / f"eval_{utc_timestamp()}.jsonl"

    system_prompt = (
        "You are Grona, a concise technical assistant. Answer directly. "
        "Do not invent non-existent APIs."
    )
    results = []
    for case in evaluation_cases():
        prompt = build_prompt(tokenizer, system_prompt, case["prompt"])
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                repetition_penalty=1.18,
                no_repeat_ngram_size=4,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        generated = tokenizer.decode(
            output_ids[0][inputs["input_ids"].shape[-1]:],
            skip_special_tokens=True,
        ).strip()
        score = score_response(generated, case)
        result = {
            "id": case["id"],
            "prompt": case["prompt"],
            "generated": generated,
            "score": score,
        }
        results.append(result)

    with output_path.open("w", encoding="utf-8", newline="\n") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    passed = sum(1 for result in results if result["score"]["passed"])
    total = len(results)
    print("Grona local LoRA heuristic eval")
    print(f"Model:   {args.model_id}")
    print(f"Adapter: {adapter_dir or 'none'}")
    print(f"Output:  {output_path}")
    print(f"Score:   {passed}/{total}")
    print("")
    for result in results:
        status = "PASS" if result["score"]["passed"] else "CHECK"
        print(f"{status} {result['id']}")
    print("")
    print("Note: deterministic substring checks only; this is not an LLM judge or quality proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
