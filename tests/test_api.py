from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_simulate_endpoint_returns_session_and_round() -> None:
    response = client.post(
        "/operations/simulate",
        json={
            "venue_name": "Grand National Stadium",
            "event_name": "Championship Opener",
            "expected_attendance": 42000,
            "priority": "crowd_flow",
            "operator_update": (
                "Gate 3 queue reached 18 minutes after two scanners failed, fans are backing into the plaza, "
                "and security plus guest services need a shared reroute before accessible guests get absorbed "
                "into the main line."
            ),
            "round_limit": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session"]["opening_turn"]["message"]
    assert payload["round"]["scorecard"]["overall"] >= 0
    assert payload["round"]["dispatcher_move"]["public_message"]


def test_websocket_flow_runs_single_round() -> None:
    with client.websocket_connect("/ws/operations") as websocket:
        websocket.send_json(
            {
                "type": "start_session",
                "payload": {
                    "venue_name": "SkyDome Arena",
                    "event_name": "City Derby Final",
                    "expected_attendance": 62000,
                    "priority": "wait_times",
                    "round_limit": 1,
                },
            }
        )
        session_started = websocket.receive_json()

        assert session_started["type"] == "session_started"
        assert session_started["payload"]["opening_turn"]["message"]

        websocket.send_json(
            {
                "type": "submit_update",
                "payload": {
                    "update": (
                        "Main east gate scanners slowed to a crawl, queue times are now over 15 minutes, and the "
                        "ops lead needs security, ushers, and guest services aligned on a fallback lane plus clear "
                        "signage for families and accessible guests."
                    )
                },
            }
        )
        round_result = websocket.receive_json()

        assert round_result["type"] == "round_result"
        assert round_result["payload"]["session_complete"] is True
