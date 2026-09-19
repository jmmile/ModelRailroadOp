"""Tests for Model Railroad Operations companion authentication."""

from fastapi.testclient import TestClient

from modelrailroadops.web import server


def pair_client(client):
    """Pair a test browser with the current companion server."""

    response = client.post(
        "/api/pair",
        json={
            "code": server.PAIRING_CODE,
        },
    )

    assert response.status_code == 200

    return response


def same_origin_headers(client):
    """Return headers representing a same-origin companion request."""

    return {
        "Origin": str(client.base_url).rstrip("/"),
    }


def test_health_does_not_require_pairing():
    """The diagnostic health endpoint remains publicly available."""

    with TestClient(server.app) as client:
        response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["application"] == (
        "Model Railroad Operations Companion"
    )


def test_authentication_status_reports_unpaired_browser():
    """A new browser starts without companion authentication."""

    with TestClient(server.app) as client:
        response = client.get("/api/auth/status")

    assert response.status_code == 200
    assert response.json() == {
        "authenticated": False,
    }


def test_sessions_reject_unpaired_browser():
    """Railroad session data is unavailable before pairing."""

    with TestClient(server.app) as client:
        response = client.get("/api/sessions")

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "This device is not paired."
    )


def test_incorrect_pairing_code_is_rejected():
    """An incorrect six-digit pairing code does not authenticate."""

    incorrect_code = (
        "000000"
        if server.PAIRING_CODE != "000000"
        else "999999"
    )

    with TestClient(server.app) as client:
        response = client.post(
            "/api/pair",
            json={
                "code": incorrect_code,
            },
        )

        assert response.status_code == 401

        status_response = client.get(
            "/api/auth/status"
        )

    assert status_response.status_code == 200
    assert status_response.json() == {
        "authenticated": False,
    }


def test_correct_pairing_code_authenticates_browser():
    """The current pairing code authenticates the browser."""

    with TestClient(server.app) as client:
        response = pair_client(client)

        assert response.json() == {
            "paired": True,
        }

        status_response = client.get(
            "/api/auth/status"
        )

    assert status_response.status_code == 200
    assert status_response.json() == {
        "authenticated": True,
    }


def test_authenticated_browser_can_request_sessions():
    """A paired browser can reach the protected sessions endpoint."""

    with TestClient(server.app) as client:
        pair_client(client)

        response = client.get("/api/sessions")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_forged_authentication_cookie_is_rejected():
    """An arbitrary cookie value cannot authenticate a browser."""

    with TestClient(server.app) as client:
        client.cookies.set(
            server.AUTH_COOKIE_NAME,
            "not-the-real-authentication-token",
        )

        response = client.get("/api/sessions")

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "This device is not paired."
    )


def test_waybill_details_reject_unpaired_browser():
    """Waybill details are protected by companion authentication."""

    with TestClient(server.app) as client:
        response = client.get(
            "/api/waybills/26"
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "This device is not paired."
    )


def test_waybill_details_return_not_found():
    """A paired browser receives 404 for an unknown Waybill."""

    with TestClient(server.app) as client:
        pair_client(client)

        response = client.get(
            "/api/waybills/999999999"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Waybill not found."
    )


def test_waybill_details_return_operator_information():
    """A paired browser can retrieve read-only Waybill details."""

    with TestClient(server.app) as client:
        pair_client(client)

        response = client.get(
            "/api/waybills/26"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 26
    assert data["car_display"] == "GN 33103"
    assert data["status"] == "COMPLETED"

    assert "load_state" in data
    assert "commodity" in data
    assert "cargo_weight_lbs" in data
    assert "gross_weight_lbs" in data
    assert "tonnage" in data
    assert "origin" in data
    assert "destination" in data
    assert "notes" in data


def test_move_completion_rejects_unpaired_browser(
    monkeypatch,
):
    """An unpaired browser cannot complete a Car Move."""

    called = False

    def fake_complete_move(car_move_id):
        nonlocal called
        called = True
        return True, "PICKUP completed successfully."

    monkeypatch.setattr(
        server.SwitchListMoveService,
        "complete_move",
        fake_complete_move,
    )

    with TestClient(server.app) as client:
        response = client.post(
            "/api/moves/123/complete",
            headers=same_origin_headers(client),
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "This device is not paired."
    )
    assert called is False


def test_move_completion_requires_origin(
    monkeypatch,
):
    """A paired write request must include its browser Origin."""

    called = False

    def fake_complete_move(car_move_id):
        nonlocal called
        called = True
        return True, "PICKUP completed successfully."

    monkeypatch.setattr(
        server.SwitchListMoveService,
        "complete_move",
        fake_complete_move,
    )

    with TestClient(server.app) as client:
        pair_client(client)

        response = client.post(
            "/api/moves/123/complete",
        )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "This write request did not originate from "
        "the companion application."
    )
    assert called is False


def test_move_completion_rejects_cross_origin_request(
    monkeypatch,
):
    """A paired browser cannot submit a cross-origin write."""

    called = False

    def fake_complete_move(car_move_id):
        nonlocal called
        called = True
        return True, "PICKUP completed successfully."

    monkeypatch.setattr(
        server.SwitchListMoveService,
        "complete_move",
        fake_complete_move,
    )

    with TestClient(server.app) as client:
        pair_client(client)

        response = client.post(
            "/api/moves/123/complete",
            headers={
                "Origin": "http://example.invalid",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "This write request did not originate from "
        "the companion application."
    )
    assert called is False


def test_move_completion_accepts_authenticated_same_origin_request(
    monkeypatch,
):
    """A paired same-origin browser may request move completion."""

    requested_move_ids = []

    def fake_complete_move(car_move_id):
        requested_move_ids.append(
            car_move_id
        )

        return (
            True,
            "PICKUP completed successfully.",
        )

    monkeypatch.setattr(
        server.SwitchListMoveService,
        "complete_move",
        fake_complete_move,
    )

    with TestClient(server.app) as client:
        pair_client(client)

        response = client.post(
            "/api/moves/123/complete",
            headers=same_origin_headers(client),
        )

    assert response.status_code == 200
    assert response.json() == {
        "completed": True,
        "car_move_id": 123,
        "message": "PICKUP completed successfully.",
    }
    assert requested_move_ids == [123]


def test_move_completion_returns_conflict_when_service_rejects_move(
    monkeypatch,
):
    """A railroad-rule rejection is returned as HTTP conflict."""

    requested_move_ids = []

    def fake_complete_move(car_move_id):
        requested_move_ids.append(
            car_move_id
        )

        return (
            False,
            "This Car Move has already been completed.",
        )

    monkeypatch.setattr(
        server.SwitchListMoveService,
        "complete_move",
        fake_complete_move,
    )

    with TestClient(server.app) as client:
        pair_client(client)

        response = client.post(
            "/api/moves/123/complete",
            headers=same_origin_headers(client),
        )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "This Car Move has already been completed."
    )
    assert requested_move_ids == [123]