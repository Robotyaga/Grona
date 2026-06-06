"""Prompt templates, prompt rendering, and inference trace records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from string import Formatter
from typing import Protocol

from .context import ContextItem
from .decision import RoutingDecision
from .local_llm import LocalLLMAdapter, LocalLLMRequest, LocalLLMResponse, StaticLocalLLMAdapter

Metadata = dict[str, object]
JsonValue = object

PROMPT_TEMPLATE_FIELDS = frozenset(
    (
        "context_block",
        "context_sources",
        "routing_summary",
        "selected_modules",
        "task",
        "workspace",
    )
)
DEFAULT_TRACE_CREATED_AT = "2026-01-01T00:00:00+00:00"


@dataclass(frozen=True)
class PromptTemplate:
    """Deterministic prompt template with explicit allowed format fields."""

    name: str
    description: str
    system_template: str
    user_template: str
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        description: str,
        system_template: str,
        user_template: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "name", " ".join(name.split()))
        object.__setattr__(self, "description", " ".join(description.split()))
        object.__setattr__(self, "system_template", system_template.strip())
        object.__setattr__(self, "user_template", user_template.strip())
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not self.name:
            raise ValueError("prompt template name cannot be empty")
        if not self.description:
            raise ValueError("prompt template description cannot be empty")
        if not self.system_template:
            raise ValueError("prompt template system_template cannot be empty")
        if not self.user_template:
            raise ValueError("prompt template user_template cannot be empty")
        unsupported = sorted(self.required_fields() - PROMPT_TEMPLATE_FIELDS)
        if unsupported:
            raise ValueError(f"prompt template contains unsupported fields: {', '.join(unsupported)}")

    def required_fields(self) -> frozenset[str]:
        """Return format fields used by this template."""
        fields: set[str] = set()
        for template_text in (self.system_template, self.user_template):
            for _literal, field_name, _format_spec, _conversion in Formatter().parse(template_text):
                if field_name:
                    fields.add(field_name.split(".")[0].split("[")[0])
        return frozenset(fields)

    def render(self, values: Mapping[str, object]) -> RenderedPrompt:
        """Render the template with explicit values and clear missing-field errors."""
        missing = sorted(field for field in self.required_fields() if field not in values)
        if missing:
            raise ValueError(f"prompt template missing fields: {', '.join(missing)}")
        safe_values = {field: str(values.get(field, "")) for field in PROMPT_TEMPLATE_FIELDS}
        try:
            system_prompt = self.system_template.format(**safe_values).strip()
            user_prompt = self.user_template.format(**safe_values).strip()
        except KeyError as exc:
            raise ValueError(f"prompt template missing field: {exc.args[0]}") from exc
        return RenderedPrompt(
            template_name=self.name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            metadata={
                "description": self.description,
                "template_metadata": json_compatible(self.metadata),
                "used_fields": sorted(self.required_fields()),
            },
        )

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize template metadata without rendering it."""
        return {
            "description": self.description,
            "metadata": json_compatible(self.metadata),
            "name": self.name,
            "system_template": self.system_template,
            "user_template": self.user_template,
        }


@dataclass(frozen=True)
class RenderedPrompt:
    """Rendered prompt ready for an explicit adapter call."""

    template_name: str
    system_prompt: str
    user_prompt: str
    full_prompt: str
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        template_name: str,
        system_prompt: str,
        user_prompt: str,
        full_prompt: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        normalized_template = " ".join(template_name.split())
        system_text = system_prompt.strip()
        user_text = user_prompt.strip()
        prompt_text = full_prompt.strip() if full_prompt else combine_prompt_text(system_text, user_text)
        object.__setattr__(self, "template_name", normalized_template)
        object.__setattr__(self, "system_prompt", system_text)
        object.__setattr__(self, "user_prompt", user_text)
        object.__setattr__(self, "full_prompt", prompt_text)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not self.template_name:
            raise ValueError("rendered prompt template_name cannot be empty")
        if not self.system_prompt:
            raise ValueError("rendered prompt system_prompt cannot be empty")
        if not self.user_prompt:
            raise ValueError("rendered prompt user_prompt cannot be empty")
        if not self.full_prompt:
            raise ValueError("rendered prompt full_prompt cannot be empty")

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize rendered prompt to JSON-compatible data."""
        return {
            "full_prompt": self.full_prompt,
            "metadata": json_compatible(self.metadata),
            "system_prompt": self.system_prompt,
            "template_name": self.template_name,
            "user_prompt": self.user_prompt,
        }

    def to_json(self) -> str:
        """Serialize rendered prompt as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> RenderedPrompt:
        """Rebuild a rendered prompt from JSON-compatible data."""
        return cls(
            template_name=str(data.get("template_name", "")),
            system_prompt=str(data.get("system_prompt", "")),
            user_prompt=str(data.get("user_prompt", "")),
            full_prompt=str(data.get("full_prompt", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )

    def to_text(self) -> str:
        """Format rendered prompt for demos."""
        return "\n".join(
            (
                f"Template: {self.template_name}",
                "System prompt:",
                self.system_prompt,
                "",
                "User prompt:",
                self.user_prompt,
            )
        )


class PromptBuilder:
    """Render model-facing prompts from tasks, route traces, and context items."""

    def __init__(self, template: PromptTemplate) -> None:
        self.template = template

    def build(
        self,
        task: str,
        routing_decision: RoutingDecision | None = None,
        context_items: Sequence[ContextItem] = (),
        workspace_metadata: Mapping[str, object] | None = None,
        extra_fields: Mapping[str, object] | None = None,
    ) -> RenderedPrompt:
        """Build one deterministic rendered prompt without calling a model."""
        task_text = " ".join(task.split())
        if not task_text:
            raise ValueError("prompt builder task cannot be empty")
        values: dict[str, object] = {
            "context_block": format_context_block(context_items),
            "context_sources": format_context_sources(context_items),
            "routing_summary": format_routing_summary(routing_decision),
            "selected_modules": format_selected_modules(routing_decision),
            "task": task_text,
            "workspace": format_workspace_metadata(workspace_metadata or {}),
        }
        values.update(extra_fields or {})
        rendered = self.template.render(values)
        metadata = {
            **rendered.metadata,
            "context_count": len(tuple(context_items)),
            "context_sources": tuple(item.source for item in context_items),
            "selected_modules": tuple(routing_decision.selected_names) if routing_decision else (),
            "workspace": json_compatible(dict(workspace_metadata or {})),
        }
        return RenderedPrompt(
            template_name=rendered.template_name,
            system_prompt=rendered.system_prompt,
            user_prompt=rendered.user_prompt,
            metadata=metadata,
        )


@dataclass(frozen=True)
class InferenceTrace:
    """One explicit prompt, adapter response, and provenance trace."""

    trace_id: str
    created_at: str
    task: str
    prompt: RenderedPrompt
    adapter_name: str
    model: str
    response_text: str
    error: str | None = None
    routing_summary: str = ""
    selected_modules: tuple[str, ...] = ()
    context_sources: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        trace_id: str,
        created_at: str,
        task: str,
        prompt: RenderedPrompt,
        adapter_name: str,
        model: str,
        response_text: str,
        error: str | None = None,
        routing_summary: str = "",
        selected_modules: Sequence[str] = (),
        context_sources: Sequence[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "trace_id", " ".join(trace_id.split()))
        object.__setattr__(self, "created_at", " ".join(created_at.split()))
        object.__setattr__(self, "task", " ".join(task.split()))
        object.__setattr__(self, "prompt", prompt)
        object.__setattr__(self, "adapter_name", " ".join(adapter_name.split()))
        object.__setattr__(self, "model", " ".join(model.split()))
        object.__setattr__(self, "response_text", response_text.strip())
        object.__setattr__(self, "error", error)
        object.__setattr__(self, "routing_summary", routing_summary.strip())
        object.__setattr__(self, "selected_modules", tuple(selected_modules))
        object.__setattr__(self, "context_sources", tuple(context_sources))
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not self.trace_id:
            raise ValueError("inference trace trace_id cannot be empty")
        if not self.created_at:
            raise ValueError("inference trace created_at cannot be empty")
        if not self.task:
            raise ValueError("inference trace task cannot be empty")
        if not self.adapter_name:
            raise ValueError("inference trace adapter_name cannot be empty")
        if not self.model:
            raise ValueError("inference trace model cannot be empty")

    @property
    def ok(self) -> bool:
        """Return whether the trace response completed without error text."""
        return self.error is None and bool(self.response_text)

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize trace to JSON-compatible data."""
        return {
            "adapter_name": self.adapter_name,
            "context_sources": list(self.context_sources),
            "created_at": self.created_at,
            "error": self.error,
            "metadata": json_compatible(self.metadata),
            "model": self.model,
            "ok": self.ok,
            "prompt": self.prompt.to_dict(),
            "response_text": self.response_text,
            "routing_summary": self.routing_summary,
            "selected_modules": list(self.selected_modules),
            "task": self.task,
            "trace_id": self.trace_id,
        }

    def to_json(self) -> str:
        """Serialize trace as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> InferenceTrace:
        """Rebuild an inference trace from JSON-compatible data."""
        prompt_data = data.get("prompt")
        if not isinstance(prompt_data, Mapping):
            raise ValueError("inference trace prompt must be an object")
        return cls(
            trace_id=str(data.get("trace_id", "")),
            created_at=str(data.get("created_at", "")),
            task=str(data.get("task", "")),
            prompt=RenderedPrompt.from_dict(prompt_data),
            adapter_name=str(data.get("adapter_name", "")),
            model=str(data.get("model", "")),
            response_text=str(data.get("response_text", "")),
            error=optional_string(data.get("error")),
            routing_summary=str(data.get("routing_summary", "")),
            selected_modules=tuple(str(item) for item in data.get("selected_modules", ()) or ()),
            context_sources=tuple(str(item) for item in data.get("context_sources", ()) or ()),
            metadata=dict(data.get("metadata", {}) or {}),
        )

    @classmethod
    def from_json(cls, text: str) -> InferenceTrace:
        """Rebuild an inference trace from stable JSON text."""
        data = loads(text)
        if not isinstance(data, Mapping):
            raise ValueError("inference trace JSON root must be an object")
        return cls.from_dict(data)

    def to_text(self) -> str:
        """Format compact trace summary for demos."""
        modules = ", ".join(self.selected_modules) if self.selected_modules else "none"
        sources = ", ".join(self.context_sources) if self.context_sources else "none"
        lines = [
            f"Trace: {self.trace_id}",
            f"Created at: {self.created_at}",
            f"Adapter: {self.adapter_name}",
            f"Model: {self.model}",
            f"OK: {self.ok}",
            f"Selected modules: {modules}",
            f"Context sources: {sources}",
        ]
        if self.error:
            lines.append(f"Error: {self.error}")
        if self.response_text:
            lines.append(f"Response: {self.response_text}")
        return "\n".join(lines)


class InferenceTraceStore(Protocol):
    """Minimal storage protocol for explicit inference traces."""

    def add(self, trace: InferenceTrace) -> None:
        """Store one inference trace."""
        ...

    def list(self) -> tuple[InferenceTrace, ...]:
        """Return stored traces in deterministic order."""
        ...

    def count(self) -> int:
        """Return number of stored traces."""
        ...

    def get(self, trace_id: str) -> InferenceTrace | None:
        """Return one trace by id when present."""
        ...

    def clear(self) -> None:
        """Remove stored traces."""
        ...


class InMemoryInferenceTraceStore:
    """In-memory trace store for tests, demos, and explicit callers."""

    def __init__(self, traces: Sequence[InferenceTrace] = ()) -> None:
        self._traces = list(traces)

    def add(self, trace: InferenceTrace) -> None:
        """Store one trace in insertion order."""
        self._traces.append(trace)

    def list(self) -> tuple[InferenceTrace, ...]:
        """Return stored traces in insertion order."""
        return tuple(self._traces)

    def count(self) -> int:
        """Return number of stored traces."""
        return len(self._traces)

    def get(self, trace_id: str) -> InferenceTrace | None:
        """Return the first trace with a matching id."""
        for trace in self._traces:
            if trace.trace_id == trace_id:
                return trace
        return None

    def clear(self) -> None:
        """Remove all traces."""
        self._traces.clear()


class JsonlInferenceTraceStore:
    """Explicit JSONL file store for inference traces; no database is used."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def add(self, trace: InferenceTrace) -> None:
        """Append one trace as one JSON object per line."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(trace.to_json())
            file.write("\n")

    def list(self) -> tuple[InferenceTrace, ...]:
        """Read all traces from the JSONL file."""
        if not self.path.exists():
            return ()
        traces: list[InferenceTrace] = []
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                text = line.strip()
                if text:
                    traces.append(InferenceTrace.from_json(text))
        return tuple(traces)

    def count(self) -> int:
        """Return number of stored traces."""
        return len(self.list())

    def get(self, trace_id: str) -> InferenceTrace | None:
        """Return one trace by id when present."""
        for trace in self.list():
            if trace.trace_id == trace_id:
                return trace
        return None

    def clear(self) -> None:
        """Clear the JSONL file while keeping the path explicit."""
        if self.path.exists():
            self.path.write_text("", encoding="utf-8")


def default_prompt_templates() -> dict[str, PromptTemplate]:
    """Return deterministic built-in prompt templates."""
    return {
        "general_task": PromptTemplate(
            name="general_task",
            description="General task prompt with routing and context provenance.",
            system_template=(
                "You are responding inside Grona's deterministic prompt trace prototype. "
                "Use only the provided task, routing trace, and context. Do not claim hidden tools."
            ),
            user_template=(
                "Task:\n{task}\n\nRouting trace:\n{routing_summary}\n\n"
                "Selected modules:\n{selected_modules}\n\nContext:\n{context_block}"
            ),
            metadata={"intended_use": "general prompt trace demo"},
        ),
        "routing_trace_summary": PromptTemplate(
            name="routing_trace_summary",
            description="Summarize the visible sparse route and context sources.",
            system_template="Summarize only the visible Grona route trace. Do not infer hidden state.",
            user_template=(
                "Task: {task}\nWorkspace: {workspace}\nSelected modules: {selected_modules}\n"
                "Routing summary: {routing_summary}\nContext sources: {context_sources}"
            ),
            metadata={"intended_use": "route trace inspection"},
        ),
        "grona_vs_monolith_baseline": PromptTemplate(
            name="grona_vs_monolith_baseline",
            description="Prepare a controlled direct baseline prompt for comparison experiments.",
            system_template=(
                "You are a direct local baseline. Answer from the whole prompt without claiming "
                "Grona sparse routing, external tools, or hidden retrieval."
            ),
            user_template="Task:\n{task}\n\nAvailable context:\n{context_block}",
            metadata={"intended_use": "baseline comparison"},
        ),
        "knowledge_seed_proposal": PromptTemplate(
            name="knowledge_seed_proposal",
            description="Prepare context for a future reviewed knowledge seed proposal.",
            system_template=(
                "Propose candidate knowledge only as untrusted review material. "
                "Preserve provenance and avoid certainty claims."
            ),
            user_template=(
                "Task:\n{task}\n\nRoute:\n{routing_summary}\n\n"
                "Context sources:\n{context_sources}\n\nContext:\n{context_block}"
            ),
            metadata={"intended_use": "untrusted knowledge seed proposal"},
        ),
        "training_example_review": PromptTemplate(
            name="training_example_review",
            description="Prepare a trace for future reviewed training-example decisions.",
            system_template=(
                "Review the prompt/response candidate conservatively. This is not automatic training."
            ),
            user_template=(
                "Task:\n{task}\n\nSelected modules:\n{selected_modules}\n\n"
                "Context:\n{context_block}\n\nWorkspace:\n{workspace}"
            ),
            metadata={"intended_use": "training candidate review"},
        ),
    }


def get_default_prompt_template(name: str = "general_task") -> PromptTemplate:
    """Return one built-in prompt template by name."""
    templates = default_prompt_templates()
    if name not in templates:
        valid = ", ".join(sorted(templates))
        raise ValueError(f"unknown prompt template: {name}; expected one of {valid}")
    return templates[name]


@dataclass(frozen=True)
class PromptTraceResult:
    """Result of a prompt-builder adapter call with an attached trace."""

    prompt: RenderedPrompt
    response: LocalLLMResponse
    trace: InferenceTrace

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize prompt trace result to JSON-compatible data."""
        return {
            "prompt": self.prompt.to_dict(),
            "response": self.response.to_dict(),
            "trace": self.trace.to_dict(),
        }


def run_prompt_trace(
    task: str,
    adapter: LocalLLMAdapter,
    template: PromptTemplate | None = None,
    routing_decision: RoutingDecision | None = None,
    context_items: Sequence[ContextItem] = (),
    workspace_metadata: Mapping[str, object] | None = None,
    model: str = "local-baseline",
    trace_id: str | None = None,
    created_at: str = DEFAULT_TRACE_CREATED_AT,
    metadata: Mapping[str, object] | None = None,
) -> PromptTraceResult:
    """Build a prompt, call an explicit adapter, and return an inference trace."""
    prompt_template = template or get_default_prompt_template("general_task")
    prompt = PromptBuilder(prompt_template).build(
        task,
        routing_decision=routing_decision,
        context_items=context_items,
        workspace_metadata=workspace_metadata,
    )
    request = LocalLLMRequest(
        prompt=prompt.user_prompt,
        system_prompt=prompt.system_prompt,
        model=model,
        metadata={"prompt_template": prompt.template_name},
    )
    response = adapter.complete(request)
    selected_modules = tuple(routing_decision.selected_names) if routing_decision else ()
    context_sources = tuple(item.source for item in context_items)
    routing_summary = format_routing_summary(routing_decision)
    trace = InferenceTrace(
        trace_id=trace_id
        or stable_trace_id(task, prompt.template_name, adapter.name, response.text, response.error),
        created_at=created_at,
        task=task,
        prompt=prompt,
        adapter_name=adapter.name,
        model=response.model,
        response_text=response.text,
        error=response.error,
        routing_summary=routing_summary,
        selected_modules=selected_modules,
        context_sources=context_sources,
        metadata={
            "adapter_response": response.to_dict(),
            "network_used": bool(response.metadata.get("network_used", False)),
            **dict(metadata or {}),
        },
    )
    return PromptTraceResult(prompt=prompt, response=response, trace=trace)


def run_static_prompt_trace(
    task: str,
    template: PromptTemplate | None = None,
    routing_decision: RoutingDecision | None = None,
    context_items: Sequence[ContextItem] = (),
    workspace_metadata: Mapping[str, object] | None = None,
) -> PromptTraceResult:
    """Run the deterministic static local LLM adapter through the prompt builder."""
    return run_prompt_trace(
        task,
        StaticLocalLLMAdapter(mode="weak_monolith"),
        template=template,
        routing_decision=routing_decision,
        context_items=context_items,
        workspace_metadata=workspace_metadata,
        metadata={"demo": "static prompt trace", "network_used": False},
    )


def stable_trace_id(
    task: str,
    template_name: str,
    adapter_name: str,
    response_text: str,
    error: str | None = None,
) -> str:
    """Create a deterministic short trace id for tests and demos."""
    material = "\n".join((task, template_name, adapter_name, response_text, error or ""))
    return f"trace:{sha256(material.encode('utf-8')).hexdigest()[:16]}"


def combine_prompt_text(system_prompt: str, user_prompt: str) -> str:
    """Combine system and user prompt text in a stable readable form."""
    return f"System:\n{system_prompt.strip()}\n\nUser:\n{user_prompt.strip()}"


def format_routing_summary(decision: RoutingDecision | None) -> str:
    """Format a compact routing summary for prompt rendering."""
    if decision is None:
        return "No routing decision was provided."
    selected = format_selected_modules(decision)
    skipped = ", ".join(decision.skipped_names) if decision.skipped_names else "none"
    return (
        f"Task routed with selected modules: {selected}. "
        f"Skipped modules: {skipped}. Adaptive enabled: {decision.adaptive_enabled}."
    )


def format_selected_modules(decision: RoutingDecision | None) -> str:
    """Format selected modules in route order."""
    if decision is None or not decision.selected_names:
        return "none"
    return ", ".join(decision.selected_names)


def format_context_block(context_items: Sequence[ContextItem]) -> str:
    """Format context items with source and relevance preserved."""
    if not context_items:
        return "No context items were provided."
    lines: list[str] = []
    for index, item in enumerate(context_items, start=1):
        lines.append(f"[{index}] source={item.source}; relevance={item.relevance:.2f}")
        lines.append(item.content)
    return "\n".join(lines)


def format_context_sources(context_items: Sequence[ContextItem]) -> str:
    """Format context source names for prompts and traces."""
    if not context_items:
        return "none"
    return ", ".join(item.source for item in context_items)


def format_workspace_metadata(metadata: Mapping[str, object]) -> str:
    """Format workspace metadata deterministically."""
    if not metadata:
        return "none"
    return "; ".join(f"{key}={metadata[key]}" for key in sorted(metadata))


def optional_string(value: object) -> str | None:
    """Return a string value or None for JSON round-trips."""
    if value is None:
        return None
    return str(value)


def json_compatible(value: object) -> JsonValue:
    """Convert simple nested values into JSON-compatible data."""
    if isinstance(value, Mapping):
        return {str(key): json_compatible(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple | list):
        return [json_compatible(item) for item in value]
    return value
