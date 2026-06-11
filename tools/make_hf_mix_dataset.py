import argparse
import json
import random
from pathlib import Path

REMOTE_DATASET_DEFAULT = "HuggingFaceH4/CodeAlpaca_20K"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{line_no}: row must be object")
            instruction = str(obj.get("instruction", "")).strip()
            input_text = str(obj.get("input", "")).strip()
            output = str(obj.get("output", "")).strip()
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


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_hf_row(row: dict) -> dict | None:
    instruction = str(row.get("instruction", "") or row.get("prompt", "")).strip()
    input_text = str(row.get("input", "") or row.get("context", "")).strip()
    output = str(
        row.get("output", "")
        or row.get("response", "")
        or row.get("completion", "")
    ).strip()

    if not instruction or not output:
        return None

    return {
        "instruction": instruction,
        "input": input_text,
        "output": output,
        "source": "huggingface",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hf-dataset", default=REMOTE_DATASET_DEFAULT)
    parser.add_argument("--hf-split", default="train")
    parser.add_argument("--grona-jsonl", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--hf-rows", type=int, default=500)
    parser.add_argument("--grona-repeat", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    grona_rows = read_jsonl(Path(args.grona_jsonl))
    if not grona_rows:
        raise SystemExit("No valid Grona rows found")

    print(f"Loading HF dataset: {args.hf_dataset} split={args.hf_split}")

    from datasets import load_dataset

    ds = load_dataset(args.hf_dataset, split=args.hf_split)

    hf_rows = []
    indices = list(range(len(ds)))
    rng.shuffle(indices)

    for idx in indices:
        row = normalize_hf_row(dict(ds[idx]))
        if row is None:
            continue
        hf_rows.append(row)
        if len(hf_rows) >= args.hf_rows:
            break

    if not hf_rows:
        raise SystemExit("No usable HF rows found")

    mixed = []

    for row in grona_rows:
        for _ in range(args.grona_repeat):
            r = dict(row)
            r["source"] = "grona"
            mixed.append(r)

    mixed.extend(hf_rows)
    rng.shuffle(mixed)

    write_jsonl(Path(args.output_jsonl), mixed)

    print("Created mixed dataset")
    print(f"Grona rows:       {len(grona_rows)}")
    print(f"Grona repeat:     {args.grona_repeat}")
    print(f"HF rows:          {len(hf_rows)}")
    print(f"Total rows:       {len(mixed)}")
    print(f"Output:           {args.output_jsonl}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())