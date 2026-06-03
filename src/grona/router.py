"""Lightweight keyword-based routing primitives for Grona."""

from __future__ import annotations

from dataclasses import dataclass, field
from re import findall
from typing import Callable, Iterable, Mapping

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


@dataclass(frozen=True)
class ModuleMatch:
    """A module score with human-readable routing reasons."""

    module: ExpertModule
    score: float
    reasons: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RoutingDecision:
    """The selected and skipped modules for a single task."""

    task: str
    selected_modules: tuple[ModuleMatch, ...]
    skipped_modules: tuple[ModuleMatch, ...]

    @property
    def selected_names(self) -> tuple[str, ...]:
        """Return selected module names in route order."""
        return tuple(match.module.name for match in self.selected_modules)


class ModuleRegistry:
    """A simple in-memory catalog of available expert modules."""

    def __init__(self, modules: Iterable[ExpertModule] = ()) -> None:
        self._modules: dict[str, ExpertModule] = {}
        for module in modules:
            self.register(module)

    def register(self, module: ExpertModule) -> None:
        """Add or replace a module by name."""
        self._modules[module.name] = module

    def remove(self, name: str) -> None:
        """Remove a module from the registry."""
        del self._modules[name]

    def all(self) -> tuple[ExpertModule, ...]:
        """Return all registered modules in insertion order."""
        return tuple(self._modules.values())


class Router:
    """Select relevant modules with transparent keyword/domain matching."""

    def __init__(self, registry: ModuleRegistry, top_k: int = 3, minimum_score: float = 1.0) -> None:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if minimum_score < 0:
            raise ValueError("minimum_score cannot be negative")
        self.registry = registry
        self.top_k = top_k
        self.minimum_score = minimum_score

    def route(self, task: str) -> RoutingDecision:
        """Score every module and return selected and skipped module matches."""
        task_terms = tokenize(task)
        matches = [self._score_module(module, task_terms) for module in self.registry.all()]
        matches.sort(key=lambda match: (match.score, -match.module.cost, match.module.name), reverse=True)

        selected = tuple(match for match in matches if match.score >= self.minimum_score)[: self.top_k]
        selected_names = {match.module.name for match in selected}
        skipped = tuple(match for match in matches if match.module.name not in selected_names)
        return RoutingDecision(task=task, selected_modules=selected, skipped_modules=skipped)

    def run(self, task: str, context: TaskContext | None = None) -> list[tuple[ModuleMatch, str]]:
        """Route a task and invoke only the selected modules."""
        decision = self.route(task)
        route_context = dict(context or {})
        route_context["selected_modules"] = ", ".join(decision.selected_names)
        return [(match, match.module.run(task, route_context)) for match in decision.selected_modules]

    def _score_module(self, module: ExpertModule, task_terms: set[str]) -> ModuleMatch:
        reasons: list[str] = []
        score = 0.0

        domain_terms = tokenize(module.domain)
        domain_hits = sorted(task_terms & domain_terms)
        if domain_hits:
            score += 2.0 * len(domain_hits)
            reasons.append("domain match: " + ", ".join(domain_hits))

        keyword_hits = sorted(task_terms & normalized_terms(module.keywords))
        if keyword_hits:
            score += 1.5 * len(keyword_hits)
            reasons.append("keyword match: " + ", ".join(keyword_hits))

        capability_hits = sorted(task_terms & normalized_terms(module.capabilities))
        if capability_hits:
            score += 1.0 * len(capability_hits)
            reasons.append("capability match: " + ", ".join(capability_hits))

        if not reasons:
            reasons.append("no keyword, domain, or capability match")

        return ModuleMatch(module=module, score=score, reasons=tuple(reasons))


def tokenize(text: str) -> set[str]:
    """Normalize text into lowercase alphanumeric terms."""
    return set(findall(r"[a-z0-9]+", text.lower()))


def normalized_terms(values: Iterable[str]) -> set[str]:
    """Normalize a collection of labels into comparable terms."""
    terms: set[str] = set()
    for value in values:
        terms.update(tokenize(value))
    return terms
