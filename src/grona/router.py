"""Lightweight sparse expert routing primitives."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Callable, Iterable, Sequence

Vector = Sequence[float]
ExpertHandler = Callable[[Vector], object]


@dataclass(frozen=True)
class Expert:
    """A small expert with a routing profile and callable behavior."""

    name: str
    profile: Vector
    handler: ExpertHandler
    description: str = ""

    def run(self, input_vector: Vector) -> object:
        """Execute the expert for an input vector."""
        return self.handler(input_vector)


@dataclass(frozen=True)
class RoutingDecision:
    """A scored expert selected by the router."""

    expert: Expert
    score: float


class SparseRouter:
    """Select the most relevant experts for an input vector."""

    def __init__(self, experts: Iterable[Expert], top_k: int = 2) -> None:
        self.experts = tuple(experts)
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        self.top_k = top_k

    def route(self, input_vector: Vector) -> list[RoutingDecision]:
        """Return the top matching experts for the provided input vector."""
        decisions = [
            RoutingDecision(expert=expert, score=cosine_similarity(input_vector, expert.profile))
            for expert in self.experts
        ]
        decisions.sort(key=lambda decision: decision.score, reverse=True)
        return decisions[: self.top_k]

    def run(self, input_vector: Vector) -> list[tuple[RoutingDecision, object]]:
        """Route an input vector and execute the activated experts."""
        return [(decision, decision.expert.run(input_vector)) for decision in self.route(input_vector)]


def cosine_similarity(left: Vector, right: Vector) -> float:
    """Compute cosine similarity for two equal-length vectors."""
    if len(left) != len(right):
        raise ValueError("vectors must have the same length")

    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_norm * right_norm)
