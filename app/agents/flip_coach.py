from __future__ import annotations

from app.agents.base import BaseAgent
from app.core.models import AgentRole, ExperienceCoach, OperationsScoreCard, VenueSessionState
from app.core.parsing import load_json_object


class ExperienceCoachAgent(BaseAgent):
    role = AgentRole.experience_coach
    system_prompt = (
        "You are an attendee experience coach for a live sports venue. Review each move through the lens of "
        "clarity, accessibility, comfort, and service recovery."
    )

    def build_prompt(
        self,
        session: VenueSessionState,
        operator_update: str,
        scorecard: OperationsScoreCard,
    ) -> str:
        return (
            "Return JSON for the attendee experience lens.\n"
            'Schema: {"experience_upgrade": str, "blindspots": [str, ...], "accessibility_check": str}\n\n'
            f"Venue:\n{session.venue_name}\n\n"
            f"Event:\n{session.event_name}\n\n"
            f"Experience priority:\n{session.priority.value}\n\n"
            f"Round:\n{session.current_round + 1}\n\n"
            f"Operator update:\n{operator_update}\n\n"
            f"Scorecard:\n{scorecard.model_dump()}\n\n"
            "Focus on signage, accessibility, families, hydration, and how confident the attendee will feel."
        )

    @staticmethod
    def parse(output: str) -> ExperienceCoach:
        return ExperienceCoach.model_validate(load_json_object(output))


FlipCoachAgent = ExperienceCoachAgent
