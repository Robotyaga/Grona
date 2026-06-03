"""Demonstrate Grona route feedback records and history summaries."""

import grona


TASKS = [
    "Refactor this Python function and explain why the test fails.",
    "Analyze why my car engine overheats while idling in traffic.",
    "Review firewall logs for suspicious port scans and malware indicators.",
    "Find the PDF manual in my document archive and summarize the maintenance notes.",
]


def main() -> None:
    router = grona.Router(grona.create_default_registry(), top_k=3)
    store = grona.InMemoryFeedbackStore()

    for index, task in enumerate(TASKS, start=1):
        decision = router.route(task)
        record = grona.FeedbackRecord.from_decision(
            decision,
            rating=5 if index <= 2 else None,
            success=index != 3,
            notes="Demo route history record.",
            metadata={"demo_index": index},
        )
        store.add(record)
        print(f"Stored feedback for task {index}: {record.route_summary}")

    summary = grona.summarize_feedback(store.list())
    print("\nRoute history summary")
    print(f"Total records: {summary.total_records}")
    print(f"Average confidence: {summary.average_confidence:.4f}")
    print(f"Success count: {summary.success_count}")
    print(f"Failure count: {summary.failure_count}")
    print("Most selected modules:")
    for module_name, count in summary.most_selected_modules:
        print(f"- {module_name}: {count}")


if __name__ == "__main__":
    main()
