import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "grona_repo_grounded.jsonl"

PY_DIRS = [
    ROOT / "src" / "grona",
    ROOT / "tests",
]

DOC_FILES = [
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
]

DOC_DIRS = [
    ROOT / "docs",
]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def public_name(name: str) -> bool:
    return not name.startswith("_")


def parse_python_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)

    classes = []
    functions = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and public_name(node.name):
            methods = []
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and public_name(child.name):
                    methods.append(child.name)
            classes.append({"name": node.name, "methods": methods})

        if isinstance(node, ast.FunctionDef) and public_name(node.name):
            functions.append(node.name)

    return {
        "path": rel(path),
        "classes": classes,
        "functions": functions,
        "text": text,
    }


def chunk_text(text: str, max_chars: int = 3500) -> list[str]:
    chunks = []
    current = []

    for line in text.splitlines():
        current.append(line)
        joined = "\n".join(current)
        if len(joined) >= max_chars:
            chunks.append(joined)
            current = []

    if current:
        chunks.append("\n".join(current))

    return chunks


def main() -> int:
    rows = []

    # Hard negative grounding examples.
    rows.extend(
        [
            {
                "instruction": "Does Grona expose a public class named Grona?",
                "input": "",
                "output": "No. Do not invent a public Grona class unless it exists in the repository. Use the actual modules, classes, functions, and CLI commands present in the codebase.",
                "source": "repo-grounding-negative",
            },
            {
                "instruction": "Does Grona have public methods named add_task(), create_model(), or run() on a Grona object?",
                "input": "",
                "output": "No. Do not claim that Grona has add_task(), create_model(), or run() unless those methods exist in the actual code. When unsure, describe a conceptual router example instead of inventing API.",
                "source": "repo-grounding-negative",
            },
            {
                "instruction": "When showing a Python routing example for Grona, what should you avoid?",
                "input": "",
                "output": "Avoid Flask/FastAPI web routes and avoid non-existent APIs such as Grona(), add_task(), create_model(), or execute(). Show a small conceptual function or use actual public classes from the repository.",
                "source": "repo-grounding-negative",
            },
            {
                "instruction": "Відповідай українською. Чи має Grona клас Grona або методи add_task(), create_model(), run()?",
                "input": "",
                "output": "Ні. Якщо такі класи або методи явно не існують у коді репозиторію, Grona не повинна їх вигадувати. Треба або використовувати реальні API з репозиторію, або чесно показувати концептуальний приклад.",
                "source": "repo-grounding-negative-uk",
            },
        ]
    )

    for base in PY_DIRS:
        if not base.exists():
            continue

        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue

            try:
                info = parse_python_file(path)
            except Exception:
                continue

            class_lines = []
            for cls in info["classes"]:
                if cls["methods"]:
                    class_lines.append(
                        f"- {cls['name']} methods: {', '.join(cls['methods'])}"
                    )
                else:
                    class_lines.append(f"- {cls['name']}")

            function_lines = [f"- {fn}" for fn in info["functions"]]

            api_summary = "\n".join(
                [
                    f"File: {info['path']}",
                    "",
                    "Public classes:",
                    "\n".join(class_lines) if class_lines else "- none",
                    "",
                    "Public functions:",
                    "\n".join(function_lines) if function_lines else "- none",
                ]
            )

            rows.append(
                {
                    "instruction": f"List the real public API symbols in {info['path']}.",
                    "input": "",
                    "output": api_summary,
                    "source": "repo-python-api",
                }
            )

            rows.append(
                {
                    "instruction": f"Based on the actual repository file {info['path']}, explain what this module contains.",
                    "input": info["text"][:3500],
                    "output": api_summary,
                    "source": "repo-python-explain",
                }
            )

    for path in DOC_FILES:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            for i, chunk in enumerate(chunk_text(text)):
                rows.append(
                    {
                        "instruction": f"Summarize this Grona repository document chunk from {rel(path)}.",
                        "input": chunk,
                        "output": f"This chunk comes from {rel(path)} and documents Grona. Use it as repository-grounded context; do not invent APIs that are not present in the repository.",
                        "source": "repo-doc",
                        "chunk": i,
                    }
                )

    for base in DOC_DIRS:
        if not base.exists():
            continue

        for path in sorted(base.rglob("*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            for i, chunk in enumerate(chunk_text(text)):
                rows.append(
                    {
                        "instruction": f"Summarize this Grona documentation chunk from {rel(path)}.",
                        "input": chunk,
                    "output": "This documentation chunk describes Grona behavior or architecture. Use the documented concepts and avoid inventing unmentioned runtime APIs.",
                        "source": "repo-doc",
                        "chunk": i,
                    }
                )

    write_jsonl(OUT, rows)

    print(f"Created {OUT}")
    print(f"Rows: {len(rows)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
