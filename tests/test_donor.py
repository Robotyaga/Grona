from grona import (
    DonorModelError,
    DonorModelProposal,
    DonorProposalCollector,
    LMStudioAdapter,
    StaticDonorModelAdapter,
    knowledge_seed_from_donor_proposal,
)
from grona.entrypoint import main


class BrokenDonorAdapter:
    name = "broken-donor"

    def propose(self, task: str, proposal_type: str = "summary") -> DonorModelProposal:
        raise DonorModelError(f"cannot propose {proposal_type} for {task}")


def test_donor_model_proposal_creation() -> None:
    proposal = DonorModelProposal(
        task="Summarize routing",
        source="test-donor",
        proposal_type="summary",
        content="A concise untrusted summary proposal.",
        confidence=0.6,
        metadata={"network_used": False},
    )

    assert proposal.task == "Summarize routing"
    assert proposal.source == "test-donor"
    assert proposal.proposal_type == "summary"
    assert proposal.confidence == 0.6
    assert "summary" in proposal.to_text().lower()


def test_static_donor_model_adapter_is_deterministic() -> None:
    adapter = StaticDonorModelAdapter()

    first = adapter.propose("Review modular routing", "route_hint")
    second = adapter.propose("Review modular routing", "route_hint")

    assert first == second
    assert first.source == "static-donor"
    assert first.metadata["network_used"] is False
    assert "Route hint" in first.content


def test_donor_proposal_collector_success_path() -> None:
    collector = DonorProposalCollector((StaticDonorModelAdapter(),))

    batch = collector.collect("Summarize modular AI routing", ("summary", "knowledge_seed"))

    assert len(batch.proposals) == 2
    assert not batch.errors
    assert batch.metadata["adapter_count"] == 1
    assert {proposal.proposal_type for proposal in batch.proposals} == {
        "summary",
        "knowledge_seed",
    }


def test_donor_proposal_collector_records_errors() -> None:
    collector = DonorProposalCollector((BrokenDonorAdapter(),))

    batch = collector.collect("Summarize modular AI routing", ("summary",))

    assert not batch.proposals
    assert len(batch.errors) == 1
    assert batch.errors[0].adapter == "broken-donor"
    assert "cannot propose" in batch.errors[0].message


def test_knowledge_seed_from_donor_proposal_keeps_provenance() -> None:
    proposal = StaticDonorModelAdapter().propose(
        "Summarize modular AI routing",
        "knowledge_seed",
    )

    seed = knowledge_seed_from_donor_proposal(proposal)

    assert seed.source.source_type == "donor_model"
    assert seed.source.reliability == 0.45
    assert seed.metadata["origin"] == "donor_model_proposal"
    assert seed.metadata["network_used"] is False
    assert seed.status == "new"


def test_lmstudio_adapter_construction_only() -> None:
    adapter = LMStudioAdapter(
        base_url="http://127.0.0.1:1234",
        model="local-model",
        timeout=1.5,
    )

    assert adapter.base_url == "http://127.0.0.1:1234"
    assert adapter.model == "local-model"
    assert adapter.timeout == 1.5
    assert adapter.name == "lmstudio-local"


def test_cli_donor_demo_behavior(capsys) -> None:
    assert main(["Summarize", "modular", "AI", "routing", "--donor-demo"]) == 0

    output = capsys.readouterr().out
    assert "Donor model demo: StaticDonorModelAdapter" in output
    assert "Execution: deterministic offline proposals only" in output
    assert "KnowledgeSeed candidate preview" in output
    assert "validation/review still required" in output
