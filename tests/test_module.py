from grona import ExpertModule


def test_expert_module_runs_handler_with_context() -> None:
    module = ExpertModule(
        name="test-module",
        domain="testing",
        capabilities=("echo",),
        keywords=("test",),
        handler=lambda task, context: f"{task} via {context['route']}",
    )

    assert module.run("hello", {"route": "unit-test"}) == "hello via unit-test"
