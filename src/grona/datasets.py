"""Deterministic in-memory dataset ingestion primitives for Growth Lab."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .documents import assign_domains, extract_keywords
from .feedback import Metadata
from .growth import KnowledgeSeed, KnowledgeSource

DATASET_SOURCE_TYPES = (
    "instruction_dataset",
    "conversation_dataset",
    "web_corpus",
    "code_dataset",
    "log_dataset",
    "unknown",
)
DATASET_FORMATS = ("alpaca", "sharegpt", "jsonl", "parquet", "text", "unknown")
DATASET_SAMPLE_TYPES = (
    "instruction",
    "conversation",
    "factual_qa",
    "reasoning",
    "writing",
    "classification",
    "summarization",
    "code",
    "unknown",
)
ROLE_ALIASES = {
    "human": "user",
    "user": "user",
    "assistant": "assistant",
    "gpt": "assistant",
    "bot": "assistant",
    "system": "system",
}


@dataclass(frozen=True)
class DatasetSource:
    """Metadata about a structured dataset source before trust or promotion."""

    id: str
    name: str
    source_type: str
    format: str
    license: str
    language: str
    reliability: float = 0.5
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        name: str,
        source_type: str = "unknown",
        format: str = "unknown",
        license: str = "unknown",
        language: str = "unknown",
        reliability: float = 0.5,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "source_type", source_type)
        object.__setattr__(self, "format", format)
        object.__setattr__(self, "license", license)
        object.__setattr__(self, "language", language)
        object.__setattr__(self, "reliability", reliability)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("dataset source id cannot be empty")
        if not name:
            raise ValueError("dataset source name cannot be empty")
        if source_type not in DATASET_SOURCE_TYPES:
            raise ValueError(f"unsupported dataset source_type: {source_type}")
        if format not in DATASET_FORMATS:
            raise ValueError(f"unsupported dataset format: {format}")
        if not license:
            raise ValueError("dataset source license cannot be empty")
        if not language:
            raise ValueError("dataset source language cannot be empty")
        if not 0.0 <= reliability <= 1.0:
            raise ValueError("dataset source reliability must be between 0.0 and 1.0")


@dataclass(frozen=True)
class DatasetSample:
    """Normalized small dataset sample that can become a Growth Lab seed."""

    id: str
    source: DatasetSource
    content: str
    sample_type: str = "unknown"
    domains: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        source: DatasetSource,
        content: str,
        sample_type: str = "unknown",
        domains: Sequence[str] = (),
        keywords: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "content", " ".join(content.split()))
        object.__setattr__(self, "sample_type", sample_type)
        object.__setattr__(self, "domains", tuple(domains))
        object.__setattr__(self, "keywords", tuple(keywords))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("dataset sample id cannot be empty")
        if sample_type not in DATASET_SAMPLE_TYPES:
            raise ValueError(f"unsupported dataset sample_type: {sample_type}")


@dataclass(frozen=True)
class InstructionDatasetSample:
    """Alpaca-like instruction sample kept separate before normalization."""

    id: str
    source: DatasetSource
    instruction: str
    input: str = ""
    output: str = ""
    sample_type: str = "instruction"
    domains: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        source: DatasetSource,
        instruction: str,
        input: str = "",
        output: str = "",
        sample_type: str = "instruction",
        domains: Sequence[str] = (),
        keywords: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "instruction", " ".join(instruction.split()))
        object.__setattr__(self, "input", " ".join(input.split()))
        object.__setattr__(self, "output", " ".join(output.split()))
        object.__setattr__(self, "sample_type", sample_type)
        object.__setattr__(self, "domains", tuple(domains))
        object.__setattr__(self, "keywords", tuple(keywords))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("instruction dataset sample id cannot be empty")
        if sample_type not in DATASET_SAMPLE_TYPES:
            raise ValueError(f"unsupported dataset sample_type: {sample_type}")

    def to_dataset_sample(self) -> DatasetSample:
        """Convert this instruction sample into the generic dataset representation."""
        content_parts = [f"Instruction: {self.instruction}"]
        if self.input:
            content_parts.append(f"Input: {self.input}")
        content_parts.append(f"Output: {self.output}")
        content = "\n".join(content_parts)
        domains = self.domains or infer_domains(content)
        keywords = self.keywords or extract_keywords(content)
        return DatasetSample(
            self.id,
            self.source,
            content,
            sample_type=self.sample_type,
            domains=domains,
            keywords=keywords,
            metadata={
                "origin": "instruction_dataset_sample",
                "instruction": self.instruction,
                "has_input": bool(self.input),
                **self.metadata,
            },
        )


@dataclass(frozen=True)
class ConversationDatasetSample:
    """ShareGPT/LMSYS-like conversation sample with simple role strings."""

    id: str
    source: DatasetSource
    messages: tuple[dict[str, str], ...]
    sample_type: str = "conversation"
    domains: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        id: str,
        source: DatasetSource,
        messages: Sequence[Mapping[str, str]],
        sample_type: str = "conversation",
        domains: Sequence[str] = (),
        keywords: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        normalized_messages = tuple(normalize_message(message) for message in messages)
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "messages", normalized_messages)
        object.__setattr__(self, "sample_type", sample_type)
        object.__setattr__(self, "domains", tuple(domains))
        object.__setattr__(self, "keywords", tuple(keywords))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not id:
            raise ValueError("conversation dataset sample id cannot be empty")
        if sample_type not in DATASET_SAMPLE_TYPES:
            raise ValueError(f"unsupported dataset sample_type: {sample_type}")

    def to_dataset_sample(self) -> DatasetSample:
        """Convert this conversation sample into the generic dataset representation."""
        content = conversation_text(self.messages)
        domains = self.domains or infer_domains(content)
        keywords = self.keywords or extract_keywords(content)
        return DatasetSample(
            self.id,
            self.source,
            content,
            sample_type=self.sample_type,
            domains=domains,
            keywords=keywords,
            metadata={
                "origin": "conversation_dataset_sample",
                "message_count": len(self.messages),
                **self.metadata,
            },
        )


class AlpacaFormatAdapter:
    """Normalize in-memory Alpaca-like records into instruction samples."""

    def parse(
        self,
        records: Sequence[Mapping[str, object]],
        source: DatasetSource,
    ) -> tuple[InstructionDatasetSample, ...]:
        """Parse records with instruction/input/output fields and skip broken rows."""
        samples: list[InstructionDatasetSample] = []
        for index, record in enumerate(records, start=1):
            instruction = clean_text(record.get("instruction"))
            output = clean_text(record.get("output"))
            if not instruction or not output:
                continue
            input_text = clean_text(record.get("input"))
            content = " ".join(part for part in (instruction, input_text, output) if part)
            metadata = dict(source.metadata)
            record_metadata = record.get("metadata")
            if isinstance(record_metadata, Mapping):
                metadata.update(record_metadata)
            metadata.update({"dataset_format": source.format, "record_index": index})
            samples.append(
                InstructionDatasetSample(
                    id=f"{source.id}:instruction-{index:04d}",
                    source=source,
                    instruction=instruction,
                    input=input_text,
                    output=output,
                    sample_type=infer_sample_type(content, default="instruction"),
                    domains=infer_domains(content),
                    keywords=extract_keywords(content),
                    metadata=metadata,
                )
            )
        return tuple(samples)


class ShareGPTFormatAdapter:
    """Normalize in-memory ShareGPT/LMSYS-like records into conversation samples."""

    def parse(
        self,
        records: Sequence[Mapping[str, object]],
        source: DatasetSource,
    ) -> tuple[ConversationDatasetSample, ...]:
        """Parse supported conversation/message variants and skip broken rows."""
        samples: list[ConversationDatasetSample] = []
        for index, record in enumerate(records, start=1):
            messages = parse_conversation_messages(record)
            if not messages:
                continue
            content = conversation_text(messages)
            metadata = dict(source.metadata)
            record_metadata = record.get("metadata")
            if isinstance(record_metadata, Mapping):
                metadata.update(record_metadata)
            metadata.update({"dataset_format": source.format, "record_index": index})
            samples.append(
                ConversationDatasetSample(
                    id=f"{source.id}:conversation-{index:04d}",
                    source=source,
                    messages=messages,
                    sample_type=infer_sample_type(content, default="conversation"),
                    domains=infer_domains(content),
                    keywords=extract_keywords(content),
                    metadata=metadata,
                )
            )
        return tuple(samples)


def knowledge_seed_from_dataset_sample(sample: DatasetSample) -> KnowledgeSeed:
    """Convert one normalized dataset sample into a raw Growth Lab KnowledgeSeed."""
    source = KnowledgeSource(
        id=f"source:dataset:{sample.source.id}",
        source_type="document",
        name=sample.source.name,
        reliability=sample.source.reliability,
        metadata={
            "origin": "dataset_source",
            "dataset_source_id": sample.source.id,
            "dataset_source_type": sample.source.source_type,
            "dataset_format": sample.source.format,
            "dataset_license": sample.source.license,
            "dataset_language": sample.source.language,
            **sample.source.metadata,
        },
    )
    metadata = {
        "origin": "dataset_sample",
        "dataset_sample_id": sample.id,
        "dataset_source_id": sample.source.id,
        "dataset_source_type": sample.source.source_type,
        "dataset_format": sample.source.format,
        "dataset_license": sample.source.license,
        "dataset_language": sample.source.language,
        "sample_type": sample.sample_type,
        **sample.metadata,
    }
    return KnowledgeSeed(
        id=f"seed:dataset:{sample.id}",
        content=sample.content,
        source=source,
        domains=sample.domains,
        keywords=sample.keywords,
        confidence=sample.source.reliability,
        metadata=metadata,
    )


def knowledge_seeds_from_dataset_samples(
    samples: Sequence[DatasetSample],
) -> tuple[KnowledgeSeed, ...]:
    """Convert normalized dataset samples into deterministic Growth Lab seeds."""
    return tuple(knowledge_seed_from_dataset_sample(sample) for sample in samples)


def parse_conversation_messages(record: Mapping[str, object]) -> tuple[dict[str, str], ...]:
    """Return normalized messages from supported conversation record variants."""
    raw_messages = record.get("conversations") or record.get("messages")
    if not isinstance(raw_messages, Sequence) or isinstance(raw_messages, (str, bytes)):
        return ()
    messages: list[dict[str, str]] = []
    for raw_message in raw_messages:
        if not isinstance(raw_message, Mapping):
            continue
        message = normalize_message(raw_message)
        if message["content"]:
            messages.append(message)
    return tuple(messages)


def normalize_message(message: Mapping[str, str]) -> dict[str, str]:
    """Normalize one loose conversation message mapping."""
    raw_role = clean_text(message.get("role") or message.get("from") or "unknown")
    role = ROLE_ALIASES.get(raw_role.lower(), "unknown")
    content = clean_text(message.get("content") or message.get("value") or "")
    return {"role": role, "content": content}


def conversation_text(messages: Sequence[Mapping[str, str]]) -> str:
    """Format normalized messages into a deterministic text block."""
    return "\n".join(
        f"{message.get('role', 'unknown')}: {message.get('content', '')}"
        for message in messages
        if message.get("content")
    )


def infer_domains(content: str) -> tuple[str, ...]:
    """Infer Grona domains for dataset samples using existing keyword rules."""
    return assign_domains(content)


def infer_sample_type(content: str, default: str = "unknown") -> str:
    """Infer a small sample type from deterministic keyword cues."""
    lowered = content.lower()
    if any(term in lowered for term in ("python", "code", "function", "api", "test")):
        return "code"
    if any(term in lowered for term in ("summarize", "summary")):
        return "summarization"
    if any(term in lowered for term in ("classify", "label", "category")):
        return "classification"
    if any(term in lowered for term in ("why", "reason", "explain", "analyze")):
        return "reasoning"
    if "?" in content:
        return "factual_qa"
    return default if default in DATASET_SAMPLE_TYPES else "unknown"


def clean_text(value: object) -> str:
    """Return normalized text for loose in-memory dataset records."""
    if value is None:
        return ""
    return " ".join(str(value).split())


def create_demo_dataset_sources() -> dict[str, DatasetSource]:
    """Create tiny deterministic demo dataset sources without downloading data."""
    return {
        "alpaca": DatasetSource(
            "dataset:yahma-alpaca-cleaned-demo",
            "yahma/alpaca-cleaned demo",
            source_type="instruction_dataset",
            format="alpaca",
            license="cc-by-4.0",
            language="en",
            reliability=0.78,
            metadata={"demo_only": True, "upstream_style": "yahma/alpaca-cleaned"},
        ),
        "sharegpt": DatasetSource(
            "dataset:lmsys-chat-1m-demo",
            "lmsys-chat-1m style demo",
            source_type="conversation_dataset",
            format="sharegpt",
            license="research-only-demo",
            language="en",
            reliability=0.7,
            metadata={"demo_only": True, "upstream_style": "LMSYS / ShareGPT"},
        ),
        "ua_alpaca": DatasetSource(
            "dataset:ua-alpaca-demo",
            "UA-Alpaca style demo",
            source_type="instruction_dataset",
            format="alpaca",
            license="unknown-demo-license",
            language="uk",
            reliability=0.68,
            metadata={"demo_only": True, "upstream_style": "UA-Alpaca"},
        ),
    }


def create_demo_alpaca_samples() -> tuple[InstructionDatasetSample, ...]:
    """Create tiny Alpaca-like demo samples from in-memory dictionaries."""
    sources = create_demo_dataset_sources()
    records = (
        {
            "instruction": "Explain how to review a Python function for missing tests.",
            "input": "A small utility function changed without a test case.",
            "output": "Check expected behavior, edge cases, imports, and add focused tests.",
        },
        {
            "instruction": "Поясни, як діагностувати перегрів двигуна.",
            "input": "Авто швидко нагрівається у заторі.",
            "output": "Перевір рівень охолоджувача, вентилятор, термостат і радіатор.",
        },
    )
    english = AlpacaFormatAdapter().parse((records[0],), sources["alpaca"])
    ukrainian = AlpacaFormatAdapter().parse((records[1],), sources["ua_alpaca"])
    return english + ukrainian


def create_demo_sharegpt_samples() -> tuple[ConversationDatasetSample, ...]:
    """Create tiny ShareGPT-like demo samples from in-memory dictionaries."""
    source = create_demo_dataset_sources()["sharegpt"]
    records = (
        {
            "conversations": [
                {"from": "human", "value": "How should I inspect suspicious firewall logs?"},
                {
                    "from": "gpt",
                    "value": "Check source IPs, ports, authentication failures, and timing patterns.",
                },
            ],
            "metadata": {"conversation_style": "sharegpt"},
        },
        {
            "messages": [
                {"role": "user", "content": "Summarize document indexing precautions."},
                {
                    "role": "assistant",
                    "content": "Preserve source metadata, chunk boundaries, and citations first.",
                },
            ],
            "metadata": {"conversation_style": "messages"},
        },
    )
    return ShareGPTFormatAdapter().parse(records, source)
