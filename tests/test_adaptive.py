from grona import (
    AdaptiveRoutingConfig,
    FeedbackRecord,
    Router,
    build_module_feedback_stats,
    create_default_registry,
)


def make_decision(task: str):
    return Router(create_default_registry(), top_k=3).route(task)


def make_record(
    task: str,
    success: bool | None = None,
    rating: int | None = None,
) -> FeedbackRecord:
    return FeedbackRecord.from_decision(
        make_decision(task),
        success=success,
        rating=rating,
        timestamp="2026-01-01T00:00:00+00:00",
    )


def route_with_feedback(task: str, records, config: AdaptiveRoutingConfig | None = None):
    return Router(
        create_default_registry(),
        top_k=3,
        adaptive_config=config or AdaptiveRoutingConfig(enabled=True),
        feedback_records=tuple(records),
    ).route(task)


def find_match(decision, module_name: str):
    return next(
        match
        for match in (*decision.selected_modules, *decision.skipped_modules)
        if match.module.name == module_name
    )


def test_build_module_feedback_stats() -> None:
    records = [
        make_record("Review firewall logs for suspicious port scans", success=True, rating=5),
        make_record("Review firewall logs for suspicious port scans", success=False, rating=3),
    ]

    stats = build_module_feedback_stats(records)["cybersecurity-scanner"]

    assert stats.times_selected == 2
    assert stats.successes == 1
    assert stats.failures == 1
    assert stats.average_rating == 4.0
    assert stats.success_rate == 0.5
    assert stats.average_confidence > 0


def test_success_history_boosts_relevant_module() -> None:
    task = "Review firewall logs for suspicious port scans"
    base = find_match(make_decision(task), "cybersecurity-scanner")
    adaptive = find_match(
        route_with_feedback(task, [make_record(task, success=True, rating=5)]),
        "cybersecurity-scanner",
    )

    assert adaptive.score > base.score
    assert adaptive.adaptive_adjustment > 0
    assert "adaptive boost" in adaptive.feedback_summary


def test_failure_history_penalizes_relevant_module() -> None:
    task = "Review firewall logs for suspicious port scans"
    base = find_match(make_decision(task), "cybersecurity-scanner")
    adaptive = find_match(
        route_with_feedback(task, [make_record(task, success=False, rating=1)]),
        "cybersecurity-scanner",
    )

    assert adaptive.score < base.score
    assert adaptive.adaptive_adjustment < 0
    assert "adaptive penalty" in adaptive.feedback_summary


def test_rating_influences_adjustment() -> None:
    task = "Analyze engine overheating symptoms"
    high = find_match(
        route_with_feedback(task, [make_record(task, rating=5)]),
        "automotive-diagnostics",
    )
    low = find_match(
        route_with_feedback(task, [make_record(task, rating=1)]),
        "automotive-diagnostics",
    )

    assert high.adaptive_adjustment > 0
    assert low.adaptive_adjustment < 0


def test_max_adjustment_cap_is_applied() -> None:
    task = "Analyze engine overheating symptoms"
    config = AdaptiveRoutingConfig(enabled=True, success_boost=10.0, max_adjustment=0.2)
    adaptive = find_match(
        route_with_feedback(task, [make_record(task, success=True, rating=5)], config),
        "automotive-diagnostics",
    )

    assert adaptive.adaptive_adjustment == 0.2


def test_disabled_adaptive_routing_matches_normal_routing() -> None:
    task = "Review firewall logs for suspicious port scans"
    normal = make_decision(task)
    disabled = route_with_feedback(
        task,
        [make_record(task, success=True, rating=5)],
        AdaptiveRoutingConfig(enabled=False),
    )

    assert [(match.module.name, match.score) for match in disabled.selected_modules] == [
        (match.module.name, match.score) for match in normal.selected_modules
    ]
    assert disabled.adaptive_enabled is False


def test_adaptive_history_does_not_select_irrelevant_module() -> None:
    relevant_task = "Review firewall logs for suspicious port scans"
    irrelevant_task = "Create thumbnails from a video clip and extract audio metadata"
    decision = route_with_feedback(
        irrelevant_task,
        [make_record(relevant_task, success=True, rating=5)],
    )

    cybersecurity = find_match(decision, "cybersecurity-scanner")
    assert cybersecurity.module.name not in decision.selected_names
    assert cybersecurity.base_score == 0
    assert cybersecurity.adaptive_adjustment == 0


def test_adaptive_explanations_are_present() -> None:
    task = "Review firewall logs for suspicious port scans"
    decision = route_with_feedback(task, [make_record(task, success=True, rating=5)])
    match = find_match(decision, "cybersecurity-scanner")

    assert decision.adaptive_enabled is True
    assert decision.feedback_available is True
    assert match.base_score is not None
    assert match.feedback_summary is not None
    assert any("base score" in reason for reason in match.reasons)
