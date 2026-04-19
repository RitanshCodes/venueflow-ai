from __future__ import annotations

import argparse
import json

from app.core.models import ExperiencePriority, VenueSessionStartRequest, VenueSimulationRequest
from app.providers.factory import build_provider
from app.services.orchestrator import VenueOpsOrchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the VenueFlow AI command-center workflow.")
    parser.add_argument("--venue", required=True, help="Venue or stadium name.")
    parser.add_argument("--event", required=True, help="Event name.")
    parser.add_argument(
        "--attendance",
        type=int,
        required=True,
        help="Expected attendance for the event.",
    )
    parser.add_argument(
        "--priority",
        default=ExperiencePriority.balanced.value,
        choices=[priority.value for priority in ExperiencePriority],
        help="Which attendee-experience dimension should get the strongest bias.",
    )
    parser.add_argument(
        "--round-limit",
        type=int,
        default=3,
        help="How many live rounds to run before the final summary.",
    )
    parser.add_argument(
        "--context",
        default="{}",
        help="Optional JSON object with additional context.",
    )
    parser.add_argument(
        "--update",
        help="Optional live operator update. If omitted, the CLI prints only the kickoff packet.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context = json.loads(args.context)
    orchestrator = VenueOpsOrchestrator(build_provider())
    priority = ExperiencePriority(args.priority)

    if args.update:
        result = orchestrator.simulate(
            VenueSimulationRequest(
                venue_name=args.venue,
                event_name=args.event,
                expected_attendance=args.attendance,
                priority=priority,
                operator_update=args.update,
                round_limit=args.round_limit,
                context=context,
            )
        )

        print("\n=== Command Brief ===\n")
        print(result.session.opening_turn.message)
        print("\n=== Scorecard ===\n")
        print(result.round.scorecard.model_dump_json(indent=2))
        print("\n=== Analyst Feedback ===\n")
        print(result.round.analyst_feedback.model_dump_json(indent=2))
        print("\n=== Dispatcher Move ===\n")
        print(result.round.dispatcher_move.operational_response)
        print("\n=== Experience Lens ===\n")
        print(result.round.experience_coach.experience_upgrade)
        return

    _, session = orchestrator.start_session(
        VenueSessionStartRequest(
            venue_name=args.venue,
            event_name=args.event,
            expected_attendance=args.attendance,
            priority=priority,
            round_limit=args.round_limit,
            context=context,
        )
    )

    print("\n=== Command Brief ===\n")
    print(session.opening_turn.message)
    print("\n=== North Star ===\n")
    print(session.strategy.north_star)
    print("\n=== Fan Message ===\n")
    print(session.strategy.fan_message)
    print("\n=== Hotspot Watchlist ===\n")
    for item in session.strategy.hotspot_watchlist:
        print(f"- {item}")


if __name__ == "__main__":
    main()
