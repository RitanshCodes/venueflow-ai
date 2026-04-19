from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.schemas import (
    HealthResponse,
    VenueOperationsRoundRequestSchema,
    VenueSessionStartRequestSchema,
    VenueSessionStartResponseSchema,
    VenueSimulationRequestSchema,
    VenueSimulationResponseSchema,
)
from app.providers.factory import build_provider
from app.services.orchestrator import VenueOpsOrchestrator


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="VenueFlow AI", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.post("/operations/start", response_model=VenueSessionStartResponseSchema)
@app.post("/debates/start", response_model=VenueSessionStartResponseSchema)
def start_operations(request: VenueSessionStartRequestSchema) -> VenueSessionStartResponseSchema:
    orchestrator = VenueOpsOrchestrator(build_provider())
    _, response = orchestrator.start_session(request)
    return response


@app.post("/operations/simulate", response_model=VenueSimulationResponseSchema)
@app.post("/debates/simulate", response_model=VenueSimulationResponseSchema)
def simulate_operations(request: VenueSimulationRequestSchema) -> VenueSimulationResponseSchema:
    orchestrator = VenueOpsOrchestrator(build_provider())
    return orchestrator.simulate(request)


@app.websocket("/ws/operations")
@app.websocket("/ws/debate")
async def operations_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    orchestrator = VenueOpsOrchestrator(build_provider())
    session = None

    try:
        while True:
            message = await websocket.receive_json()
            event_type = message.get("type")
            payload = message.get("payload", {})

            if event_type == "start_session":
                request = VenueSessionStartRequestSchema.model_validate(payload)
                session, response = orchestrator.start_session(request)
                await websocket.send_json({"type": "session_started", "payload": response.model_dump(mode="json")})
                continue

            if event_type in {"submit_update", "submit_argument"}:
                if session is None:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "payload": {"message": "Start a venue simulation before submitting an update."},
                        }
                    )
                    continue

                request = VenueOperationsRoundRequestSchema.model_validate(payload)
                session, response = orchestrator.play_round(session, request)
                await websocket.send_json({"type": "round_result", "payload": response.model_dump(mode="json")})
                continue

            await websocket.send_json(
                {
                    "type": "error",
                    "payload": {"message": f"Unknown event type: {event_type}"},
                }
            )
    except WebSocketDisconnect:
        return
