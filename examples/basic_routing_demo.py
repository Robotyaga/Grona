"""Demonstrate Grona's first lightweight routing prototype."""

from pathlib import Path
from sys import path

path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from grona import ExpertModule, ModuleRegistry, Router  # noqa: E402


def make_mock_handler(label: str):
    def handle(task: str, context):
        selected = context.get("selected_modules", "unknown route")
        return f"{label} handled a scoped part of the task. Route: {selected}."

    return handle


def build_registry() -> ModuleRegistry:
    return ModuleRegistry(
        [
            ExpertModule(
                name="code-assistant",
                domain="code software programming",
                capabilities=("debugging", "refactoring", "static analysis"),
                keywords=("python", "function", "bug", "repository", "test", "class", "api"),
                handler=make_mock_handler("Code assistant"),
                description="Inspects code-oriented tasks and suggests implementation steps.",
                cost=2,
            ),
            ExpertModule(
                name="automotive-diagnostics",
                domain="automotive car engine vehicle",
                capabilities=("diagnostics", "maintenance", "inspection"),
                keywords=("overheat", "overheating", "idle", "coolant", "radiator", "engine", "traffic"),
                handler=make_mock_handler("Automotive diagnostics"),
                description="Reasons about vehicle symptoms and likely inspection paths.",
                cost=2,
            ),
            ExpertModule(
                name="cybersecurity-scanner",
                domain="cybersecurity security network",
                capabilities=("threat analysis", "vulnerability review", "incident triage"),
                keywords=("malware", "phishing", "firewall", "port", "breach", "scan", "logs"),
                handler=make_mock_handler("Cybersecurity scanner"),
                description="Reviews security-oriented tasks and risk indicators.",
                cost=3,
            ),
            ExpertModule(
                name="media-video-tool",
                domain="media video photo audio",
                capabilities=("transcoding", "metadata extraction", "workflow automation"),
                keywords=("clip", "video", "thumbnail", "frames", "audio", "render", "photo"),
                handler=make_mock_handler("Media/video tool"),
                description="Handles media workflow and processing tasks.",
                cost=2,
            ),
            ExpertModule(
                name="document-search",
                domain="document search knowledge retrieval",
                capabilities=("search", "summarization", "evidence lookup"),
                keywords=("pdf", "document", "manual", "notes", "find", "archive", "report"),
                handler=make_mock_handler("Document search"),
                description="Finds and summarizes information from document collections.",
                cost=1,
            ),
        ]
    )


def print_decision(router: Router, task: str) -> None:
    decision = router.route(task)

    print("=" * 80)
    print(f"Task: {task}")
    print("\nSelected modules:")
    for match in decision.selected_modules:
        print(f"- {match.module.name} (score {match.score:.1f})")
        for reason in match.reasons:
            print(f"  reason: {reason}")

    print("\nSkipped modules:")
    for match in decision.skipped_modules:
        print(f"- {match.module.name} (score {match.score:.1f})")
        print(f"  reason: {'; '.join(match.reasons)}")

    print("\nActivated outputs:")
    for match, output in router.run(task):
        print(f"- {match.module.name}: {output}")
    print()


def main() -> None:
    router = Router(build_registry(), top_k=2)
    tasks = [
        "Refactor this Python function and explain why the test fails.",
        "Analyze why my car engine overheats while idling in traffic.",
        "Review firewall logs for suspicious port scans and malware indicators.",
        "Create thumbnails from a video clip and extract audio metadata.",
        "Find the PDF manual in my document archive and summarize the maintenance notes.",
    ]

    for task in tasks:
        print_decision(router, task)


if __name__ == "__main__":
    main()
