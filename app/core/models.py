from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    strategist = "strategist"
    analyst = "analyst"
    dispatcher = "dispatcher"
    experience_coach = "experience_coach"


class ExperiencePriority(str, Enum):
    balanced = "balanced"
    crowd_flow = "crowd_flow"
    wait_times = "wait_times"
    accessibility = "accessibility"
    premium_service = "premium_service"


class PriorityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TranscriptSpeaker(str, Enum):
    operator = "operator"
    command = "command"


class AgentStep(BaseModel):
    agent: AgentRole
    prompt: str
    output: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class VenueStrategy(BaseModel):
    north_star: str
    opening_brief: str
    fan_message: str
    hotspot_watchlist: list[str] = Field(default_factory=list)
    quick_wins: list[str] = Field(default_factory=list)
    coordination_focus: list[str] = Field(default_factory=list)


class OperationsScoreCard(BaseModel):
    crowd_flow: int = Field(ge=0, le=10)
    wait_time: int = Field(ge=0, le=10)
    coordination: int = Field(ge=0, le=10)
    fan_experience: int = Field(ge=0, le=10)
    overall: int = Field(ge=0, le=100)
    flagged_risks: list[str] = Field(default_factory=list)
    rubric_notes: list[str] = Field(default_factory=list)


class AnalystFeedback(BaseModel):
    wins: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    coaching_tip: str
    next_move: str


class DispatcherMove(BaseModel):
    operational_response: str
    public_message: str
    staff_actions: list[str] = Field(default_factory=list)
    priority_level: PriorityLevel


class ExperienceCoach(BaseModel):
    experience_upgrade: str
    blindspots: list[str] = Field(default_factory=list)
    accessibility_check: str


class TranscriptTurn(BaseModel):
    speaker: TranscriptSpeaker
    label: str
    message: str
    round_number: int = Field(ge=0)


class RoundSnapshot(BaseModel):
    round_number: int = Field(ge=1)
    operator_update: str
    scorecard: OperationsScoreCard
    analyst_feedback: AnalystFeedback
    public_message: str


class SessionSummary(BaseModel):
    average_crowd_flow: float
    average_wait_time: float
    average_coordination: float
    average_fan_experience: float
    best_call: str
    biggest_bottleneck: str
    next_priority: str


class VenueSessionState(BaseModel):
    venue_name: str
    event_name: str
    expected_attendance: int = Field(ge=1000, le=150000)
    priority: ExperiencePriority
    round_limit: int = Field(default=3, ge=1, le=8)
    current_round: int = Field(default=0, ge=0)
    context: dict[str, Any] = Field(default_factory=dict)
    strategy: VenueStrategy
    transcript: list[TranscriptTurn] = Field(default_factory=list)
    rounds: list[RoundSnapshot] = Field(default_factory=list)
    trace: list[AgentStep] = Field(default_factory=list)


class VenueSessionStartRequest(BaseModel):
    venue_name: str = Field(min_length=3, max_length=120)
    event_name: str = Field(min_length=3, max_length=160)
    expected_attendance: int = Field(ge=1000, le=150000)
    priority: ExperiencePriority = ExperiencePriority.balanced
    round_limit: int = Field(default=3, ge=1, le=8)
    context: dict[str, Any] = Field(default_factory=dict)


class VenueSessionStartResponse(BaseModel):
    venue_name: str
    event_name: str
    expected_attendance: int
    priority: ExperiencePriority
    round_limit: int
    strategy: VenueStrategy
    opening_turn: TranscriptTurn


class VenueOperationsRoundRequest(BaseModel):
    update: str = Field(min_length=20, max_length=4000)


class VenueOperationsRoundResponse(BaseModel):
    round_number: int = Field(ge=1)
    operator_update: str
    scorecard: OperationsScoreCard
    analyst_feedback: AnalystFeedback
    dispatcher_move: DispatcherMove
    experience_coach: ExperienceCoach
    session_complete: bool
    summary: SessionSummary | None = None


class VenueSimulationRequest(BaseModel):
    venue_name: str = Field(min_length=3, max_length=120)
    event_name: str = Field(min_length=3, max_length=160)
    expected_attendance: int = Field(ge=1000, le=150000)
    priority: ExperiencePriority = ExperiencePriority.balanced
    operator_update: str = Field(min_length=20, max_length=4000)
    round_limit: int = Field(default=3, ge=1, le=8)
    context: dict[str, Any] = Field(default_factory=dict)


class VenueSimulationResponse(BaseModel):
    session: VenueSessionStartResponse
    round: VenueOperationsRoundResponse
