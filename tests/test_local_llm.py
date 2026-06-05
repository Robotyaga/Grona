from grona import (
    ExperimentConfig,
    ExperimentRunner,
    LMStudioCompletionAdapter,
    LocalLLMBaselineRunner,
    LocalLLMRequest,
    LocalLLMResponse,
    StaticLocalLLMAdapter,
    create_demo_benchmark_cases,
    create_demo_experiment_configs,
)
from grona.entrypoint import main as entrypoint_main
from grona.local_llm import parse_chat_completion_text
from grona.local_llm_cli import format_local_llm_static_demo


def test_local_llm_request_creation_and_serialization() -> None:
    request = LocalLLMRequest(
        "  Explain   sparse routing. ",
        model="demo-model",
        metadata={"source": "test"},
    )

    assert request.prompt == "Explain sparse routing."
    assert request.model == "demo-model"
    assert request.temperature == 0.0
    assert request.max_tokens == 256
    assert request.to_json() == request.to_json()


def test_local_llm_request_rejects_empty_prompt() -> None:
    try:
        LocalLLMRequest("   ")
    except ValueError as exc:
        assert "prompt cannot be empty" in str(exc)
    else:
        raise AssertionError("expected empty prompt to fail")


def test_local_llm_response_ok_and_text_formatting() -> None:
    response = LocalLLMResponse("Answer", "demo-model", "static", latency_ms=1.5)

    assert response.ok is True
    assert response.to_dict()["ok"] is True
    assert "Answer" in response.to_text()
    assert response.to_json() == response.to_json()


def test_local_llm_response_error_is_not_ok() -> None:
    response = LocalLLMResponse("", "demo-model", "static", error="offline")

    assert response.ok is False
    assert "offline" in response.to_text()


def test_static_local_llm_adapter_is_deterministic() -> None:
    adapter = StaticLocalLLMAdapter(mode="echo_summary")
    request = LocalLLMRequest("Explain sparse routing.")

    first = adapter.complete(request)
    second = adapter.complete(request)

    assert first == second
    assert first.ok is True
    assert first.metadata["network_used"] is False
    assert "Echo summary" in first.text


def test_static_local_llm_adapter_rejects_unknown_mode() -> None:
    try:
        StaticLocalLLMAdapter(mode="real-model")
    except ValueError as exc:
        assert "unsupported static local LLM mode" in str(exc)
    else:
        raise AssertionError("expected unsupported static mode to fail")


def test_local_llm_baseline_runner_returns_comparison_ready_result() -> None:
    adapter = StaticLocalLLMAdapter(mode="weak_monolith")
    result = LocalLLMBaselineRunner(adapter).run("Explain sparse routing.")

    assert result.adapter_name == "static-local-llm"
    assert result.response.ok is True
    assert result.metadata["response_ok"] is True
    assert "Local LLM baseline result" in result.to_text()
    assert result.to_json() == result.to_json()


def test_lmstudio_completion_adapter_construction_only() -> None:
    adapter = LMStudioCompletionAdapter(
        base_url="http://127.0.0.1:1234",
        model="local-model",
        timeout=0.5,
    )

    assert adapter.name == "lmstudio-completion"
    assert adapter.base_url == "http://127.0.0.1:1234"
    assert adapter.model == "local-model"


def test_parse_chat_completion_text_rejects_invalid_payload() -> None:
    try:
        parse_chat_completion_text({"choices": []})
    except ValueError as exc:
        assert "choices" in str(exc)
    else:
        raise AssertionError("expected invalid chat completion payload to fail")


def test_experiment_runner_requires_adapter_for_local_llm_mode() -> None:
    configs = (
        ExperimentConfig("routing-only", "Routing baseline.", "routing_only"),
        ExperimentConfig("local-llm", "Local LLM baseline.", "local_llm_baseline"),
    )
    runner = ExperimentRunner(create_demo_benchmark_cases(), configs)

    try:
        runner.run()
    except ValueError as exc:
        assert "requires local_llm_adapter" in str(exc)
    else:
        raise AssertionError("expected local_llm_baseline without adapter to fail")


def test_experiment_runner_can_use_static_local_llm_adapter() -> None:
    configs = (
        ExperimentConfig("routing-only", "Routing baseline.", "routing_only"),
        ExperimentConfig("local-llm", "Local LLM baseline.", "local_llm_baseline"),
    )
    runner = ExperimentRunner(
        create_demo_benchmark_cases(),
        configs,
        local_llm_adapter=StaticLocalLLMAdapter(),
    )

    results, comparison = runner.run_and_compare()

    assert len(results) == 2
    assert comparison.candidate_config_names == ("local-llm",)
    assert results[1].config.mode == "local_llm_baseline"


def test_existing_demo_experiment_configs_remain_deterministic() -> None:
    runner = ExperimentRunner(create_demo_benchmark_cases(), create_demo_experiment_configs())

    first = runner.run_and_compare()[1].to_json()
    second = runner.run_and_compare()[1].to_json()

    assert first == second


def test_local_llm_static_cli_demo_behavior() -> None:
    output = format_local_llm_static_demo()

    assert "Local LLM baseline static demo" in output
    assert "deterministic static adapter only" in output
    assert "Baseline result JSON:" in output


def test_entrypoint_routes_local_llm_static_demo(capsys) -> None:
    status = entrypoint_main(("--local-llm-static-demo",))
    output = capsys.readouterr().out

    assert status == 0
    assert "Local LLM baseline static demo" in output
