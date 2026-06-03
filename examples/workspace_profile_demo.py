"""Demonstrate Grona workspace profiles."""

from grona import (
    Router,
    create_automotive_workspace_profile,
    create_cybersecurity_workspace_profile,
    create_default_registry,
    create_default_workspace_profile,
    create_document_research_workspace_profile,
    create_media_workflow_workspace_profile,
    filter_modules_for_workspace,
)

TASKS = (
    "Diagnose engine overheating and coolant loss",
    "Review this Python script for security issues",
    "Plan a MotionCam RAW video workflow",
    "Find notes about document indexing and citations",
)


def print_workspace_route(profile_name: str, task: str) -> None:
    profile_map = {
        "default": create_default_workspace_profile,
        "automotive": create_automotive_workspace_profile,
        "cybersecurity": create_cybersecurity_workspace_profile,
        "media": create_media_workflow_workspace_profile,
        "documents": create_document_research_workspace_profile,
    }
    profile = profile_map[profile_name]()
    registry = filter_modules_for_workspace(create_default_registry(), profile)
    decision = Router(registry, top_k=3).route(task)

    print("=" * 80)
    print(f"Workspace: {profile.name}")
    print(f"Domains: {', '.join(profile.enabled_domains) or 'all default domains'}")
    print(f"Modules: {', '.join(registry.names())}")
    print(f"Task: {task}")
    print("Selected:")
    for match in decision.selected_modules:
        print(f"- {match.module.name} ({match.score:.1f})")
    print()


def main() -> None:
    for task in TASKS:
        print_workspace_route("default", task)
    print_workspace_route("automotive", TASKS[0])
    print_workspace_route("cybersecurity", TASKS[1])
    print_workspace_route("media", TASKS[2])
    print_workspace_route("documents", TASKS[3])


if __name__ == "__main__":
    main()
