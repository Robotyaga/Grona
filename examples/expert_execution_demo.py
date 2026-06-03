"""Demonstrate deterministic demo expert execution in Grona."""

from grona import (
    ContextBuilder,
    Orchestrator,
    Router,
    create_default_executor_registry,
    create_default_memory_modules,
    create_default_registry,
)
from grona.cli import format_orchestration_result

TASKS = [
    "Diagnose engine overheating after idling in traffic.",
    "Review this Python package for tests, linting, and exposed secrets.",
    "Plan a video stabilization workflow with codec compression and audio EQ.",
    "Find the PDF manual and summarize the maintenance notes.",
    "Plan the next steps for an ambiguous project report.",
]


def main() -> None:
    router = Router(create_default_registry(), top_k=3)
    orchestrator = Orchestrator(
        router,
        context_builder=ContextBuilder(memory_modules=create_default_memory_modules()),
        executor_registry=create_default_executor_registry(),
    )

    for task in TASKS:
        print("=" * 80)
        print(format_orchestration_result(orchestrator.run(task)))
        print()


if __name__ == "__main__":
    main()
