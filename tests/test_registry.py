from grona import ExpertModule, ModuleRegistry


def make_module(name: str) -> ExpertModule:
    return ExpertModule(
        name=name,
        domain="test",
        capabilities=("testing",),
        keywords=(name,),
        handler=lambda task, context: task,
    )


def test_modules_can_be_registered_and_replaced() -> None:
    registry = ModuleRegistry()
    first = make_module("alpha")
    replacement = make_module("alpha")

    registry.register(first)
    registry.register(replacement)

    assert len(registry) == 1
    assert registry.get("alpha") is replacement
    assert registry.names() == ("alpha",)
