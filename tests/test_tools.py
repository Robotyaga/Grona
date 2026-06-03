from grona import (
    MockToolAdapter,
    Orchestrator,
    Router,
    SafeToolRunner,
    SafetyPolicy,
    ToolAdapter,
    ToolRegistry,
    ToolRequest,
    ToolResult,
    ToolSpec,
    create_default_adapter_registry,
    create_default_registry,
    create_default_safety_policy,
    create_default_tool_registry,
)
from grona.cli import main


def test_tool_spec_creation() -> None:
    spec = ToolSpec(
        name="mock_reader",
        description="Read-only mock reader.",
        action_type="read_file",
        risk_level="low",
        read_only=True,
        input_schema={"query": "str"},
        metadata={"domain": "docs"},
    )

    assert spec.name == "mock_reader"
    assert spec.input_schema == {"query": "str"}
    assert spec.metadata == {"domain": "docs"}


def test_tool_request_creation() -> None:
    request = ToolRequest(
        "mock_code_inspector",
        "Review code",
        inputs={"path": "src"},
        requested_by="code-assistant",
        metadata={"demo": True},
    )

    assert request.tool_name == "mock_code_inspector"
    assert request.inputs == {"path": "src"}
    assert request.requested_by == "code-assistant"


def test_tool_result_formatting() -> None:
    result = ToolResult(
        "mock_code_inspector",
        True,
        "Prepared checkpoints.",
        details=("Check tests.",),
    )

    output = result.to_text()

    assert "Tool: mock_code_inspector" in output
    assert "Status: success" in output
    assert "Check tests." in output


def test_mock_tool_adapter_planning() -> None:
    adapter = create_default_tool_registry().get("mock_code_inspector")
    assert adapter is not None

    action = adapter.plan_action(
        ToolRequest("mock_code_inspector", "Review code", requested_by="code-assistant")
    )

    assert action.name == "mock_code_inspector"
    assert action.action_type == "read_file"
    assert action.risk_level == "low"
    assert action.read_only is True


def test_mock_tool_adapter_execution() -> None:
    adapter = create_default_tool_registry().get("mock_document_search")
    assert adapter is not None

    result = adapter.execute(
        ToolRequest("mock_document_search", "Find docs", requested_by="document-search")
    )

    assert result.success is True
    assert "Mock document search" in result.output
    assert result.metadata["tool_adapter"] == "mock"


def test_tool_registry_register_get_list_and_find() -> None:
    registry = ToolRegistry()
    adapter = MockToolAdapter(
        ToolSpec(
            name="mock_reader",
            description="Read-only mock reader.",
            action_type="read_file",
            risk_level="low",
            read_only=True,
            metadata={"domain": "docs"},
        ),
        output="Read-only result.",
    )

    registry.register(adapter)

    assert registry.get("mock_reader") is adapter
    assert registry.list() == (adapter,)
    assert registry.find_by_action_type("read_file") == (adapter,)
    assert registry.find_by_metadata("domain", "docs") == (adapter,)


def test_safe_tool_runner_allowed_action() -> None:
    runner = SafeToolRunner(create_default_tool_registry(), create_default_safety_policy())

    result = runner.run(
        ToolRequest("mock_code_inspector", "Review code", requested_by="code-assistant")
    )

    assert result.success is True
    assert result.metadata["policy_allowed"] is True
    assert result.metadata["policy_dry_run"] is False
    assert "Mock code inspector" in result.output


def test_safe_tool_runner_blocked_action() -> None:
    registry = ToolRegistry(
        (
            MockToolAdapter(
                ToolSpec(
                    name="mock_delete",
                    description="Mock delete.",
                    action_type="delete_file",
                    risk_level="high",
                    read_only=False,
                ),
                output="Should not run.",
            ),
        )
    )
    runner = SafeToolRunner(registry, create_default_safety_policy())

    result = runner.run(ToolRequest("mock_delete", "Delete cache"))

    assert result.success is False
    assert result.metadata["policy_allowed"] is False
    assert "blocked" in result.output.lower()


def test_safe_tool_runner_dry_run_behavior() -> None:
    runner = SafeToolRunner(create_default_tool_registry(), create_default_safety_policy())

    result = runner.run(
        ToolRequest(
            "mock_security_checklist",
            "Review security exposure",
            requested_by="cybersecurity-scanner",
        )
    )

    assert result.success is True
    assert result.metadata["policy_allowed"] is True
    assert result.metadata["policy_dry_run"] is True
    assert "dry-run" in result.output


def test_safe_tool_runner_missing_tool() -> None:
    runner = SafeToolRunner(create_default_tool_registry())

    result = runner.run(ToolRequest("missing_tool", "Try missing tool"))

    assert result.success is False
    assert result.metadata["tool_missing"] is True


def test_orchestrator_includes_demo_tool_results() -> None:
    runner = SafeToolRunner(create_default_tool_registry(), create_default_safety_policy())
    result = Orchestrator(
        Router(create_default_registry(), top_k=3),
        adapter_registry=create_default_adapter_registry(),
        safety_policy=create_default_safety_policy(),
        tool_runner=runner,
    ).run("Review this Python package for tests and exposed secrets")

    assert result.metadata["tool_results_used"] is True
    assert result.metadata["tool_result_count"] > 0
    assert any("Tool result from" in detail for item in result.expert_results for detail in item.details)


def test_cli_use_demo_tools(capsys) -> None:
    assert main(
        [
            "Review",
            "this",
            "Python",
            "script",
            "for",
            "security",
            "issues",
            "--orchestrate",
            "--use-demo-adapters",
            "--use-demo-tools",
            "--safe",
        ]
    ) == 0

    output = capsys.readouterr().out
    assert "Tools: mock tool results used" in output
    assert "Execution: deterministic mock tools only" in output


def test_tool_adapter_protocol_import_is_available() -> None:
    assert ToolAdapter is not None
