"""Local LLM baseline adapter contracts for explicit opt-in experiments."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from json import dumps, loads
from time import perf_counter
from typing import Protocol
from urllib import error, request

Metadata = dict[str, object]
JsonValue = object

LOCAL_LLM_STATIC_MODES = frozenset(("generic", "echo_summary", "weak_monolith"))


@dataclass(frozen=True)
class LocalLLMRequest:
    """One explicit local LLM completion request."""

    prompt: str
    system_prompt: str = "You are a local baseline model for Grona experiments."
    model: str = "local-baseline"
    temperature: float = 0.0
    max_tokens: int = 256
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        prompt: str,
        system_prompt: str = "You are a local baseline model for Grona experiments.",
        model: str = "local-baseline",
        temperature: float = 0.0,
        max_tokens: int = 256,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "prompt", " ".join(prompt.split()))
        object.__setattr__(self, "system_prompt", " ".join(system_prompt.split()))
        object.__setattr__(self, "model", model)
        object.__setattr__(self, "temperature", temperature)
        object.__setattr__(self, "max_tokens", max_tokens)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not self.prompt:
            raise ValueError("local LLM request prompt cannot be empty")
        if not self.system_prompt:
            raise ValueError("local LLM request system_prompt cannot be empty")
        if not model:
            raise ValueError("local LLM request model cannot be empty")
        if not 0.0 <= temperature <= 2.0:
            raise ValueError("local LLM request temperature must be between 0.0 and 2.0")
        if max_tokens <= 0:
            raise ValueError("local LLM request max_tokens must be positive")

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize request to deterministic JSON-compatible data."""
        return {
            "max_tokens": self.max_tokens,
            "metadata": json_compatible(self.metadata),
            "model": self.model,
            "prompt": self.prompt,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
        }

    def to_json(self) -> str:
        """Serialize request as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class LocalLLMResponse:
    """Response from a local LLM baseline adapter."""

    text: str
    model: str
    source: str
    latency_ms: float | None = None
    error: str | None = None
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        text: str,
        model: str,
        source: str,
        latency_ms: float | None = None,
        error: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "text", text.strip())
        object.__setattr__(self, "model", model)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "latency_ms", latency_ms)
        object.__setattr__(self, "error", error)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not model:
            raise ValueError("local LLM response model cannot be empty")
        if not source:
            raise ValueError("local LLM response source cannot be empty")
        if latency_ms is not None and latency_ms < 0:
            raise ValueError("local LLM response latency_ms cannot be negative")

    @property
    def ok(self) -> bool:
        """Return whether the adapter produced text without an error."""
        return self.error is None and bool(self.text)

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize response to deterministic JSON-compatible data."""
        return {
            "error": self.error,
            "latency_ms": self.latency_ms,
            "metadata": json_compatible(self.metadata),
            "model": self.model,
            "ok": self.ok,
            "source": self.source,
            "text": self.text,
        }

    def to_json(self) -> str:
        """Serialize response as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def to_text(self) -> str:
        """Format response for demos."""
        lines = [
            f"Source: {self.source}",
            f"Model: {self.model}",
            f"OK: {self.ok}",
        ]
        if self.latency_ms is not None:
            lines.append(f"Latency: {self.latency_ms:.1f} ms")
        if self.error:
            lines.append(f"Error: {self.error}")
        if self.text:
            lines.append(f"Text: {self.text}")
        return "\n".join(lines)


class LocalLLMAdapter(Protocol):
    """Minimal protocol for explicit local LLM baseline adapters."""

    name: str

    def complete(self, request: LocalLLMRequest) -> LocalLLMResponse:
        """Return one completion response for a request."""
        ...


class StaticLocalLLMAdapter:
    """Deterministic offline local LLM adapter for tests and demos."""

    def __init__(
        self,
        name: str = "static-local-llm",
        mode: str = "weak_monolith",
        model: str = "static-local-baseline",
    ) -> None:
        if not name:
            raise ValueError("static local LLM adapter name cannot be empty")
        if mode not in LOCAL_LLM_STATIC_MODES:
            valid = ", ".join(sorted(LOCAL_LLM_STATIC_MODES))
            raise ValueError(f"unsupported static local LLM mode: {mode}; expected one of {valid}")
        if not model:
            raise ValueError("static local LLM adapter model cannot be empty")
        self.name = name
        self.mode = mode
        self.model = model

    def complete(self, request: LocalLLMRequest) -> LocalLLMResponse:
        """Return deterministic text without network access."""
        text = static_local_llm_text(request.prompt, self.mode)
        return LocalLLMResponse(
            text=text,
            model=request.model or self.model,
            source=self.name,
            latency_ms=0.0,
            metadata={
                "adapter": "static",
                "mode": self.mode,
                "network_used": False,
            },
        )


class LMStudioCompletionAdapter:
    """Optional LM Studio compatible adapter, disabled unless explicitly constructed."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234",
        model: str | None = None,
        timeout: float = 10.0,
        endpoint_path: str = "/v1/chat/completions",
        name: str = "lmstudio-completion",
    ) -> None:
        if not base_url:
            raise ValueError("LM Studio completion base_url cannot be empty")
        if timeout <= 0:
            raise ValueError("LM Studio completion timeout must be positive")
        if not endpoint_path.startswith("/"):
            raise ValueError("LM Studio completion endpoint_path must start with /")
        if not name:
            raise ValueError("LM Studio completion adapter name cannot be empty")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.endpoint_path = endpoint_path
        self.name = name

    def complete(self, request_item: LocalLLMRequest) -> LocalLLMResponse:
        """Call an explicitly configured local LM Studio-compatible server."""
        model = request_item.model or self.model
        if not model:
            return LocalLLMResponse(
                text="",
                model="unconfigured",
                source=self.name,
                error="LM Studio model is not configured",
                metadata={"adapter": "lmstudio", "network_used": False},
            )
        payload = {
            "max_tokens": request_item.max_tokens,
            "messages": [
                {"role": "system", "content": request_item.system_prompt},
                {"role": "user", "content": request_item.prompt},
            ],
            "model": model,
            "temperature": request_item.temperature,
        }
        started_at = perf_counter()
        try:
            data = self._post_json(payload)
            text = parse_chat_completion_text(data)
            latency_ms = (perf_counter() - started_at) * 1000.0
            return LocalLLMResponse(
                text=text,
                model=model,
                source=self.name,
                latency_ms=latency_ms,
                metadata={
                    "adapter": "lmstudio",
                    "base_url": self.base_url,
                    "endpoint_path": self.endpoint_path,
                    "network_used": True,
                },
            )
        except Exception as exc:  # noqa: BLE001
            latency_ms = (perf_counter() - started_at) * 1000.0
            return LocalLLMResponse(
                text="",
                model=model,
                source=self.name,
                latency_ms=latency_ms,
                error=f"LM Studio completion request failed: {exc}",
                metadata={
                    "adapter": "lmstudio",
                    "base_url": self.base_url,
                    "endpoint_path": self.endpoint_path,
                    "network_used": True,
                },
            )

    def _post_json(self, payload: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
        request_data = dumps(payload).encode("utf-8")
        http_request = request.Request(
            f"{self.base_url}{self.endpoint_path}",
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                raw_data = response.read().decode("utf-8")
        except error.URLError as exc:
            raise RuntimeError(str(exc)) from exc
        data = loads(raw_data)
        if not isinstance(data, Mapping):
            raise ValueError("LM Studio response root must be an object")
        return data


@dataclass(frozen=True)
class LocalLLMBaselineResult:
    """Comparison-ready baseline result from one local LLM adapter run."""

    task: str
    adapter_name: str
    response: LocalLLMResponse
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        task: str,
        adapter_name: str,
        response: LocalLLMResponse,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "task", " ".join(task.split()))
        object.__setattr__(self, "adapter_name", adapter_name)
        object.__setattr__(self, "response", response)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not self.task:
            raise ValueError("local LLM baseline task cannot be empty")
        if not adapter_name:
            raise ValueError("local LLM baseline adapter_name cannot be empty")

    def to_dict(self) -> dict[str, JsonValue]:
        """Serialize baseline result to deterministic JSON-compatible data."""
        return {
            "adapter_name": self.adapter_name,
            "metadata": json_compatible(self.metadata),
            "response": self.response.to_dict(),
            "task": self.task,
        }

    def to_json(self) -> str:
        """Serialize baseline result as stable JSON."""
        return dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def to_text(self) -> str:
        """Format baseline result for demos."""
        return "\n".join(
            (
                "Local LLM baseline result",
                f"Task: {self.task}",
                f"Adapter: {self.adapter_name}",
                self.response.to_text(),
                "Limitations: baseline adapter output is not graded for semantic quality.",
            )
        )


class LocalLLMBaselineRunner:
    """Run a task through an explicit local LLM baseline adapter."""

    def __init__(self, adapter: LocalLLMAdapter) -> None:
        self.adapter = adapter

    def run(
        self,
        task: str,
        system_prompt: str = "You are a local baseline model for Grona experiments.",
        model: str = "local-baseline",
        temperature: float = 0.0,
        max_tokens: int = 256,
        metadata: Mapping[str, object] | None = None,
    ) -> LocalLLMBaselineResult:
        """Run one comparison-ready local LLM baseline task."""
        request_item = LocalLLMRequest(
            prompt=task,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
        )
        response = self.adapter.complete(request_item)
        return LocalLLMBaselineResult(
            task=task,
            adapter_name=self.adapter.name,
            response=response,
            metadata={
                "request": request_item.to_dict(),
                "response_ok": response.ok,
            },
        )


def static_local_llm_text(prompt: str, mode: str = "weak_monolith") -> str:
    """Create deterministic offline baseline text."""
    normalized_prompt = " ".join(prompt.split()) or "unspecified task"
    if mode == "generic":
        return f"Static local baseline response for: {normalized_prompt}."
    if mode == "echo_summary":
        return f"Echo summary: {normalized_prompt[:120]}"
    if mode == "weak_monolith":
        return (
            f"Weak monolith baseline for '{normalized_prompt}': answer directly from the whole "
            "prompt without sparse module routing, source-aware context, or growth traces."
        )
    raise ValueError(f"unsupported static local LLM mode: {mode}")


def parse_chat_completion_text(data: Mapping[str, JsonValue]) -> str:
    """Extract assistant text from an OpenAI-compatible chat completion payload."""
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("chat completion response did not include choices")
    first = choices[0]
    if not isinstance(first, Mapping):
        raise ValueError("chat completion choice is invalid")
    message = first.get("message")
    if not isinstance(message, Mapping):
        raise ValueError("chat completion choice did not include a message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("chat completion content is empty")
    return content.strip()


def json_compatible(value: object) -> JsonValue:
    """Convert simple nested values into JSON-compatible data."""
    if isinstance(value, Mapping):
        return {str(key): json_compatible(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple | list):
        return [json_compatible(item) for item in value]
    return value
