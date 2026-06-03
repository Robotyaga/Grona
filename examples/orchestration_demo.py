"""Demonstrate Grona's route-scoped context and orchestration prototype."""

from grona import Orchestrator, Router, create_default_registry
from grona.cli import format_orchestration_result

TASKS = [
    "Analyze engine overheating symptoms and recommend the first inspection steps.",
    "Review this Python script for security issues and suspicious network behavior.",
    "Find the PDF manual in my document archive and summarize maintenance notes.",
]


def main() -> None:
    router = Router(create_default_registry(), top_k=3)
    orchestrator = Orchestrator(router)

    for task in TASKS:
        print("=" * 80)
        print(format_orchestration_result(orchestrator.run(task)))
        print()


if __name__ == "__main__":
    main()
