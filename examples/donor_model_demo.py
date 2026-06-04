"""Demonstrate deterministic donor model proposal collection."""

from grona import (
    DonorProposalCollector,
    StaticDonorModelAdapter,
    knowledge_seed_from_donor_proposal,
)


def main() -> None:
    """Run the offline donor proposal demo."""
    task = "Summarize modular AI routing"
    adapter = StaticDonorModelAdapter()
    collector = DonorProposalCollector((adapter,))
    batch = collector.collect(task, ("summary", "route_hint", "knowledge_seed"))

    print("Donor model demo")
    print("Execution: deterministic static donor only; no LM Studio, APIs, or training.")
    print()
    print(batch.to_text())

    knowledge_proposals = [
        proposal for proposal in batch.proposals if proposal.proposal_type == "knowledge_seed"
    ]
    if knowledge_proposals:
        seed = knowledge_seed_from_donor_proposal(knowledge_proposals[0])
        print()
        print("KnowledgeSeed candidate:")
        print(f"- {seed.id}")
        print(f"- source type: {seed.source.source_type}")
        print(f"- domains: {', '.join(seed.domains)}")
        print(f"- keywords: {', '.join(seed.keywords[:6])}")
        print("- still requires deterministic validation and review")


if __name__ == "__main__":
    main()
