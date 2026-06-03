"""Expert module primitives for Grona."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

TaskContext = Mapping[str, str]
ModuleHandler = Callable[[str, TaskContext], str]


@dataclass(frozen=True)
class ExpertModule:
    """A specialized module that can be selected for a task."""

    name: str
    domain: str
    capabilities: tuple[str, ...]
    keywords: tuple[str, ...]
    handler: ModuleHandler
    description: str = ""
    cost: int = 1

    def run(self, task: str, context: TaskContext | None = None) -> str:
        """Invoke the module with the task and optional route context."""
        return self.handler(task, context or {})
