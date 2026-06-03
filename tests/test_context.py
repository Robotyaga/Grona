from grona import ContextBuilder, ContextItem, Router, create_default_registry


def test_context_item_validates_relevance() -> None:
    item = ContextItem(source="demo:test", content="context", relevance=0.5)

    assert item.source == "demo:test"
    assert item.relevance == 0.5


def test_context_builder_creates_items_for_selected_modules() -> None:
    router = Router(create_default_registry(), top_k=2)
    decision = router.route("Analyze engine overheating symptoms")

    items = ContextBuilder().build(decision)

    assert len(items) == len(decision.selected_modules)
    assert items[0].source.startswith("demo:")
    assert items[0].content
    assert 0.0 <= items[0].relevance <= 1.0
    assert items[0].metadata["module"] in decision.selected_names


def test_context_builder_handles_empty_selection() -> None:
    router = Router(create_default_registry(), minimum_score=100)
    decision = router.route("Unknown task")

    items = ContextBuilder().build(decision)

    assert len(items) == 1
    assert items[0].source == "demo:fallback"
    assert items[0].relevance == 0.0
