import json
import sys
from pathlib import Path

path = Path(sys.argv[1])

ok = 0

with path.open("r", encoding="utf-8-sig") as f:
    for line_no, line in enumerate(f, start=1):
        raw = line.rstrip("\n")
        line = raw.strip()

        if not line:
            continue

        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"BAD line {line_no}: {e}")
            print(raw)
            raise SystemExit(1) from None

        if not isinstance(obj, dict):
            print(f"BAD line {line_no}: not a JSON object")
            print(raw)
            raise SystemExit(1)

        for key in ("instruction", "output"):
            if not str(obj.get(key, "")).strip():
                print(f"BAD line {line_no}: empty required field: {key}")
                print(raw)
                raise SystemExit(1)

        ok += 1

print(f"OK: {ok} valid JSONL rows")
