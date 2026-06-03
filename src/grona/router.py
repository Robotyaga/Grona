"""Lightweight keyword-based routing for Grona."""

from __future__ import annotations

from collections.abc import Iterable
from re import findall

from .decision import ModuleMatch, RoutingDecision
from .module import ExpertModule, TaskContext
from .registry import ModuleRegistry


class Router:
    """Select relevant modules with transparent keyword/domain matching."""

    def __init__(
        self,
        registry: ModuleRegistry,
        top_k: int = 3,
        minimum_score: float = 1.0,
    ) -> None:
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
        matches = [self._score_module(module, task_terms) for module in self.registry]
        matches.sort(key=lambda match: (-match.score, match.module.cost, match.module.name))

        selected = tuple(
            match for match in matches if match.score >= self.minimum_score
        )[: self.top_k]
        selected_names = {match.module.name for match in selected}
        skipped = tuple(match for match in matches if match.module.name not in selected_names)
        return RoutingDecision(task=task, selected_modules=selected, skipped_modules=skipped)

    def run(self, task: str, context: TaskContext | None = None) -> list[tuple[ModuleMatch, str]]:
        """Route a task and invoke only the selected modules."""
        decision = self.route(task)
        route_context = dict(context or {})
        route_context["selected_modules"] = ", ".join(decision.selected_names)
        return [
            (match, match.module.run(task, route_context))
            for match in decision.selected_modules
        ]

    def _score_module(self, module: ExpertModule, task_terms: set[str]) -> ModuleMatch:
        reasons: list[str] = []
        score = 0.0

        domain_hits = sorted(task_terms & tokenize(module.domain))
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
