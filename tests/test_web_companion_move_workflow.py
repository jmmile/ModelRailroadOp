"""End-to-end tests for companion Car Move workflow."""

from fastapi.testclient import TestClient

from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.web import server
from test_switch_list_output import seed_switch_list


def pair_client(client):
    """Pair a test browser with the companion server."""

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


def move_url(
    operations_session_id,
    train_id,
):
    """Return the companion Train Work endpoint."""

    return (
        f"/api/sessions/{operations_session_id}"
        f"/trains/{train_id}/moves"
    )


def complete_move(
    client,
    car_move_id,
):
    """Complete one Car Move through the companion API."""

    return client.post(
        f"/api/moves/{car_move_id}/complete",
        headers=same_origin_headers(client),
    )


def get_move_by_id(
    moves,
    car_move_id,
):
    """Find one Car Move in a companion response."""

    return next(
        move
        for move in moves
        if move["car_move_id"] == car_move_id
    )


def configure_test_database(
    monkeypatch,
    test_database,
):
    """Point companion move services at the pytest database."""

    monkeypatch.setattr(
        "modelrailroadops.services."
        "switch_list_move_service.SessionLocal",
        test_database.SessionLocal,
    )

    monkeypatch.setattr(
        "modelrailroadops.services."
        "switch_list_service.SessionLocal",
        test_database.SessionLocal,
    )


def test_two_companion_clients_share_move_completion_state(
    test_database,
    monkeypatch,
):
    """
    Two paired companion clients see the same railroad state.

    This reproduces the manually verified iPad/desktop workflow:

    1. Both clients see the generated PICKUP and SETOUT.
    2. The first client completes the PICKUP.
    3. The second client sees the PICKUP completed and SETOUT pending.
    4. The second client completes the SETOUT.
    5. The first client sees no remaining active Train Work.
    """

    record_ids = seed_switch_list(
        test_database
    )

    configure_test_database(
        monkeypatch,
        test_database,
    )

    operations_session_id = (
        record_ids["operations_session_id"]
    )

    train_id = record_ids["train_id"]

    pickup_id = record_ids["pickup_id"]
    setout_id = record_ids["setout_id"]

    url = move_url(
        operations_session_id,
        train_id,
    )

    with (
        TestClient(server.app) as ipad_client,
        TestClient(server.app) as desktop_client,
    ):
        pair_client(ipad_client)
        pair_client(desktop_client)

        #
        # Both companion devices initially see the same
        # generated switch-list work.
        #

        ipad_response = ipad_client.get(
            url
        )

        desktop_response = desktop_client.get(
            url
        )

        assert ipad_response.status_code == 200
        assert desktop_response.status_code == 200

        ipad_moves = ipad_response.json()
        desktop_moves = desktop_response.json()

        assert len(ipad_moves) == 2
        assert len(desktop_moves) == 2

        ipad_pickup = get_move_by_id(
            ipad_moves,
            pickup_id,
        )

        ipad_setout = get_move_by_id(
            ipad_moves,
            setout_id,
        )

        desktop_pickup = get_move_by_id(
            desktop_moves,
            pickup_id,
        )

        desktop_setout = get_move_by_id(
            desktop_moves,
            setout_id,
        )

        assert ipad_pickup["move_type"] == "PICKUP"
        assert ipad_pickup["move_status"] == "PENDING"

        assert ipad_setout["move_type"] == "SETOUT"
        assert ipad_setout["move_status"] == "PENDING"

        assert desktop_pickup["move_type"] == "PICKUP"
        assert desktop_pickup["move_status"] == "PENDING"

        assert desktop_setout["move_type"] == "SETOUT"
        assert desktop_setout["move_status"] == "PENDING"

        #
        # Simulate completing the PICKUP from the iPad.
        #

        pickup_response = complete_move(
            ipad_client,
            pickup_id,
        )

        assert pickup_response.status_code == 200
        assert pickup_response.json()["completed"] is True
        assert (
            pickup_response.json()["car_move_id"]
            == pickup_id
        )

        #
        # Verify the database lifecycle after PICKUP.
        #

        with test_database.SessionLocal() as session:
            pickup = session.get(
                CarMove,
                pickup_id,
            )

            setout = session.get(
                CarMove,
                setout_id,
            )

            waybill = session.get(
                Waybill,
                record_ids["waybill_id"],
            )

            assert pickup.status == "COMPLETED"
            assert setout.status == "PENDING"
            assert waybill.status == "IN_PROGRESS"

        #
        # Simulate the desktop requesting fresh Train Work.
        # It must see the state written by the iPad.
        #

        desktop_response = desktop_client.get(
            url
        )

        assert desktop_response.status_code == 200

        desktop_moves = desktop_response.json()

        assert len(desktop_moves) == 2

        desktop_pickup = get_move_by_id(
            desktop_moves,
            pickup_id,
        )

        desktop_setout = get_move_by_id(
            desktop_moves,
            setout_id,
        )

        assert (
            desktop_pickup["move_status"]
            == "COMPLETED"
        )

        assert (
            desktop_setout["move_status"]
            == "PENDING"
        )

        assert (
            desktop_pickup["waybill_status"]
            == "IN_PROGRESS"
        )

        assert (
            desktop_setout["waybill_status"]
            == "IN_PROGRESS"
        )

        #
        # Simulate completing the SETOUT from the desktop.
        #

        setout_response = complete_move(
            desktop_client,
            setout_id,
        )

        assert setout_response.status_code == 200
        assert setout_response.json()["completed"] is True
        assert (
            setout_response.json()["car_move_id"]
            == setout_id
        )

        #
        # Verify the database lifecycle after SETOUT.
        #

        with test_database.SessionLocal() as session:
            pickup = session.get(
                CarMove,
                pickup_id,
            )

            setout = session.get(
                CarMove,
                setout_id,
            )

            waybill = session.get(
                Waybill,
                record_ids["waybill_id"],
            )

            assert pickup.status == "COMPLETED"
            assert setout.status == "COMPLETED"
            assert waybill.status == "COMPLETED"

        #
        # Simulate the iPad requesting fresh Train Work.
        # With both instructions completed, there should
        # be no active switch-list work remaining.
        #

        ipad_response = ipad_client.get(
            url
        )

        assert ipad_response.status_code == 200
        assert ipad_response.json() == []


def test_companion_rejects_setout_before_pickup(
    test_database,
    monkeypatch,
):
    """
    The companion cannot SETOUT a car that has not been picked up.

    The browser must use the same railroad operating rules as
    the desktop application.
    """

    record_ids = seed_switch_list(
        test_database
    )

    configure_test_database(
        monkeypatch,
        test_database,
    )

    with TestClient(server.app) as client:
        pair_client(client)

        response = complete_move(
            client,
            record_ids["setout_id"],
        )

    assert response.status_code == 409

    with test_database.SessionLocal() as session:
        pickup = session.get(
            CarMove,
            record_ids["pickup_id"],
        )

        setout = session.get(
            CarMove,
            record_ids["setout_id"],
        )

        waybill = session.get(
            Waybill,
            record_ids["waybill_id"],
        )

        assert pickup.status == "PENDING"
        assert setout.status == "PENDING"
        assert waybill.status == "ACTIVE"