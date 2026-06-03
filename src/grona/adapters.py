"""Safe deterministic execution adapter contracts for Grona."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from .context import ContextItem
from .executor import ExpertResult, confidence_from_context, context_details
from .feedback import Metadata


@dataclass(frozen=True)
class ExecutionRequest:
    """Normalized input passed from orchestration to an execution adapter."""

    task: str
    module_name: str
    context_items: tuple[ContextItem, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        task: str,
        module_name: str,
        context_items: Sequence[ContextItem] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "task", task)
        object.__setattr__(self, "module_name", module_name)
        object.__setattr__(self, "context_items", tuple(context_items))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not task:
            raise ValueError("execution request task cannot be empty")
        if not module_name:
            raise ValueError("execution request module_name cannot be empty")


class ExecutionAdapter(Protocol):
    """Bridge between a selected expert module and an execution backend."""

    name: str
    description: str
    supported_modules: Sequence[str]

    def execute(self, request: ExecutionRequest) -> ExpertResult:
        """Execute a normalized request and return an expert result."""


class ExecutionAdapterRegistry:
    """Registry for adapters keyed by the module names they support."""

    def __init__(self, adapters: Iterable[ExecutionAdapter] = ()) -> None:
        self._adapters: list[ExecutionAdapter] = []
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: ExecutionAdapter) -> None:
        """Register an adapter if an adapter with the same name is not present."""
        self._adapters = [item for item in self._adapters if item.name != adapter.name]
        self._adapters.append(adapter)
        self._adapters.sort(key=lambda item: item.name)

    def list(self) -> tuple[ExecutionAdapter, ...]:
        """Return adapters in deterministic name order."""
        return tuple(self._adapters)

    def get(self, module_name: str) -> ExecutionAdapter | None:
        """Return the first adapter that supports a module name."""
        for adapter in self._adapters:
            if adapter_supports_module(adapter, module_name):
                return adapter
        return None

    def missing(self, module_names: Sequence[str]) -> tuple[str, ...]:
        """Return selected module names with no supporting adapter."""
        return tuple(name for name in module_names if self.get(name) is None)


@dataclass(frozen=True)
class StaticExecutionAdapter:
    """Deterministic adapter backed by static per-module responses."""

    name: str
    responses: Mapping[str, tuple[str, tuple[str, ...]]]
    description: str = "Deterministic static execution adapter."

    @property
    def supported_modules(self) -> tuple[str, ...]:
        """Return module names with static responses."""
        return tuple(sorted(self.responses))

    def execute(self, request: ExecutionRequest) -> ExpertResult:
        """Return the configured deterministic response for a module."""
        fallback = (
            f"No static response configured for {request.module_name}.",
            ("No deterministic adapter details are available for this module.",),
        )
        summary, details = self.responses.get(request.module_name, fallback)
        return ExpertResult(
            module_name=request.module_name,
            task=request.task,
            summary=summary,
            details=tuple(
                (
                    *details,
                    *context_details(request.context_items, request.module_name),
                )
            ),
            confidence=confidence_from_context(request.context_items),
            metadata=adapter_metadata(self, request, "static"),
        )


@dataclass(frozen=True)
class PythonFunctionAdapter:
    """Adapter that wraps a safe local Python callable."""

    name: str
    supported_modules: tuple[str, ...]
    handler: Callable[[ExecutionRequest], ExpertResult]
    description: str = "Deterministic Python function execution adapter."

    def __init__(
        self,
        name: str,
        supported_modules: Sequence[str],
        handler: Callable[[ExecutionRequest], ExpertResult],
        description: str = "Deterministic Python function execution adapter.",
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "supported_modules", tuple(supported_modules))
        object.__setattr__(self, "handler", handler)
        object.__setattr__(self, "description", description)

    def execute(self, request: ExecutionRequest) -> ExpertResult:
        """Run the wrapped callable and tag the result with adapter metadata."""
        result = self.handler(request)
        merged_metadata = {
            **result.metadata,
            **adapter_metadata(self, request, "python_function"),
        }
        return ExpertResult(
            module_name=result.module_name,
            task=result.task,
            summary=result.summary,
            details=result.details,
            confidence=result.confidence,
            metadata=merged_metadata,
        )


@dataclass(frozen=True)
class NoopExecutionAdapter:
    """Adapter that reports unavailable execution without failing."""

    name: str = "noop-adapter"
    description: str = "No execution adapter; returns an unavailable result."
    supported_modules: tuple[str, ...] = ()

    def execute(self, request: ExecutionRequest) -> ExpertResult:
        """Return a no-op expert result for a selected module."""
        return ExpertResult(
            module_name=request.module_name,
            task=request.task,
            summary=f"No execution adapter is available for {request.module_name}.",
            details=(
                "The orchestrator preserved the route and context without calling tools.",
            ),
            confidence=0.0,
            metadata=adapter_metadata(self, request, "noop"),
        )


def adapter_supports_module(adapter: ExecutionAdapter, module_name: str) -> bool:
    """Return whether an adapter supports a module."""
    return module_name in set(adapter.supported_modules)


def adapter_metadata(
    adapter: ExecutionAdapter,
    request: ExecutionRequest,
    backend_kind: str,
) -> Metadata:
    """Create common metadata for adapter-produced expert results."""
    return {
        "execution_backend": "adapter",
        "backend_kind": backend_kind,
        "adapter_name": adapter.name,
        "adapter_description": adapter.description,
        "module_name": request.module_name,
        "context_count": len(request.context_items),
    }


def create_default_adapter_registry() -> ExecutionAdapterRegistry:
    """Create deterministic demo adapters for Grona's default modules."""
    return ExecutionAdapterRegistry(
        (
            StaticExecutionAdapter(
                name="default-static-adapter",
                description="Static deterministic adapter for default demo modules.",
                responses={
                    "code-assistant": (
                        "Adapter prepared a code inspection outline.",
                        (
                            "Review tests, linting, function boundaries, and error paths.",
                            "Keep code execution future-facing; no subprocess was called.",
                        ),
                    ),
                    "automotive-diagnostics": (
                        "Adapter prepared an automotive diagnostic outline.",
                        (
                            "Check coolant, thermostat behavior, radiator flow, "
                            "and fan activation.",
                            "Treat this as deterministic guidance, not a real diagnostic tool.",
                        ),
                    ),
                    "cybersecurity-scanner": (
                        "Adapter prepared a cybersecurity review outline.",
                        (
                            "Review secrets, authentication, permissions, ports, and logs.",
                            "No scanner, network access, or exploit tooling was called.",
                        ),
                    ),
                    "media-video-tool": (
                        "Adapter prepared a media workflow outline.",
                        (
                            "Inspect codec, compression, stabilization, color, and audio needs.",
                            "No media files or external processors were opened.",
                        ),
                    ),
                    "document-search": (
                        "Adapter prepared a document retrieval outline.",
                        (
                            "Define query terms, source boundaries, citations, and summary scope.",
                            "No document index, filesystem search, or database was queried.",
                        ),
                    ),
                    "general-reasoning": (
                        "Adapter prepared a general reasoning outline.",
                        (
                            "Clarify the goal, constraints, uncertainty, and next checks.",
                            "Keep the route trace visible before adding heavier execution.",
                        ),
                    ),
                },
            ),
        )
    )
