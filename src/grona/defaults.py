"""Default mock modules for Grona demos and tests."""

from __future__ import annotations

from .module import ExpertModule, TaskContext
from .registry import ModuleRegistry


def create_default_registry() -> ModuleRegistry:
    """Create a demo registry with heterogeneous mock expert modules."""
    return ModuleRegistry(
        [
            ExpertModule(
                name="code-assistant",
                domain="code software programming",
                capabilities=("debugging", "refactoring", "static analysis"),
                keywords=(
                    "python",
                    "function",
                    "bug",
                    "repository",
                    "test",
                    "class",
                    "api",
                    "code",
                ),
                handler=_mock_handler("Code assistant"),
                description="Inspects code-oriented tasks and suggests implementation steps.",
                cost=2,
            ),
            ExpertModule(
                name="automotive-diagnostics",
                domain="automotive car engine vehicle",
                capabilities=("diagnostics", "maintenance", "inspection"),
                keywords=(
                    "overheat",
                    "overheating",
                    "idle",
                    "idling",
                    "coolant",
                    "radiator",
                    "engine",
                    "traffic",
                    "car",
                ),
                handler=_mock_handler("Automotive diagnostics"),
                description="Reasons about vehicle symptoms and likely inspection paths.",
                cost=2,
            ),
            ExpertModule(
                name="cybersecurity-scanner",
                domain="cybersecurity security network",
                capabilities=("threat analysis", "vulnerability review", "incident triage"),
                keywords=("malware", "phishing", "firewall", "port", "breach", "scan", "logs"),
                handler=_mock_handler("Cybersecurity scanner"),
                description="Reviews security-oriented tasks and risk indicators.",
                cost=3,
            ),
            ExpertModule(
                name="media-video-tool",
                domain="media video photo audio",
                capabilities=("transcoding", "metadata extraction", "workflow automation"),
                keywords=("clip", "video", "thumbnail", "frames", "audio", "render", "photo"),
                handler=_mock_handler("Media/video tool"),
                description="Handles media workflow and processing tasks.",
                cost=2,
            ),
            ExpertModule(
                name="document-search",
                domain="document search knowledge retrieval",
                capabilities=("search", "summarization", "evidence lookup"),
                keywords=("pdf", "document", "manual", "notes", "find", "archive", "report"),
                handler=_mock_handler("Document search"),
                description="Finds and summarizes information from document collections.",
                cost=1,
            ),
            ExpertModule(
                name="general-reasoning",
                domain="general reasoning planning",
                capabilities=("triage", "decomposition", "explanation"),
                keywords=("analyze", "explain", "plan", "compare", "decide", "ambiguous", "help"),
                handler=_mock_handler("General reasoning"),
                description="Provides lightweight fallback reasoning for broad or ambiguous tasks.",
                cost=1,
            ),
        ]
    )


def _mock_handler(label: str):
    def handle(task: str, context: TaskContext) -> str:
        selected = context.get("selected_modules", "unknown route")
        return f"{label} handled a scoped part of the task. Route: {selected}."

    return handle
