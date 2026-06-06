from grona import (
    ContextBuilder,
    ContextItem,
    InferenceTrace,
    InMemoryInferenceTraceStore,
    JsonlInferenceTraceStore,
    PromptBuilder,
    PromptTemplate,
    RenderedPrompt,
    Router,
    create_default_registry,
    default_prompt_templates,
    get_default_prompt_template,
    run_static_prompt_trace,
)
from grona.entrypoint import main as entrypoint_main
from grona.prompt_trace_cli import format_prompt_trace_demo


def build_demo_route(task: str = "Explain sparse routing."):
    router = Router(create_default_registry(), top_k=2)
    decision = router.route(task)
    context_items = ContextBuilder().build(decision, task)
    return decision, context_items


def test_prompt_template_creation_and_rendering() -> None:
    template = PromptTemplate(
        "unit_template",
        "Unit test template.",
        "System sees {task}.",
        "User asks {task} with {selected_modules}.",
        metadata={"source": "test"},
    )

    rendered = template.render({"task": "Demo task", "selected_modules": "module-a"})

    assert template.name == "unit_template"
    assert template.required_fields() == frozenset(("selected_modules", "task"))
    assert rendered.template_name == "unit_template"
    assert "Demo task" in rendered.full_prompt
    assert template.to_dict()["metadata"] == {"source": "test"}


def test_prompt_template_rejects_unsupported_fields() -> None:
    try:
        PromptTemplate("bad", "Bad template.", "System {unknown}.", "User {task}.")
    except ValueError as exc:
        assert "unsupported fields" in str(exc)
    else:
        raise AssertionError("expected unsupported prompt field to fail")


def test_prompt_template_missing_fields_are_clear() -> None:
    template = PromptTemplate("needs_task", "Needs task.", "System {task}.", "User {task}.")

    try:
        template.render({})
    except ValueError as exc:
        assert "missing fields: task" in str(exc)
    else:
        raise AssertionError("expected missing field to fail")


def test_default_prompt_templates_exist() -> None:
    templates = default_prompt_templates()

    assert set(templates) == {
        "general_task",
        "grona_vs_monolith_baseline",
        "knowledge_seed_proposal",
        "routing_trace_summary",
        "training_example_review",
    }
    assert get_default_prompt_template("general_task").name == "general_task"


def test_prompt_builder_renders_deterministic_prompt() -> None:
    task = "Explain route provenance."
    decision, context_items = build_demo_route(task)
    builder = PromptBuilder(get_default_prompt_template("general_task"))

    first = builder.build(task, routing_decision=decision, context_items=context_items)
    second = builder.build(task, routing_decision=decision, context_items=context_items)

    assert first == second
    assert "Explain route provenance." in first.user_prompt
    assert "Selected modules" in first.user_prompt
    assert first.metadata["context_count"] == len(context_items)


def test_prompt_builder_accepts_manual_context_items() -> None:
    item = ContextItem("manual:test", "Manual prompt context.", 0.75)
    prompt = PromptBuilder(get_default_prompt_template("routing_trace_summary")).build(
        "Summarize routing.",
        context_items=(item,),
        workspace_metadata={"workspace": "unit"},
    )

    assert "manual:test" in prompt.user_prompt
    assert "workspace=unit" in prompt.user_prompt


def test_rendered_prompt_serialization_round_trip() -> None:
    prompt = RenderedPrompt(
        "demo",
        "System prompt.",
        "User prompt.",
        metadata={"source": "test"},
    )

    rebuilt = RenderedPrompt.from_dict(prompt.to_dict())

    assert rebuilt == prompt
    assert prompt.to_json() == prompt.to_json()
    assert "System prompt" in prompt.to_text()


def test_inference_trace_creation_and_json_round_trip() -> None:
    prompt = RenderedPrompt("demo", "System prompt.", "User prompt.")
    trace = InferenceTrace(
        "trace:unit",
        "2026-01-01T00:00:00+00:00",
        "Demo task",
        prompt,
        "static-local-llm",
        "local-baseline",
        "Demo response",
        selected_modules=("general-reasoning",),
        context_sources=("demo:general-reasoning",),
        metadata={"source": "test"},
    )

    rebuilt = InferenceTrace.from_json(trace.to_json())

    assert trace.ok is True
    assert rebuilt == trace
    assert rebuilt.to_dict()["selected_modules"] == ["general-reasoning"]


def test_in_memory_inference_trace_store() -> None:
    result = run_static_prompt_trace("Explain trace storage.")
    store = InMemoryInferenceTraceStore()

    store.add(result.trace)

    assert store.count() == 1
    assert store.list() == (result.trace,)
    assert store.get(result.trace.trace_id) == result.trace
    assert store.get("missing") is None
    store.clear()
    assert store.count() == 0


def test_jsonl_inference_trace_store(tmp_path) -> None:
    result = run_static_prompt_trace("Explain JSONL trace storage.")
    store = JsonlInferenceTraceStore(tmp_path / "traces.jsonl")

    store.add(result.trace)

    assert store.count() == 1
    assert store.list() == (result.trace,)
    assert store.get(result.trace.trace_id) == result.trace
    store.clear()
    assert store.count() == 0


def test_static_prompt_trace_runner_is_deterministic() -> None:
    task = "Explain prompt provenance."
    decision, context_items = build_demo_route(task)

    first = run_static_prompt_trace(task, routing_decision=decision, context_items=context_items)
    second = run_static_prompt_trace(task, routing_decision=decision, context_items=context_items)

    assert first.trace == second.trace
    assert first.response.ok is True
    assert first.trace.metadata["network_used"] is False
    assert first.trace.prompt.template_name == "general_task"


def test_prompt_trace_cli_demo_behavior() -> None:
    output = format_prompt_trace_demo()

    assert "Prompt trace demo" in output
    assert "deterministic static adapter only" in output
    assert "Rendered prompt preview:" in output
    assert "Trace JSON preview:" in output


def test_entrypoint_routes_prompt_trace_demo(capsys) -> None:
    status = entrypoint_main(("--prompt-trace-demo",))
    output = capsys.readouterr().out

    assert status == 0
    assert "Prompt trace demo" in output
