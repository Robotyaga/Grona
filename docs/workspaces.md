# Workspaces

A Grona workspace is a lightweight in-memory profile for a project or use case. It describes the configured vineyard: active modules, relevant domains, memory sources, tool profiles, routing mode, adaptive defaults, safety defaults, and metadata.

The workspace layer is intentionally small. It uses dataclasses and the Python standard library only.

See also [Architecture](architecture.md), [Project vision](project-vision.md), [Development notes](development.md), and [Roadmap](roadmap.md).

## Core Types

### WorkspaceProfile

`WorkspaceProfile` describes a named profile:

- `name`
- `description`
- `enabled_modules`
- `enabled_domains`
- `memory_sources`
- `tool_profiles`
- `routing_mode`
- `adaptive_enabled`
- `safety_enabled`
- `metadata`

Routing modes are simple strings:

- `basic`
- `adaptive`
- `orchestrated`
- `safe_orchestrated`

### WorkspaceConfig

`WorkspaceConfig` wraps a profile with optional structured settings:

- `routing_settings`
- `context_settings`
- `safety_settings`
- `memory_settings`
- `tool_settings`
- `metadata`

This is not a config framework. It is a small serializable object for reproducible prototype settings.

## Serialization

Both `WorkspaceProfile` and `WorkspaceConfig` support:

- `to_dict()`
- `from_dict()`
- `to_json()`
- `from_json()`

JSON serialization is deterministic enough for tests through sorted keys.

## Built-In Profiles

Grona includes these built-in workspace profiles:

- `default`: broad profile with all default modules.
- `code`: code, software, documents, and general reasoning; adaptive routing enabled.
- `cybersecurity`: cybersecurity, code, documents, and general reasoning; safety enabled.
- `media`: media/video/audio, documents, and general reasoning.
- `automotive`: automotive, documents, and general reasoning; safety enabled.
- `documents`: document search, retrieval, knowledge, and general reasoning.

## Routing Effects

`filter_modules_for_workspace(registry, profile)` returns a new `ModuleRegistry`:

- If `enabled_modules` is non-empty, only those modules are selected.
- Otherwise, modules matching `enabled_domains` are selected.
- If filtering selects modules, `general-reasoning` is preserved as a fallback when available.
- The original registry is not mutated.

## CLI Usage

```bash
python -m grona "Diagnose engine overheating" --workspace automotive
python -m grona "Review this Python script for security issues" --workspace cybersecurity
python -m grona "Plan MotionCam RAW workflow" --workspace media
python -m grona "Find document indexing notes" --workspace documents
```

The CLI prints the active workspace, routing mode, enabled domains, enabled modules, memory sources, and tool profiles before routing or orchestration output.

Workspace defaults can enable adaptive routing, safety, or orchestration. Explicit CLI flags such as `--adaptive`, `--safe`, and `--orchestrate` still enable those same behaviors predictably.

## Current Limitations

- No persisted workspace directory yet.
- No external config files are loaded from disk.
- No secrets, credentials, or user-specific private settings.
- No production config management.
- No filesystem scanning or project auto-discovery.
- No external APIs or database-backed profiles.

The workspace layer is only a deterministic profile/config foundation for future project-specific Grona setups.
