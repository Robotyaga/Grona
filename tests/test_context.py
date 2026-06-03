from grona import ContextBuilder, ContextItem, Router, create_default_registry


def route(task: str):
    return Router(create_default_registry(), top_k=3).route(task)


def test_context_item_creation() -> None:
    item = ContextItem(
        source="automotive_knowledge_stub",
        content="Check coolant level and fan activation.",
        relevance=0.85,
        metadata={"domain": "automotive"},
    )

    assert item.source == "automotive_knowledge_stub"
    assert item.content
    assert item.relevance == 0.85
    assert item.metadata == {"domain": "automotive"}


def test_context_builder_returns_automotive_context() -> None:
    decision = route("Analyze engine overheating symptoms")

    items = ContextBuilder().build(decision, decision.task)

    assert any(item.metadata.get("module") == "automotive-diagnostics" for item in items)
    assert any("coolant" in item.content for item in items)
    assert all(0.0 <= item.relevance <= 1.0 for item in items)


def test_context_builder_returns_cybersecurity_context() -> None:
    decision = route("Review firewall logs for suspicious port scans")

    items = ContextBuilder().build(decision, decision.task)

    assert any(item.metadata.get("module") == "cybersecurity-scanner" for item in items)
    assert any("threat" in item.content.lower() for item in items)


def test_context_builder_returns_code_context() -> None:
    decision = route("Refactor this Python function and explain why the test fails")

    items = ContextBuilder().build(decision, decision.task)

    assert any(item.metadata.get("module") == "code-assistant" for item in items)
    assert any("code review" in item.content.lower() for item in items)


def test_context_builder_handles_empty_selected_modules() -> None:
    router = Router(create_default_registry(), minimum_score=100)
    decision = router.route("Unknown task")

    items = ContextBuilder().build(decision, "Unknown task")

    assert len(items) == 1
    assert items[0].source == "demo:fallback"
    assert items[0].relevance == 0.0
