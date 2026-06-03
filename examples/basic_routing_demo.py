"""Demonstrate Grona's lightweight routing prototype."""

from grona import Router, create_default_registry
from grona.cli import format_decision


TASKS = [
    "Refactor this Python function and explain why the test fails.",
    "Analyze why my car engine overheats while idling in traffic.",
    "Review firewall logs for suspicious port scans and malware indicators.",
    "Create thumbnails from a video clip and extract audio metadata.",
    "Find the PDF manual in my document archive and summarize the maintenance notes.",
    "Analyze this repository report and plan whether the issue is code, documentation, or search related.",
]


def main() -> None:
    router = Router(create_default_registry(), top_k=3)

    for task in TASKS:
        decision = router.route(task)
        print("=" * 80)
        print(format_decision(decision))
        print("\nActivated outputs:")
        for match, output in router.run(task):
            print(f"- {match.module.name}: {output}")
        print()


if __name__ == "__main__":
    main()
