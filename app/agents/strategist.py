from __future__ import annotations

from app.agents.base import BaseAgent
from app.core.models import AgentRole, ExperiencePriority, VenueStrategy
from app.core.parsing import load_json_object


class VenueStrategistAgent(BaseAgent):
    role = AgentRole.strategist
    system_prompt = (
        "You are a sports venue operations strategist. Design clear crowd-flow plans, "
        "queue-reduction tactics, and live coordination priorities that improve the fan experience."
    )

    def build_prompt(
        self,
        venue_name: str,
        event_name: str,
        expected_attendance: int,
        priority: ExperiencePriority,
        round_limit: int,
        context: dict,
    ) -> str:
        return (
            "Return JSON for a venue kickoff packet.\n"
            'Schema: {"north_star": str, "opening_brief": str, "fan_message": str, '
            '"hotspot_watchlist": [str, ...], "quick_wins": [str, ...], '
            '"coordination_focus": [str, ...]}\n\n'
            f"Venue:\n{venue_name}\n\n"
            f"Event:\n{event_name}\n\n"
            f"Expected attendance:\n{expected_attendance}\n\n"
            f"Experience priority:\n{priority.value}\n\n"
            f"Round limit:\n{round_limit}\n\n"
            f"Extra context:\n{context}\n\n"
            "Design for crowd movement, wait-time reduction, and real-time coordination. "
            "Keep the opening brief specific enough for a hackathon demo."
        )

    @staticmethod
    def parse(output: str) -> VenueStrategy:
        return VenueStrategy.model_validate(load_json_object(output))


StrategistAgent = VenueStrategistAgent
