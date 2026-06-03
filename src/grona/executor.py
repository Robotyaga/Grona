"""Deterministic expert execution interfaces and demo executors."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from .context import ContextItem
from .feedback import Metadata


@dataclass(frozen=True)
class ExpertResult:
    """Structured output from an executable expert."""

    module_name: str
    task: str
    summary: str
    details: tuple[str, ...] = ()
    confidence: float = 0.0
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", tuple(self.details))
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_text(self) -> str:
        """Format the expert result for humans."""
        lines = [
            f"Expert: {self.module_name}",
            f"Summary: {self.summary}",
            f"Confidence: {self.confidence:.2f}",
            "Details:",
        ]
        if self.details:
            lines.extend(f"- {detail}" for detail in self.details)
        else:
            lines.append("- none")
        return "\n".join(lines)


class ExecutableExpert(Protocol):
    """Minimal interface for deterministic or real future expert executors."""

    module_name: str

    def execute(self, task: str, context_items: Sequence[ContextItem]) -> ExpertResult:
        """Execute an expert against a task and focused context."""


class ExpertExecutorRegistry:
    """Registry mapping routed module names to executable experts."""

    def __init__(self, executors: Iterable[ExecutableExpert] = ()) -> None:
        self._executors: dict[str, ExecutableExpert] = {}
        for executor in executors:
            self.register(executor)

    def register(self, executor: ExecutableExpert) -> None:
        """Register an executor by its module name."""
        self._executors[executor.module_name] = executor

    def get(self, module_name: str) -> ExecutableExpert | None:
        """Return an executor for a module name, if registered."""
        return self._executors.get(module_name)

    def list(self) -> tuple[ExecutableExpert, ...]:
        """Return registered executors in deterministic name order."""
        return tuple(self._executors[name] for name in sorted(self._executors))

    def missing(self, module_names: Sequence[str]) -> tuple[str, ...]:
        """Return module names that do not have registered executors."""
        return tuple(name for name in module_names if name not in self._executors)


class CodeExpertExecutor:
    """Deterministic demo executor for code tasks."""

    module_name = "code-assistant"

    def execute(self, task: str, context_items: Sequence[ContextItem]) -> ExpertResult:
        details = (
            "Review package structure, function boundaries, and error handling.",
            "Run or add focused tests before changing behavior.",
            "Use linting/static analysis signals as a deterministic quality check.",
            *context_details(context_items, "code"),
        )
        return expert_result(
            self.module_name,
            task,
            "Prepared a code review and debugging outline.",
            details,
            context_items,
        )


class AutomotiveDiagnosticsExpertExecutor:
    """Deterministic demo executor for automotive diagnostics tasks."""

    module_name = "automotive-diagnostics"

    def execute(self, task: str, context_items: Sequence[ContextItem]) -> ExpertResult:
        details = (
            "Inspect coolant level and look for air pockets or visible leaks.",
            "Check thermostat opening behavior and coolant circulation.",
            "Verify fan activation and radiator flow under the reported conditions.",
            *context_details(context_items, "automotive"),
        )
        return expert_result(
            self.module_name,
            task,
            "Prepared a diagnostic reasoning outline for an automotive issue.",
            details,
            context_items,
        )


class CybersecurityExpertExecutor:
    """Deterministic demo executor for cybersecurity tasks."""

    module_name = "cybersecurity-scanner"

    def execute(self, task: str, context_items: Sequence[ContextItem]) -> ExpertResult:
        details = (
            "Review input validation and authentication boundaries.",
            "Check secrets handling, permission scope, and exposed services.",
            "Inspect logs for repeated sources, suspicious ports, and unexpected traffic.",
            *context_details(context_items, "security"),
        )
        return expert_result(
            self.module_name,
            task,
            "Prepared a deterministic cybersecurity review outline.",
            details,
            context_items,
        )


class MediaWorkflowExpertExecutor:
    """Deterministic demo executor for media workflow tasks."""

    module_name = "media-video-tool"

    def execute(self, task: str, context_items: Sequence[ContextItem]) -> ExpertResult:
        details = (
            "Identify codec, compression, and export constraints.",
            "Plan color workflow, stabilization, and audio cleanup steps.",
            "Preserve source metadata and define the output format before processing.",
            *context_details(context_items, "media"),
        )
        return expert_result(
            self.module_name,
            task,
            "Prepared a media workflow outline.",
            details,
            context_items,
        )


class DocumentSearchExpertExecutor:
    """Deterministic demo executor for document search tasks."""

    module_name = "document-search"

    def execute(self, task: str, context_items: Sequence[ContextItem]) -> ExpertResult:
        details = (
            "Identify document sources, indexing fields, and extraction boundaries.",
            "Keep citations or source references attached to summaries.",
            "Separate search terms, retrieved evidence, and summary scope.",
            *context_details(context_items, "document"),
        )
        return expert_result(
            self.module_name,
            task,
            "Prepared a document retrieval outline.",
            details,
            context_items,
        )


class GeneralReasoningExpertExecutor:
    """Deterministic demo executor for general planning tasks."""

    module_name = "general-reasoning"

    def execute(self, task: str, context_items: Sequence[ContextItem]) -> ExpertResult:
        details = (
            "Clarify the goal, constraints, and success criteria.",
            "Break the task into inspectable steps before choosing an execution path.",
            "Keep uncertainty visible instead of hiding it behind a single answer.",
            *context_details(context_items, "general"),
        )
        return expert_result(
            self.module_name,
            task,
            "Prepared a general reasoning outline.",
            details,
            context_items,
        )


def expert_result(
    module_name: str,
    task: str,
    summary: str,
    details: Sequence[str],
    context_items: Sequence[ContextItem],
) -> ExpertResult:
    """Create a deterministic expert result with context-aware confidence."""
    return ExpertResult(
        module_name=module_name,
        task=task,
        summary=summary,
        details=tuple(details),
        confidence=confidence_from_context(context_items),
        metadata={
            "executor_kind": "deterministic_demo",
            "context_count": len(context_items),
        },
    )


def confidence_from_context(context_items: Sequence[ContextItem]) -> float:
    """Estimate deterministic demo confidence from available context."""
    return round(min(0.95, 0.55 + (0.08 * len(context_items))), 4)


def context_details(context_items: Sequence[ContextItem], topic: str) -> tuple[str, ...]:
    """Create short detail bullets from the most relevant context items."""
    selected = sorted(context_items, key=lambda item: (-item.relevance, item.source))[:2]
    return tuple(
        f"Use {topic} context from {item.source}: {shorten(item.content)}"
        for item in selected
    )


def shorten(text: str, limit: int = 120) -> str:
    """Shorten context text for readable deterministic output."""
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def create_default_executor_registry() -> ExpertExecutorRegistry:
    """Create demo executors for Grona's default modules."""
    return ExpertExecutorRegistry(
        (
            CodeExpertExecutor(),
            AutomotiveDiagnosticsExpertExecutor(),
            CybersecurityExpertExecutor(),
            MediaWorkflowExpertExecutor(),
            DocumentSearchExpertExecutor(),
            GeneralReasoningExpertExecutor(),
        )
    )
