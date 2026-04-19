from __future__ import annotations

from app.agents.base import BaseAgent
from app.core.models import AgentRole, AnalystFeedback, OperationsScoreCard, VenueSessionState
from app.core.parsing import load_json_object


class OperationsAnalystAgent(BaseAgent):
    role = AgentRole.analyst
    system_prompt = (
        "You are a venue operations analyst. Evaluate decisions for crowd movement, queue impact, "
        "cross-team coordination, and fan experience, then coach the ops lead on the next action."
    )

    def build_prompt(
        self,
        session: VenueSessionState,
        operator_update: str,
        scorecard: OperationsScoreCard,
    ) -> str:
        return (
            "Return JSON for the operations analyst feedback.\n"
            'Schema: {"wins": [str, ...], "risks": [str, ...], "coaching_tip": str, "next_move": str}\n\n'
            f"Venue:\n{session.venue_name}\n\n"
            f"Event:\n{session.event_name}\n\n"
            f"Experience priority:\n{session.priority.value}\n\n"
            f"Round:\n{session.current_round + 1}\n\n"
            f"Latest operator update:\n{operator_update}\n\n"
            f"Scorecard:\n{scorecard.model_dump()}\n\n"
            "Wins should highlight what is operationally strong. Risks should identify what is still exposed."
        )

    @staticmethod
    def parse(output: str) -> AnalystFeedback:
        return AnalystFeedback.model_validate(load_json_object(output))


JudgeAgent = OperationsAnalystAgent
