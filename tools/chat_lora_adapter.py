import argparse
from pathlib import Path

CONFIRMATION = "I_UNDERSTAND_THIS_LOADS_LOCAL_MODEL"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--adapter-dir", required=True)
    parser.add_argument("--tokenizer-dir", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--do-sample", action="store_true")
    parser.add_argument("--repetition-penalty", type=float, default=1.18)
    parser.add_argument("--no-repeat-ngram-size", type=int, default=4)
    parser.add_argument(
        "--system",
        default=(
            "You are Grona, a concise technical assistant for modular sparse AI architecture. "
            "Answer clearly and do not invent non-existent APIs."
        ),
    )
    parser.add_argument("--memory-file", default="")
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

    system_prompt = args.system
    if args.memory_file:
        memory_path = Path(args.memory_file)
        if not memory_path.exists():
            raise SystemExit(f"memory_file does not exist: {memory_path}")
        memory_text = memory_path.read_text(encoding="utf-8").strip()
        if memory_text:
            system_prompt = (
                f"{system_prompt}\n\n"
                "Persistent local notes:\n"
                f"{memory_text}"
            )

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_dir,
        trust_remote_code=True,
    )

    print("Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=dtype,
        trust_remote_code=True,
    ).to(device)

    print("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(base_model, adapter_dir).to(device)
    model.eval()

    print("")
    print("Grona LoRA chat ready.")
    print("Type /exit to quit, /clear to reset context.")
    print("")

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    while True:
        try:
            user_text = input("you> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("")
            break

        if not user_text:
            continue

        if user_text.lower() in {"/exit", "exit", "quit"}:
            break

        if user_text.lower() == "/clear":
            messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                }
            ]
            print("context cleared")
            continue

        messages.append({"role": "user", "content": user_text})

        if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            prompt_parts = []
            for msg in messages:
                prompt_parts.append(f"<|im_start|>{msg['role']}\n{msg['content']}\n<|im_end|>")
            prompt_parts.append("<|im_start|>assistant\n")
            prompt = "\n".join(prompt_parts)

        inputs = tokenizer(prompt, return_tensors="pt").to(device)

        with torch.no_grad():
            generate_kwargs = {
                "max_new_tokens": args.max_new_tokens,
                "pad_token_id": tokenizer.eos_token_id,
                "eos_token_id": tokenizer.eos_token_id,
                "repetition_penalty": args.repetition_penalty,
                "no_repeat_ngram_size": args.no_repeat_ngram_size,
            }

            if args.do_sample:
                generate_kwargs.update(
                    {
                        "do_sample": True,
                        "temperature": args.temperature,
                        "top_p": args.top_p,
                        "top_k": args.top_k,
                    }
                )
            else:
                generate_kwargs.update({"do_sample": False})

            output_ids = model.generate(**inputs, **generate_kwargs)

        generated = tokenizer.decode(
            output_ids[0][inputs["input_ids"].shape[-1]:],
            skip_special_tokens=True,
        ).strip()

        print("")
        print(f"grona> {generated}")
        print("")

        messages.append({"role": "assistant", "content": generated})

    print("bye")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
