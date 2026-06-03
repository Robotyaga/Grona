from grona import Router, RoutingDecision, create_default_registry


def route(task: str) -> RoutingDecision:
    return Router(create_default_registry(), top_k=3).route(task)


def selected_names(decision: RoutingDecision) -> set[str]:
    return set(decision.selected_names)


def skipped_names(decision: RoutingDecision) -> set[str]:
    return set(decision.skipped_names)


def test_router_selects_code_module_for_code_task() -> None:
    decision = route("Refactor this Python function and explain why the test fails.")

    assert "code-assistant" in selected_names(decision)
    assert "automotive-diagnostics" in skipped_names(decision)


def test_router_selects_car_diagnostics_for_engine_task() -> None:
    decision = route("Analyze why my car engine overheats while idling in traffic.")

    assert "automotive-diagnostics" in selected_names(decision)
    assert "cybersecurity-scanner" in skipped_names(decision)


def test_router_selects_cybersecurity_module_for_security_task() -> None:
    decision = route("Review firewall logs for suspicious port scans and malware indicators.")

    assert "cybersecurity-scanner" in selected_names(decision)
    assert "media-video-tool" in skipped_names(decision)


def test_irrelevant_modules_are_skipped() -> None:
    decision = route("Create thumbnails from a video clip and extract audio metadata.")

    assert "media-video-tool" in selected_names(decision)
    assert "automotive-diagnostics" in skipped_names(decision)
    assert "cybersecurity-scanner" in skipped_names(decision)


def test_routing_decisions_include_reasons_and_scores() -> None:
    decision = route("Find the PDF manual in my document archive.")
    document_match = next(match for match in decision.selected_modules if match.module.name == "document-search")

    assert document_match.score > 0
    assert document_match.reasons
    assert any("keyword match" in reason for reason in document_match.reasons)


def test_scores_are_deterministic_for_same_task() -> None:
    first = route("Review firewall logs for suspicious port scans.")
    second = route("Review firewall logs for suspicious port scans.")

    first_scores = [(match.module.name, match.score) for match in first.selected_modules]
    second_scores = [(match.module.name, match.score) for match in second.selected_modules]
    assert first_scores == second_scores
