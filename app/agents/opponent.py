from __future__ import annotations

from app.agents.base import BaseAgent
from app.core.models import AgentRole, DispatcherMove, VenueSessionState
from app.core.parsing import load_json_object


class DispatcherAgent(BaseAgent):
    role = AgentRole.dispatcher
    system_prompt = (
        "You are an incident dispatcher for a large sports venue. Turn updates into concrete response moves, "
        "staff deployment orders, and calm attendee messaging."
    )

    def build_prompt(self, session: VenueSessionState, operator_update: str) -> str:
        timeline = "\n".join(f"- {turn.speaker.value} [{turn.label}]: {turn.message}" for turn in session.transcript[-6:])
        return (
            "Return JSON for the dispatcher response move.\n"
            'Schema: {"operational_response": str, "public_message": str, '
            '"staff_actions": [str, ...], "priority_level": str}\n\n'
            f"Venue:\n{session.venue_name}\n\n"
            f"Event:\n{session.event_name}\n\n"
            f"Expected attendance:\n{session.expected_attendance}\n\n"
            f"Experience priority:\n{session.priority.value}\n\n"
            f"Current round:\n{session.current_round + 1}\n\n"
            f"Session strategy:\n{session.strategy.model_dump()}\n\n"
            f"Recent timeline:\n{timeline}\n\n"
            f"Latest operator update:\n{operator_update}\n\n"
            "Recommend concrete field action, clear fan messaging, and a priority level of low, medium, high, or critical."
        )

    @staticmethod
    def parse(output: str) -> DispatcherMove:
        return DispatcherMove.model_validate(load_json_object(output))


OpponentAgent = DispatcherAgent
