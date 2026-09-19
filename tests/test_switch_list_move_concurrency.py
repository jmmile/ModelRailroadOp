"""Concurrency tests for switch-list Car Move completion."""

import threading

from sqlalchemy import select

from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.switch_list_move_service import (
    SwitchListMoveService,
)
from test_switch_list_output import seed_switch_list


def test_completed_pickup_cannot_be_completed_twice(
    test_database,
):
    """
    A sequential duplicate completion is rejected.

    This establishes the expected result before testing two
    competing completion requests.
    """

    record_ids = seed_switch_list(
        test_database
    )

    first_success, first_message = (
        SwitchListMoveService.complete_move(
            record_ids["pickup_id"]
        )
    )

    second_success, second_message = (
        SwitchListMoveService.complete_move(
            record_ids["pickup_id"]
        )
    )

    assert first_success, first_message
    assert second_success is False
    assert "already been completed" in second_message.lower()

    with test_database.SessionLocal() as session:
        pickup = session.get(
            CarMove,
            record_ids["pickup_id"],
        )
        waybill = session.get(
            Waybill,
            record_ids["waybill_id"],
        )

        assert pickup.status == "COMPLETED"
        assert waybill.status == "IN_PROGRESS"


def test_competing_pickup_completions_only_succeed_once(
    test_database,
):
    """
    Two competing requests cannot both complete one PICKUP.

    BEGIN IMMEDIATE must serialize the transactions so that the
    second transaction sees the committed COMPLETED status rather
    than independently completing the same pending instruction.
    """

    record_ids = seed_switch_list(
        test_database
    )

    pickup_id = record_ids["pickup_id"]

    barrier = threading.Barrier(2)
    results = []
    errors = []

    def complete_pickup():
        try:
            barrier.wait(
                timeout=5
            )

            result = (
                SwitchListMoveService.complete_move(
                    pickup_id
                )
            )

            results.append(
                result
            )

        except Exception as exc:
            errors.append(
                exc
            )

    first_thread = threading.Thread(
        target=complete_pickup,
    )
    second_thread = threading.Thread(
        target=complete_pickup,
    )

    first_thread.start()
    second_thread.start()

    first_thread.join(
        timeout=10
    )
    second_thread.join(
        timeout=10
    )

    assert not first_thread.is_alive()
    assert not second_thread.is_alive()
    assert errors == []

    assert len(results) == 2

    successful_results = [
        result
        for result in results
        if result[0] is True
    ]

    rejected_results = [
        result
        for result in results
        if result[0] is False
    ]

    assert len(successful_results) == 1
    assert len(rejected_results) == 1

    assert (
        "already been completed"
        in rejected_results[0][1].lower()
    )

    with test_database.SessionLocal() as session:
        pickup = session.get(
            CarMove,
            pickup_id,
        )

        waybill = session.get(
            Waybill,
            record_ids["waybill_id"],
        )

        completed_pickups = (
            session.execute(
                select(CarMove).where(
                    CarMove.id == pickup_id,
                    CarMove.status == "COMPLETED",
                )
            )
            .scalars()
            .all()
        )

        assert pickup.status == "COMPLETED"
        assert waybill.status == "IN_PROGRESS"
        assert len(completed_pickups) == 1