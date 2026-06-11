import argparse
import json
import random
from pathlib import Path


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def clean_text(value) -> str:
    return str(value or "").strip()


def normalize_openmath(row: dict) -> dict | None:
    problem = clean_text(row.get("problem"))
    solution = clean_text(row.get("generated_solution"))
    answer = clean_text(row.get("expected_answer"))

    if not problem or not solution:
        return None

    output = solution
    if answer:
        output += f"\n\nFinal answer: {answer}"

    return {
        "instruction": problem,
        "input": "",
        "output": output,
        "source": "nvidia/OpenMathInstruct-2",
    }


def normalize_opencode(row: dict) -> dict | None:
    instruction = clean_text(row.get("input"))
    output = clean_text(row.get("output"))

    if not instruction or not output:
        return None

    # Prefer rows with passing tests when metadata exists.
    status = clean_text(row.get("tests_execution_status")).lower()
    avg = row.get("average_test_score")

    if avg not in (None, ""):
        try:
            if float(avg) < 0.8:
                return None
        except Exception:
            pass

    if status and "fail" in status and "pass" not in status:
        return None

    return {
        "instruction": instruction,
        "input": "",
        "output": output,
        "source": "nvidia/OpenCodeInstruct",
    }


def normalize_openhermes(row: dict) -> dict | None:
    conversations = row.get("conversations") or row.get("messages")
    if not isinstance(conversations, list):
        return None

    user_text = ""
    assistant_text = ""

    for msg in conversations:
        if not isinstance(msg, dict):
            continue
        role = clean_text(msg.get("from") or msg.get("role")).lower()
        content = clean_text(msg.get("value") or msg.get("content") or msg.get("text"))
        if not content:
            continue
        if role in {"human", "user"} and not user_text:
            user_text = content
        elif role in {"gpt", "assistant"} and user_text and not assistant_text:
            assistant_text = content
            break

    if not user_text or not assistant_text:
        return None

    return {
        "instruction": user_text,
        "input": "",
        "output": assistant_text,
        "source": "teknium/OpenHermes-2.5",
    }


def normalize_ultrachat(row: dict) -> dict | None:
    messages = row.get("messages")
    if not isinstance(messages, list):
        return None

    user_text = ""
    assistant_text = ""

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = clean_text(msg.get("role")).lower()
        content = clean_text(msg.get("content"))
        if not content:
            continue
        if role == "user" and not user_text:
            user_text = content
        elif role == "assistant" and user_text and not assistant_text:
            assistant_text = content
            break

    if not user_text or not assistant_text:
        return None

    return {
        "instruction": user_text,
        "input": "",
        "output": assistant_text,
        "source": "HuggingFaceH4/ultrachat_200k",
    }


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


def collect_stream(dataset_name, split, rows, normalizer, max_chars, seed):
    from datasets import load_dataset

    print(f"Loading stream: {dataset_name} split={split}")
    ds = load_dataset(dataset_name, split=split, streaming=True)

    out = []
    seen = 0
    skipped = 0

    # Reservoir-ish randomization: streaming + skip with seeded probability.
    rng = random.Random(seed)

    for raw in ds:
        seen += 1

        # avoid always taking first rows
        if rng.random() < 0.15 and seen < rows * 5:
            skipped += 1
            continue

        row = normalizer(dict(raw))
        if row is None:
            skipped += 1
            continue

        if too_long(row, max_chars) or bad_row(row):
            skipped += 1
            continue

        out.append(row)

        if len(out) % 250 == 0:
            print(f"{dataset_name}: collected={len(out)} seen={seen} skipped={skipped}")

        if len(out) >= rows:
            break

    print(f"{dataset_name}: final collected={len(out)} seen={seen} skipped={skipped}")
    return out


def read_jsonl(path: Path):
    rows = []
    if not path.exists():
        print(f"Warning: missing local file: {path}")
        return rows

    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                continue
            instruction = clean_text(obj.get("instruction"))
            output = clean_text(obj.get("output"))
            input_text = clean_text(obj.get("input"))
            if instruction and output:
                rows.append(
                    {
                        "instruction": instruction,
                        "input": input_text,
                        "output": output,
                        "source": obj.get("source", str(path)),
                    }
                )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--openmath-rows", type=int, default=5000)
    parser.add_argument("--opencode-rows", type=int, default=5000)
    parser.add_argument("--openhermes-rows", type=int, default=1000)
    parser.add_argument("--ultrachat-rows", type=int, default=1000)
    parser.add_argument("--grona-jsonl", default="data/grona_donor_mix_001.jsonl")
    parser.add_argument("--corrections-jsonl", default="data/uk_exam_corrections_002.jsonl")
    parser.add_argument("--corrections-repeat", type=int, default=8)
    parser.add_argument("--max-chars", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    rows = []

    rows.extend(
        collect_stream(
            "nvidia/OpenMathInstruct-2",
            "train_1M",
            args.openmath_rows,
            normalize_openmath,
            args.max_chars,
            args.seed + 1,
        )
    )

    rows.extend(
        collect_stream(
            "nvidia/OpenCodeInstruct",
            "train",
            args.opencode_rows,
            normalize_opencode,
            args.max_chars,
            args.seed + 2,
        )
    )

    if args.openhermes_rows > 0:
        rows.extend(
            collect_stream(
                "teknium/OpenHermes-2.5",
                "train",
                args.openhermes_rows,
                normalize_openhermes,
                args.max_chars,
                args.seed + 3,
            )
        )

    if args.ultrachat_rows > 0:
        rows.extend(
            collect_stream(
                "HuggingFaceH4/ultrachat_200k",
                "train_sft",
                args.ultrachat_rows,
                normalize_ultrachat,
                args.max_chars,
                args.seed + 4,
            )
        )

    grona_rows = read_jsonl(Path(args.grona_jsonl))
    correction_rows = read_jsonl(Path(args.corrections_jsonl))

    rows.extend(grona_rows)

    for _ in range(args.corrections_repeat):
        rows.extend(correction_rows)

    random.shuffle(rows)

    out_path = Path(args.output_jsonl)
    write_jsonl(out_path, rows)

    print("")
    print(f"Created: {out_path}")
    print(f"Total rows: {len(rows)}")
    print(f"Grona local rows: {len(grona_rows)}")
    print(f"Correction rows: {len(correction_rows)} x {args.corrections_repeat}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())