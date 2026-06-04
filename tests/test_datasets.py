from grona import (
    AlpacaFormatAdapter,
    ConversationDatasetSample,
    DatasetSample,
    DatasetSource,
    InstructionDatasetSample,
    KnowledgeSeed,
    ShareGPTFormatAdapter,
    create_demo_alpaca_samples,
    create_demo_dataset_sources,
    create_demo_sharegpt_samples,
    knowledge_seed_from_dataset_sample,
    knowledge_seeds_from_dataset_samples,
)
from grona.cli import main


def make_source() -> DatasetSource:
    return DatasetSource(
        "dataset:test-alpaca",
        "Test Alpaca",
        source_type="instruction_dataset",
        format="alpaca",
        license="cc-by-4.0",
        language="en",
        reliability=0.82,
        metadata={"demo_only": True},
    )


def test_dataset_source_creation() -> None:
    source = make_source()

    assert source.id == "dataset:test-alpaca"
    assert source.source_type == "instruction_dataset"
    assert source.format == "alpaca"
    assert source.license == "cc-by-4.0"
    assert source.reliability == 0.82


def test_dataset_sample_creation() -> None:
    source = make_source()
    sample = DatasetSample(
        "sample:test",
        source,
        "Explain a deterministic dataset normalization layer.",
        sample_type="instruction",
        domains=("general",),
        keywords=("dataset", "normalization"),
    )

    assert sample.source == source
    assert sample.sample_type == "instruction"
    assert sample.domains == ("general",)
    assert sample.keywords == ("dataset", "normalization")


def test_instruction_dataset_sample_conversion() -> None:
    source = make_source()
    sample = InstructionDatasetSample(
        "sample:instruction",
        source,
        "Explain how to test a Python function.",
        input="A function changed without tests.",
        output="Add focused unit tests for expected behavior and edge cases.",
    )

    generic = sample.to_dataset_sample()

    assert generic.sample_type == "instruction"
    assert "Instruction:" in generic.content
    assert "Input:" in generic.content
    assert "Output:" in generic.content
    assert generic.metadata["origin"] == "instruction_dataset_sample"


def test_conversation_dataset_sample_conversion() -> None:
    source = DatasetSource(
        "dataset:test-chat",
        "Test Chat",
        source_type="conversation_dataset",
        format="sharegpt",
        license="research-only-demo",
        language="en",
    )
    sample = ConversationDatasetSample(
        "sample:conversation",
        source,
        messages=(
            {"from": "human", "value": "How should I inspect logs?"},
            {"from": "gpt", "value": "Check ports, authentication, and timestamps."},
        ),
    )

    generic = sample.to_dataset_sample()

    assert sample.messages[0]["role"] == "user"
    assert sample.messages[1]["role"] == "assistant"
    assert generic.sample_type == "conversation"
    assert "user: How should I inspect logs?" in generic.content
    assert generic.metadata["message_count"] == 2


def test_alpaca_format_adapter_parses_valid_samples() -> None:
    source = make_source()
    records = (
        {
            "instruction": "Explain how to review Python imports.",
            "input": "A small package has new imports.",
            "output": "Check unused imports, public API imports, and lint output.",
        },
    )

    samples = AlpacaFormatAdapter().parse(records, source)

    assert len(samples) == 1
    assert samples[0].instruction == "Explain how to review Python imports."
    assert samples[0].source == source
    assert "python" in samples[0].keywords


def test_alpaca_format_adapter_skips_broken_samples() -> None:
    source = make_source()
    records = (
        {"instruction": "Missing output should be skipped."},
        {"output": "Missing instruction should be skipped."},
        {"instruction": "Valid row", "output": "Valid enough output for conversion."},
    )

    samples = AlpacaFormatAdapter().parse(records, source)

    assert len(samples) == 1
    assert samples[0].id == "dataset:test-alpaca:instruction-0003"


def test_sharegpt_format_adapter_parses_conversations_format() -> None:
    source = DatasetSource(
        "dataset:test-sharegpt",
        "Test ShareGPT",
        source_type="conversation_dataset",
        format="sharegpt",
        license="research-only-demo",
        language="en",
    )
    records = (
        {
            "conversations": [
                {"from": "human", "value": "How do I inspect firewall logs?"},
                {"from": "gpt", "value": "Review ports, source IPs, and auth failures."},
            ]
        },
    )

    samples = ShareGPTFormatAdapter().parse(records, source)

    assert len(samples) == 1
    assert samples[0].messages[0]["role"] == "user"
    assert samples[0].messages[1]["role"] == "assistant"


def test_sharegpt_format_adapter_parses_messages_format() -> None:
    source = DatasetSource(
        "dataset:test-messages",
        "Test Messages",
        source_type="conversation_dataset",
        format="sharegpt",
        license="research-only-demo",
        language="en",
    )
    records = (
        {
            "messages": [
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": "Summarize document indexing."},
            ]
        },
    )

    samples = ShareGPTFormatAdapter().parse(records, source)

    assert len(samples) == 1
    assert samples[0].messages[0]["role"] == "system"
    assert samples[0].messages[1]["content"] == "Summarize document indexing."


def test_knowledge_seed_from_dataset_sample_preserves_license_metadata() -> None:
    source = make_source()
    sample = DatasetSample(
        "sample:seed",
        source,
        "Explain Python package tests, linting, imports, and API boundaries.",
        sample_type="code",
        domains=("code",),
        keywords=("python", "tests", "lint"),
    )

    seed = knowledge_seed_from_dataset_sample(sample)

    assert isinstance(seed, KnowledgeSeed)
    assert seed.source.name == source.name
    assert seed.source.metadata["dataset_license"] == "cc-by-4.0"
    assert seed.metadata["dataset_format"] == "alpaca"
    assert seed.metadata["dataset_license"] == "cc-by-4.0"
    assert seed.metadata["sample_type"] == "code"


def test_knowledge_seeds_from_dataset_samples_are_deterministic() -> None:
    samples = tuple(sample.to_dataset_sample() for sample in create_demo_alpaca_samples())
    samples += tuple(sample.to_dataset_sample() for sample in create_demo_sharegpt_samples())

    first = knowledge_seeds_from_dataset_samples(samples)
    second = knowledge_seeds_from_dataset_samples(samples)

    assert first == second
    assert len(first) == 4
    assert {seed.metadata["dataset_language"] for seed in first} == {"en", "uk"}


def test_create_demo_dataset_sources() -> None:
    sources = create_demo_dataset_sources()

    assert sources["alpaca"].license == "cc-by-4.0"
    assert sources["sharegpt"].source_type == "conversation_dataset"
    assert sources["ua_alpaca"].language == "uk"


def test_cli_dataset_demo_behavior(capsys) -> None:
    assert main(["--dataset-demo"]) == 0

    output = capsys.readouterr().out
    assert "Growth Lab demo: Dataset ingestion foundation" in output
    assert "Dataset samples:" in output
    assert "Instruction samples:" in output
    assert "Conversation samples:" in output
    assert "Generated KnowledgeSeeds:" in output
    assert "Validation statuses:" in output
