from __future__ import annotations

from statistics import mean

from app.agents.flip_coach import ExperienceCoachAgent
from app.agents.judge import OperationsAnalystAgent
from app.agents.opponent import DispatcherAgent
from app.agents.strategist import VenueStrategistAgent
from app.core.models import (
    AgentStep,
    RoundSnapshot,
    SessionSummary,
    TranscriptSpeaker,
    TranscriptTurn,
    VenueOperationsRoundRequest,
    VenueOperationsRoundResponse,
    VenueSessionStartRequest,
    VenueSessionStartResponse,
    VenueSessionState,
    VenueSimulationRequest,
    VenueSimulationResponse,
)
from app.providers.base import LLMProvider
from app.services.scoring import VenueOperationsScorer


class VenueOpsOrchestrator:
    def __init__(self, provider: LLMProvider, scorer: VenueOperationsScorer | None = None) -> None:
        self.strategist = VenueStrategistAgent(provider)
        self.dispatcher = DispatcherAgent(provider)
        self.analyst = OperationsAnalystAgent(provider)
        self.experience_coach = ExperienceCoachAgent(provider)
        self.scorer = scorer or VenueOperationsScorer()

    def start_session(
        self,
        request: VenueSessionStartRequest,
    ) -> tuple[VenueSessionState, VenueSessionStartResponse]:
        trace: list[AgentStep] = []

        strategist_prompt = self.strategist.build_prompt(
            request.venue_name,
            request.event_name,
            request.expected_attendance,
            request.priority,
            request.round_limit,
            request.context,
        )
        strategist_raw = self.strategist.run(strategist_prompt)
        strategy = self.strategist.parse(strategist_raw.output)
        trace.append(
            AgentStep(
                agent=self.strategist.role,
                prompt=strategist_raw.prompt,
                output=strategist_raw.output,
            )
        )

        opening_turn = TranscriptTurn(
            speaker=TranscriptSpeaker.command,
            label="Command Brief",
            message=strategy.opening_brief,
            round_number=0,
        )
        state = VenueSessionState(
            venue_name=request.venue_name,
            event_name=request.event_name,
            expected_attendance=request.expected_attendance,
            priority=request.priority,
            round_limit=request.round_limit,
            context=request.context,
            strategy=strategy,
            transcript=[opening_turn],
            trace=trace,
        )

        response = VenueSessionStartResponse(
            venue_name=state.venue_name,
            event_name=state.event_name,
            expected_attendance=state.expected_attendance,
            priority=state.priority,
            round_limit=state.round_limit,
            strategy=state.strategy,
            opening_turn=opening_turn,
        )
        return state, response

    def play_round(
        self,
        state: VenueSessionState,
        request: VenueOperationsRoundRequest,
    ) -> tuple[VenueSessionState, VenueOperationsRoundResponse]:
        round_number = state.current_round + 1
        latest_command_message = self._latest_command_message(state)

        operator_turn = TranscriptTurn(
            speaker=TranscriptSpeaker.operator,
            label="Field Update",
            message=request.update,
            round_number=round_number,
        )
        state.transcript.append(operator_turn)

        scorecard = self.scorer.score_update(
            request.update,
            latest_command_message=latest_command_message,
            event_name=state.event_name,
        )

        analyst_prompt = self.analyst.build_prompt(state, request.update, scorecard)
        analyst_raw = self.analyst.run(analyst_prompt)
        analyst_feedback = self.analyst.parse(analyst_raw.output)
        state.trace.append(
            AgentStep(
                agent=self.analyst.role,
                prompt=analyst_raw.prompt,
                output=analyst_raw.output,
                metadata={"round": round_number},
            )
        )

        dispatcher_prompt = self.dispatcher.build_prompt(state, request.update)
        dispatcher_raw = self.dispatcher.run(dispatcher_prompt)
        dispatcher_move = self.dispatcher.parse(dispatcher_raw.output)
        state.trace.append(
            AgentStep(
                agent=self.dispatcher.role,
                prompt=dispatcher_raw.prompt,
                output=dispatcher_raw.output,
                metadata={"round": round_number},
            )
        )

        command_turn = TranscriptTurn(
            speaker=TranscriptSpeaker.command,
            label=f"{dispatcher_move.priority_level.value.title()} Response",
            message=dispatcher_move.operational_response,
            round_number=round_number,
        )
        state.transcript.append(command_turn)

        experience_prompt = self.experience_coach.build_prompt(state, request.update, scorecard)
        experience_raw = self.experience_coach.run(experience_prompt)
        experience_coach = self.experience_coach.parse(experience_raw.output)
        state.trace.append(
            AgentStep(
                agent=self.experience_coach.role,
                prompt=experience_raw.prompt,
                output=experience_raw.output,
                metadata={"round": round_number},
            )
        )

        state.current_round = round_number
        state.rounds.append(
            RoundSnapshot(
                round_number=round_number,
                operator_update=request.update,
                scorecard=scorecard,
                analyst_feedback=analyst_feedback,
                public_message=dispatcher_move.public_message,
            )
        )

        session_complete = state.current_round >= state.round_limit
        summary = self._build_summary(state) if session_complete else None

        response = VenueOperationsRoundResponse(
            round_number=round_number,
            operator_update=request.update,
            scorecard=scorecard,
            analyst_feedback=analyst_feedback,
            dispatcher_move=dispatcher_move,
            experience_coach=experience_coach,
            session_complete=session_complete,
            summary=summary,
        )
        return state, response

    def simulate(self, request: VenueSimulationRequest) -> VenueSimulationResponse:
        state, session = self.start_session(
            VenueSessionStartRequest(
                venue_name=request.venue_name,
                event_name=request.event_name,
                expected_attendance=request.expected_attendance,
                priority=request.priority,
                round_limit=request.round_limit,
                context=request.context,
            )
        )
        _, round_result = self.play_round(state, VenueOperationsRoundRequest(update=request.operator_update))
        return VenueSimulationResponse(session=session, round=round_result)

    def _latest_command_message(self, state: VenueSessionState) -> str:
        for turn in reversed(state.transcript):
            if turn.speaker is TranscriptSpeaker.command:
                return turn.message
        return state.strategy.opening_brief

    def _build_summary(self, state: VenueSessionState) -> SessionSummary:
        crowd_flow_scores = [round_item.scorecard.crowd_flow for round_item in state.rounds]
        wait_time_scores = [round_item.scorecard.wait_time for round_item in state.rounds]
        coordination_scores = [round_item.scorecard.coordination for round_item in state.rounds]
        fan_experience_scores = [round_item.scorecard.fan_experience for round_item in state.rounds]

        strongest_round = max(state.rounds, key=lambda round_item: round_item.scorecard.overall)
        lowest_dimension = min(
            (
                ("crowd_flow", mean(crowd_flow_scores)),
                ("wait_time", mean(wait_time_scores)),
                ("coordination", mean(coordination_scores)),
                ("fan_experience", mean(fan_experience_scores)),
            ),
            key=lambda item: item[1],
        )[0]

        bottleneck_map = {
            "crowd_flow": "Pedestrian routing still depends too much on reaction instead of pre-positioned flow control.",
            "wait_time": "Queue pressure is not being converted into fast enough service recovery.",
            "coordination": "The response still needs tighter ownership and cross-team rhythm.",
            "fan_experience": "Guest confidence, accessibility, and reassurance are lagging the operational move.",
        }
        next_priority_map = {
            "crowd_flow": "Pre-open fallback routes and assign zone owners before the next demand spike.",
            "wait_time": "Track queue ETA every few minutes and trigger backup lanes earlier.",
            "coordination": "Create a tighter dispatch loop with one named owner and one reporting cadence.",
            "fan_experience": "Pair every operational move with signage, an accessible option, and one fan-facing message.",
        }

        return SessionSummary(
            average_crowd_flow=round(mean(crowd_flow_scores), 2),
            average_wait_time=round(mean(wait_time_scores), 2),
            average_coordination=round(mean(coordination_scores), 2),
            average_fan_experience=round(mean(fan_experience_scores), 2),
            best_call=strongest_round.analyst_feedback.coaching_tip,
            biggest_bottleneck=bottleneck_map[lowest_dimension],
            next_priority=next_priority_map[lowest_dimension],
        )


DebateCoachOrchestrator = VenueOpsOrchestrator
