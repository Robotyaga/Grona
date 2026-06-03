"""Demonstrate Grona's lightweight memory/retrieval stub layer."""

from grona import (
    ContextBuilder,
    Orchestrator,
    Router,
    create_default_memory_modules,
    create_default_registry,
)
from grona.cli import format_orchestration_result

TASKS = [
    "Analyze engine overheating symptoms and recommend first inspection steps.",
    "Review firewall logs for suspicious port scans and exposed secrets.",
    "Refactor this Python package and improve tests and linting.",
    "Plan a video stabilization workflow with codec compression and audio EQ.",
    "Find the PDF manual and summarize the maintenance notes.",
    "Review this repository report for code, security, documents, and planning risks.",
]


def main() -> None:
    router = Router(create_default_registry(), top_k=3)
    plain_orchestrator = Orchestrator(router)
    memory_orchestrator = Orchestrator(
        router,
        context_builder=ContextBuilder(memory_modules=create_default_memory_modules()),
    )

    print("Without memory")
    print("=" * 80)
    print(format_orchestration_result(plain_orchestrator.run(TASKS[0])))

    print("\nWith demo memory")
    for task in TASKS:
        print("=" * 80)
        print(format_orchestration_result(memory_orchestrator.run(task)))
        print()


if __name__ == "__main__":
    main()
