import argparse
from pathlib import Path

CONFIRMATION = "I_UNDERSTAND_THIS_LOADS_LOCAL_MODEL"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--adapter-dir", required=True)
    parser.add_argument("--tokenizer-dir", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--do-sample", action="store_true")
    parser.add_argument("--confirmation-token", required=True)
    args = parser.parse_args()

    if args.confirmation_token != CONFIRMATION:
        raise SystemExit(f"confirmation token must be exactly: {CONFIRMATION}")

    adapter_dir = Path(args.adapter_dir)
    tokenizer_dir = Path(args.tokenizer_dir)

    if not adapter_dir.exists():
        raise SystemExit(f"adapter_dir does not exist: {adapter_dir}")
    if not tokenizer_dir.exists():
        raise SystemExit(f"tokenizer_dir does not exist: {tokenizer_dir}")

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_dir,
        trust_remote_code=True,
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=dtype,
        trust_remote_code=True,
    ).to(device)

    model = PeftModel.from_pretrained(base_model, adapter_dir).to(device)
    model.eval()

    messages = [
        {
            "role": "system",
            "content": "You are Grona, a concise technical assistant for modular sparse AI architecture.",
        },
        {
            "role": "user",
            "content": args.prompt,
        },
    ]

    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        text = (
            "<|im_start|>system\n"
            "You are Grona, a concise technical assistant for modular sparse AI architecture.\n"
            "<|im_end|>\n"
            "<|im_start|>user\n"
            f"{args.prompt}\n"
            "<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

    inputs = tokenizer(text, return_tensors="pt").to(device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            do_sample=args.do_sample,
            temperature=args.temperature if args.do_sample else None,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated = tokenizer.decode(
        output_ids[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True,
    )

    print("PROMPT:")
    print(args.prompt)
    print("")
    print("GENERATED:")
    print(generated.strip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())