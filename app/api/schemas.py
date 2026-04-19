from pydantic import BaseModel

from app.core.models import (
    VenueOperationsRoundRequest,
    VenueOperationsRoundResponse,
    VenueSessionStartRequest,
    VenueSessionStartResponse,
    VenueSimulationRequest,
    VenueSimulationResponse,
)


class HealthResponse(BaseModel):
    status: str


VenueSessionStartRequestSchema = VenueSessionStartRequest
VenueSessionStartResponseSchema = VenueSessionStartResponse
VenueOperationsRoundRequestSchema = VenueOperationsRoundRequest
VenueOperationsRoundResponseSchema = VenueOperationsRoundResponse
VenueSimulationRequestSchema = VenueSimulationRequest
VenueSimulationResponseSchema = VenueSimulationResponse

# Backward-compatible aliases for any older imports.
DebateStartRequestSchema = VenueSessionStartRequestSchema
DebateStartResponseSchema = VenueSessionStartResponseSchema
DebateRoundRequestSchema = VenueOperationsRoundRequestSchema
DebateRoundResponseSchema = VenueOperationsRoundResponseSchema
DebateSimulationRequestSchema = VenueSimulationRequestSchema
DebateSimulationResponseSchema = VenueSimulationResponseSchema
