from grona import (
    WorkspaceConfig,
    WorkspaceProfile,
    create_automotive_workspace_profile,
    create_code_assistant_workspace_profile,
    create_cybersecurity_workspace_profile,
    create_default_registry,
    create_default_workspace_profile,
    create_document_research_workspace_profile,
    create_media_workflow_workspace_profile,
    filter_modules_for_workspace,
    get_builtin_workspace_profile,
)
from grona.cli import main


def test_workspace_profile_creation() -> None:
    profile = WorkspaceProfile(
        name="test",
        description="Test workspace.",
        enabled_modules=("code-assistant",),
        enabled_domains=("code",),
        memory_sources=("notes",),
        tool_profiles=("mock_code_inspector",),
        routing_mode="adaptive",
        adaptive_enabled=True,
        safety_enabled=True,
        metadata={"kind": "unit"},
    )

    assert profile.name == "test"
    assert profile.enabled_modules == ("code-assistant",)
    assert profile.routing_mode == "adaptive"
    assert profile.metadata == {"kind": "unit"}


def test_workspace_config_creation() -> None:
    profile = create_default_workspace_profile()
    config = WorkspaceConfig(
        profile,
        routing_settings={"top_k": 2},
        context_settings={"max_context_items": 4},
        safety_settings={"dry_run": True},
        memory_settings={"sources": "demo"},
        tool_settings={"tools": "mock"},
        metadata={"project": "demo"},
    )

    assert config.profile == profile
    assert config.routing_settings == {"top_k": 2}
    assert config.metadata == {"project": "demo"}


def test_workspace_profile_dict_round_trip() -> None:
    profile = create_cybersecurity_workspace_profile()

    restored = WorkspaceProfile.from_dict(profile.to_dict())

    assert restored == profile
    assert restored.safety_enabled is True
    assert "mock_security_checklist" in restored.tool_profiles


def test_workspace_profile_json_round_trip_is_deterministic() -> None:
    profile = create_automotive_workspace_profile()

    first = profile.to_json()
    restored = WorkspaceProfile.from_json(first)
    second = restored.to_json()

    assert restored == profile
    assert first == second
    assert '"name": "automotive"' in first


def test_workspace_config_json_round_trip() -> None:
    config = WorkspaceConfig(
        create_media_workflow_workspace_profile(),
        routing_settings={"mode": "demo"},
    )

    restored = WorkspaceConfig.from_json(config.to_json())

    assert restored == config
    assert restored.profile.name == "media"


def test_default_workspace_profile_keeps_all_modules() -> None:
    registry = create_default_registry()
    profile = create_default_workspace_profile()

    filtered = filter_modules_for_workspace(registry, profile)

    assert filtered.names() == registry.names()


def test_workspace_specific_profiles_enable_expected_domains() -> None:
    assert "automotive" in create_automotive_workspace_profile().enabled_domains
    assert "cybersecurity" in create_cybersecurity_workspace_profile().enabled_domains
    assert "media" in create_media_workflow_workspace_profile().enabled_domains
    assert "documents" in create_document_research_workspace_profile().enabled_domains
    assert create_code_assistant_workspace_profile().adaptive_enabled is True


def test_registry_filtering_by_enabled_modules() -> None:
    registry = create_default_registry()
    profile = WorkspaceProfile(
        name="module-filter",
        description="Filter by module names.",
        enabled_modules=("code-assistant",),
    )

    filtered = filter_modules_for_workspace(registry, profile)

    assert filtered.names() == ("code-assistant", "general-reasoning")
    assert registry.names() != filtered.names()


def test_registry_filtering_by_enabled_domains() -> None:
    registry = create_default_registry()
    profile = WorkspaceProfile(
        name="domain-filter",
        description="Filter by domains.",
        enabled_domains=("media", "documents"),
    )

    filtered = filter_modules_for_workspace(registry, profile)

    assert "media-video-tool" in filtered.names()
    assert "document-search" in filtered.names()
    assert "code-assistant" not in filtered.names()


def test_general_fallback_preserved_when_filtering() -> None:
    registry = create_default_registry()
    profile = create_automotive_workspace_profile()

    filtered = filter_modules_for_workspace(registry, profile)

    assert "automotive-diagnostics" in filtered.names()
    assert "general-reasoning" in filtered.names()


def test_get_builtin_workspace_profile() -> None:
    assert get_builtin_workspace_profile("default").name == "default"
    assert get_builtin_workspace_profile("documents").name == "documents"


def test_cli_workspace_filters_routing(capsys) -> None:
    assert main(["Plan", "MotionCam", "RAW", "workflow", "--workspace", "media"]) == 0

    output = capsys.readouterr().out
    assert "Workspace: media" in output
    assert "media-video-tool" in output
    assert "automotive-diagnostics" not in output


def test_cli_workspace_safety_orchestrates(capsys) -> None:
    assert main(["Diagnose", "engine", "overheating", "--workspace", "automotive"]) == 0

    output = capsys.readouterr().out
    assert "Workspace: automotive" in output
    assert "workspace implies orchestration" in output
    assert "workspace enables safety by default" in output
    assert "Orchestration summary:" in output
