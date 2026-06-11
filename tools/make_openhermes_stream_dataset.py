import argparse
import json
from pathlib import Path


def get_messages(row: dict):
    value = row.get("conversations") or row.get("messages")
    if isinstance(value, list):
        return value
    return None


def msg_role(msg: dict) -> str:
    return str(msg.get("from") or msg.get("role") or msg.get("speaker") or "").lower()


def msg_content(msg: dict) -> str:
    return str(msg.get("value") or msg.get("content") or msg.get("text") or "").strip()


def convert_row(row: dict) -> dict | None:
    messages = get_messages(row)

    if messages:
        user_text = ""
        assistant_text = ""

        for msg in messages:
            if not isinstance(msg, dict):
                continue

            role = msg_role(msg)
            content = msg_content(msg)

            if not content:
                continue

            if role in {"human", "user"} and not user_text:
                user_text = content
            elif role in {"gpt", "assistant"} and user_text and not assistant_text:
                assistant_text = content
                break

        if user_text and assistant_text:
            return {
                "instruction": user_text,
                "input": "",
                "output": assistant_text,
                "source": "teknium/OpenHermes-2.5",
            }

    instruction = str(
        row.get("instruction")
        or row.get("prompt")
        or row.get("question")
        or ""
    ).strip()

    input_text = str(row.get("input") or row.get("context") or "").strip()

    output = str(
        row.get("output")
        or row.get("response")
        or row.get("answer")
        or row.get("completion")
        or ""
    ).strip()

    if instruction and output:
        return {
            "instruction": instruction,
            "input": input_text,
            "output": output,
            "source": "teknium/OpenHermes-2.5",
        }

    return None


def too_long(row: dict, max_chars: int) -> bool:
    return (
        len(row["instruction"]) > max_chars
        or len(row.get("input", "")) > max_chars
        or len(row["output"]) > max_chars
    )


def bad_row(row: dict) -> bool:
    text = (row["instruction"] + "\n" + row["output"]).lower()
    markers = [
        "as an ai language model",
        "i cannot assist",
        "i'm sorry, but i can't",
    ]
    return any(marker in text for marker in markers)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--rows", type=int, default=5000)
    parser.add_argument("--max-chars", type=int, default=6000)
    parser.add_argument("--split", default="train")
    args = parser.parse_args()

    from datasets import load_dataset

    out_path = Path(args.output_jsonl)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("Loading OpenHermes in streaming mode...")
    ds = load_dataset("teknium/OpenHermes-2.5", split=args.split, streaming=True)

    written = 0
    seen = 0
    skipped = 0

    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        for raw in ds:
            seen += 1
            row = convert_row(dict(raw))

            if row is None:
                skipped += 1
                continue

            if too_long(row, args.max_chars) or bad_row(row):
                skipped += 1
                continue

            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1

            if written % 100 == 0:
                print(f"written={written} seen={seen} skipped={skipped}")

            if written >= args.rows:
                break

    print("")
    print(f"Created: {out_path}")
    print(f"Rows:    {written}")
    print(f"Seen:    {seen}")
    print(f"Skipped: {skipped}")

    if written == 0:
        raise SystemExit("No rows written from OpenHermes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())