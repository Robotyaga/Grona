"""Routing decision data structures."""

from __future__ import annotations

from dataclasses import dataclass, field

from .module import ExpertModule


@dataclass(frozen=True)
class ModuleMatch:
    """A module score with human-readable routing reasons."""

    module: ExpertModule
    score: float
    reasons: tuple[str, ...] = field(default_factory=tuple)
    base_score: float | None = None
    adaptive_adjustment: float = 0.0
    adaptive_enabled: bool = False
    feedback_summary: str | None = None

    @property
    def final_score(self) -> float:
        """Return the score used for route ordering."""
        return self.score


@dataclass(frozen=True)
class RoutingDecision:
    """The selected and skipped modules for a single task."""

    task: str
    selected_modules: tuple[ModuleMatch, ...]
    skipped_modules: tuple[ModuleMatch, ...]
    adaptive_enabled: bool = False
    feedback_available: bool = False

    @property
    def selected_names(self) -> tuple[str, ...]:
        """Return selected module names in route order."""
        return tuple(match.module.name for match in self.selected_modules)

    @property
    def skipped_names(self) -> tuple[str, ...]:
        """Return skipped module names in route order."""
        return tuple(match.module.name for match in self.skipped_modules)
