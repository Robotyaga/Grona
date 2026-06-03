"""Workspace profiles and lightweight project configuration for Grona."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from json import dumps, loads
from typing import Any

from .feedback import Metadata
from .registry import ModuleRegistry
from .router import normalized_terms

ROUTING_MODES = ("basic", "adaptive", "orchestrated", "safe_orchestrated")
BUILTIN_WORKSPACES = ("default", "code", "cybersecurity", "media", "automotive", "documents")


@dataclass(frozen=True)
class WorkspaceProfile:
    """A lightweight profile describing one configured Grona workspace."""

    name: str
    description: str
    enabled_modules: tuple[str, ...] = ()
    enabled_domains: tuple[str, ...] = ()
    memory_sources: tuple[str, ...] = ()
    tool_profiles: tuple[str, ...] = ()
    routing_mode: str = "basic"
    adaptive_enabled: bool = False
    safety_enabled: bool = False
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        description: str,
        enabled_modules: Sequence[str] = (),
        enabled_domains: Sequence[str] = (),
        memory_sources: Sequence[str] = (),
        tool_profiles: Sequence[str] = (),
        routing_mode: str = "basic",
        adaptive_enabled: bool = False,
        safety_enabled: bool = False,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "enabled_modules", tuple(enabled_modules))
        object.__setattr__(self, "enabled_domains", tuple(enabled_domains))
        object.__setattr__(self, "memory_sources", tuple(memory_sources))
        object.__setattr__(self, "tool_profiles", tuple(tool_profiles))
        object.__setattr__(self, "routing_mode", routing_mode)
        object.__setattr__(self, "adaptive_enabled", adaptive_enabled)
        object.__setattr__(self, "safety_enabled", safety_enabled)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        if not name:
            raise ValueError("workspace profile name cannot be empty")
        if not description:
            raise ValueError("workspace profile description cannot be empty")
        if routing_mode not in ROUTING_MODES:
            raise ValueError(f"unsupported routing_mode: {routing_mode}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the profile to deterministic JSON-compatible data."""
        return {
            "name": self.name,
            "description": self.description,
            "enabled_modules": list(self.enabled_modules),
            "enabled_domains": list(self.enabled_domains),
            "memory_sources": list(self.memory_sources),
            "tool_profiles": list(self.tool_profiles),
            "routing_mode": self.routing_mode,
            "adaptive_enabled": self.adaptive_enabled,
            "safety_enabled": self.safety_enabled,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> WorkspaceProfile:
        """Deserialize a workspace profile from JSON-compatible data."""
        return cls(
            name=str(data["name"]),
            description=str(data["description"]),
            enabled_modules=tuple(data.get("enabled_modules", ())),
            enabled_domains=tuple(data.get("enabled_domains", ())),
            memory_sources=tuple(data.get("memory_sources", ())),
            tool_profiles=tuple(data.get("tool_profiles", ())),
            routing_mode=str(data.get("routing_mode", "basic")),
            adaptive_enabled=bool(data.get("adaptive_enabled", False)),
            safety_enabled=bool(data.get("safety_enabled", False)),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_json(self) -> str:
        """Serialize the profile to deterministic JSON text."""
        return dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, data: str) -> WorkspaceProfile:
        """Deserialize a workspace profile from JSON text."""
        return cls.from_dict(loads(data))


@dataclass(frozen=True)
class WorkspaceConfig:
    """Structured workspace configuration without external config dependencies."""

    profile: WorkspaceProfile
    routing_settings: Metadata = field(default_factory=dict)
    context_settings: Metadata = field(default_factory=dict)
    safety_settings: Metadata = field(default_factory=dict)
    memory_settings: Metadata = field(default_factory=dict)
    tool_settings: Metadata = field(default_factory=dict)
    metadata: Metadata = field(default_factory=dict)

    def __init__(
        self,
        profile: WorkspaceProfile,
        routing_settings: Mapping[str, object] | None = None,
        context_settings: Mapping[str, object] | None = None,
        safety_settings: Mapping[str, object] | None = None,
        memory_settings: Mapping[str, object] | None = None,
        tool_settings: Mapping[str, object] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        object.__setattr__(self, "profile", profile)
        object.__setattr__(self, "routing_settings", dict(routing_settings or {}))
        object.__setattr__(self, "context_settings", dict(context_settings or {}))
        object.__setattr__(self, "safety_settings", dict(safety_settings or {}))
        object.__setattr__(self, "memory_settings", dict(memory_settings or {}))
        object.__setattr__(self, "tool_settings", dict(tool_settings or {}))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the config to deterministic JSON-compatible data."""
        return {
            "profile": self.profile.to_dict(),
            "routing_settings": dict(self.routing_settings),
            "context_settings": dict(self.context_settings),
            "safety_settings": dict(self.safety_settings),
            "memory_settings": dict(self.memory_settings),
            "tool_settings": dict(self.tool_settings),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> WorkspaceConfig:
        """Deserialize a workspace config from JSON-compatible data."""
        return cls(
            profile=WorkspaceProfile.from_dict(dict(data["profile"])),
            routing_settings=dict(data.get("routing_settings") or {}),
            context_settings=dict(data.get("context_settings") or {}),
            safety_settings=dict(data.get("safety_settings") or {}),
            memory_settings=dict(data.get("memory_settings") or {}),
            tool_settings=dict(data.get("tool_settings") or {}),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_json(self) -> str:
        """Serialize the config to deterministic JSON text."""
        return dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, data: str) -> WorkspaceConfig:
        """Deserialize a workspace config from JSON text."""
        return cls.from_dict(loads(data))


def create_default_workspace_profile() -> WorkspaceProfile:
    """Create the broad default workspace profile."""
    return WorkspaceProfile(
        name="default",
        description="General Grona workspace with all default demo modules available.",
        enabled_domains=(),
        memory_sources=("demo_memory", "demo_document_sources"),
        tool_profiles=("mock_tools",),
        routing_mode="basic",
        metadata={"profile_kind": "built_in"},
    )


def create_code_assistant_workspace_profile() -> WorkspaceProfile:
    """Create a code-focused workspace profile."""
    return WorkspaceProfile(
        name="code",
        description="Workspace for code review, debugging, and repository planning.",
        enabled_domains=("code", "software", "programming", "documents", "general"),
        memory_sources=("python_project_notes", "code_quality_checklists"),
        tool_profiles=("mock_code_inspector", "mock_document_search"),
        routing_mode="adaptive",
        adaptive_enabled=True,
        safety_enabled=False,
        metadata={"profile_kind": "built_in"},
    )


def create_cybersecurity_workspace_profile() -> WorkspaceProfile:
    """Create a cybersecurity-focused workspace profile."""
    return WorkspaceProfile(
        name="cybersecurity",
        description="Workspace for security review, logs, and risk triage.",
        enabled_domains=("cybersecurity", "security", "network", "code", "documents", "general"),
        memory_sources=("security_checklists", "incident_notes", "code_review_notes"),
        tool_profiles=("mock_security_checklist", "mock_code_inspector"),
        routing_mode="safe_orchestrated",
        adaptive_enabled=True,
        safety_enabled=True,
        metadata={"profile_kind": "built_in"},
    )


def create_media_workflow_workspace_profile() -> WorkspaceProfile:
    """Create a media workflow workspace profile."""
    return WorkspaceProfile(
        name="media",
        description="Workspace for media, video, audio, and MotionCam-style workflows.",
        enabled_domains=("media", "video", "audio", "documents", "general"),
        memory_sources=("codec_notes", "color_workflow_notes", "stabilization_notes"),
        tool_profiles=("mock_media_metadata_reader", "mock_document_search"),
        routing_mode="orchestrated",
        adaptive_enabled=False,
        safety_enabled=False,
        metadata={"profile_kind": "built_in"},
    )


def create_automotive_workspace_profile() -> WorkspaceProfile:
    """Create an automotive diagnostics workspace profile."""
    return WorkspaceProfile(
        name="automotive",
        description="Workspace for vehicle diagnostics and repair reasoning.",
        enabled_domains=("automotive", "car", "engine", "vehicle", "documents", "general"),
        memory_sources=("automotive_notes", "repair_checklists"),
        tool_profiles=("mock_automotive_checklist", "mock_document_search"),
        routing_mode="safe_orchestrated",
        adaptive_enabled=False,
        safety_enabled=True,
        metadata={"profile_kind": "built_in"},
    )


def create_document_research_workspace_profile() -> WorkspaceProfile:
    """Create a document research workspace profile."""
    return WorkspaceProfile(
        name="documents",
        description="Workspace for document search, notes, indexing, and evidence review.",
        enabled_domains=("documents", "document", "search", "retrieval", "knowledge", "general"),
        memory_sources=("document_index_notes", "research_notes"),
        tool_profiles=("mock_document_search",),
        routing_mode="orchestrated",
        adaptive_enabled=False,
        safety_enabled=False,
        metadata={"profile_kind": "built_in"},
    )


def get_builtin_workspace_profile(name: str) -> WorkspaceProfile:
    """Return one built-in workspace profile by CLI-friendly name."""
    profiles = {
        "default": create_default_workspace_profile,
        "code": create_code_assistant_workspace_profile,
        "cybersecurity": create_cybersecurity_workspace_profile,
        "media": create_media_workflow_workspace_profile,
        "automotive": create_automotive_workspace_profile,
        "documents": create_document_research_workspace_profile,
    }
    try:
        return profiles[name]()
    except KeyError as exc:
        available = ", ".join(BUILTIN_WORKSPACES)
        raise ValueError(f"unknown workspace '{name}'. Available: {available}") from exc


def filter_modules_for_workspace(
    registry: ModuleRegistry,
    profile: WorkspaceProfile,
    preserve_general_fallback: bool = True,
) -> ModuleRegistry:
    """Return a filtered registry for a workspace without mutating the original."""
    modules = registry.all()
    if profile.enabled_modules:
        enabled_names = set(profile.enabled_modules)
        selected = [module for module in modules if module.name in enabled_names]
    elif profile.enabled_domains:
        enabled_terms = normalized_terms(profile.enabled_domains)
        selected = [
            module for module in modules if normalized_terms((module.domain,)) & enabled_terms
        ]
    else:
        selected = list(modules)

    if preserve_general_fallback and selected:
        selected_names = {module.name for module in selected}
        fallback = next((module for module in modules if module.name == "general-reasoning"), None)
        if fallback is not None and fallback.name not in selected_names:
            selected.append(fallback)

    return ModuleRegistry(selected)
