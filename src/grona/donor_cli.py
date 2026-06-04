"""CLI demo for deterministic donor model proposals."""

from __future__ import annotations

from collections.abc import Sequence

from .donor import (
    DonorProposalCollector,
    StaticDonorModelAdapter,
    knowledge_seed_from_donor_proposal,
)

DEFAULT_DONOR_TASK = "Summarize modular AI routing"
DEMO_PROPOSAL_TYPES = ("summary", "route_hint", "knowledge_seed")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the deterministic donor proposal demo."""
    args = tuple(argv or ())
    task = donor_task_from_args(args)
    print(format_donor_demo(task))
    return 0


def donor_task_from_args(args: Sequence[str]) -> str:
    """Extract task text while ignoring the donor demo flag."""
    task_parts = [item for item in args if item != "--donor-demo"]
    return " ".join(task_parts).strip() or DEFAULT_DONOR_TASK


def format_donor_demo(task: str) -> str:
    """Format deterministic donor proposals and a seed conversion preview."""
    collector = DonorProposalCollector((StaticDonorModelAdapter(),))
    batch = collector.collect(task, DEMO_PROPOSAL_TYPES)
    seed = next(
        (
            knowledge_seed_from_donor_proposal(proposal)
            for proposal in batch.proposals
            if proposal.proposal_type == "knowledge_seed"
        ),
        None,
    )
    lines = [
        "Donor model demo: StaticDonorModelAdapter",
        "Execution: deterministic offline proposals only; no LM Studio, APIs, or training.",
        "",
        batch.to_text(),
    ]
    if seed is not None:
        lines.extend(
            [
                "",
                "KnowledgeSeed candidate preview:",
                f"- id: {seed.id}",
                f"- source_type: {seed.source.source_type}",
                f"- domains: {', '.join(seed.domains)}",
                f"- keywords: {', '.join(seed.keywords[:6])}",
                "- status: untrusted raw seed; validation/review still required",
            ]
        )
    return "\n".join(lines)
