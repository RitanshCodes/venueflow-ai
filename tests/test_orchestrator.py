from app.core.models import ExperiencePriority, VenueOperationsRoundRequest, VenueSessionStartRequest
from app.providers.mock import MockLLMProvider
from app.services.orchestrator import VenueOpsOrchestrator


def test_orchestrator_starts_session_and_scores_round() -> None:
    orchestrator = VenueOpsOrchestrator(MockLLMProvider())
    state, session = orchestrator.start_session(
        VenueSessionStartRequest(
            venue_name="SkyDome Arena",
            event_name="City Derby Final",
            expected_attendance=62000,
            priority=ExperiencePriority.crowd_flow,
            round_limit=2,
        )
    )

    assert session.strategy.opening_brief
    assert session.priority == ExperiencePriority.crowd_flow
    assert state.current_round == 0

    state, round_result = orchestrator.play_round(
        state,
        VenueOperationsRoundRequest(
            update=(
                "Gate 3 queue is at 18 minutes after two scanners went offline, fans are spilling into the plaza, "
                "and we need security, ushers, and guest services on one reroute with an accessible fallback lane."
            )
        ),
    )

    assert round_result.round_number == 1
    assert round_result.scorecard.crowd_flow >= 2
    assert round_result.scorecard.coordination >= 2
    assert round_result.dispatcher_move.operational_response
    assert round_result.experience_coach.experience_upgrade
    assert round_result.analyst_feedback.coaching_tip
    assert round_result.session_complete is False


def test_orchestrator_returns_summary_after_final_round() -> None:
    orchestrator = VenueOpsOrchestrator(MockLLMProvider())
    state, _ = orchestrator.start_session(
        VenueSessionStartRequest(
            venue_name="Harbor Field",
            event_name="Night Cricket Clash",
            expected_attendance=48000,
            priority=ExperiencePriority.wait_times,
            round_limit=1,
        )
    )

    _, round_result = orchestrator.play_round(
        state,
        VenueOperationsRoundRequest(
            update=(
                "Rain pushed everyone under the main concourse, concessions are flooding, and the response now needs "
                "faster queue estimates, extra kiosks, and one fan message that separates family, premium, and "
                "accessible routing."
            )
        ),
    )

    assert round_result.session_complete is True
    assert round_result.summary is not None
    assert round_result.summary.biggest_bottleneck
