from datetime import time
from types import SimpleNamespace

from modelrailroadops.ui.operations.operations_sessions_widget import (
    OperationsSessionsWidget,
)


def test_passenger_route_timing_prefers_train_schedule():
    train = SimpleNamespace(
        scheduled_departure=time(8, 15),
        scheduled_arrival=time(10, 45),
    )
    routes = [
        SimpleNamespace(
            arrival_time=None,
            departure_time=time(8, 30),
        ),
        SimpleNamespace(
            arrival_time=time(10, 30),
            departure_time=None,
        ),
    ]

    assert (
        OperationsSessionsWidget.format_passenger_route_timing(
            train,
            routes,
        )
        == "8:15 AM → 10:45 AM"
    )


def test_passenger_route_timing_falls_back_to_route_endpoints():
    train = SimpleNamespace(
        scheduled_departure=None,
        scheduled_arrival=None,
    )
    routes = [
        SimpleNamespace(
            arrival_time=None,
            departure_time=time(9, 5),
        ),
        SimpleNamespace(
            arrival_time=time(11, 20),
            departure_time=None,
        ),
    ]

    assert (
        OperationsSessionsWidget.format_passenger_route_timing(
            train,
            routes,
        )
        == "9:05 AM → 11:20 AM"
    )


def test_passenger_route_timing_handles_partial_and_missing_times():
    route_without_times = SimpleNamespace(
        arrival_time=None,
        departure_time=None,
    )

    assert (
        OperationsSessionsWidget.format_passenger_route_timing(
            SimpleNamespace(
                scheduled_departure=time(14, 0),
                scheduled_arrival=None,
            ),
            [],
        )
        == "Departs 2:00 PM"
    )
    assert (
        OperationsSessionsWidget.format_passenger_route_timing(
            SimpleNamespace(
                scheduled_departure=None,
                scheduled_arrival=None,
            ),
            [route_without_times],
        )
        == "—"
    )


def test_passenger_route_stops_lists_every_station_with_times():
    routes = [
        SimpleNamespace(
            location="Staging Yard",
            operating_location=None,
            arrival_time=None,
            departure_time=time(8, 0),
        ),
        SimpleNamespace(
            location="Pine Bluff",
            operating_location=SimpleNamespace(
                name="Pine Bluff Station"
            ),
            arrival_time=time(8, 35),
            departure_time=time(8, 40),
        ),
        SimpleNamespace(
            location="Mesa Station",
            operating_location=None,
            arrival_time=time(9, 15),
            departure_time=None,
        ),
    ]

    assert (
        OperationsSessionsWidget.format_passenger_route_stops(
            routes
        )
        == (
            "Staging Yard (Dep 8:00 AM) → "
            "Pine Bluff Station (Arr 8:35 AM, Dep 8:40 AM) → "
            "Mesa Station (Arr 9:15 AM)"
        )
    )


def test_passenger_route_stops_handles_missing_route():
    assert (
        OperationsSessionsWidget.format_passenger_route_stops(
            []
        )
        == "—"
    )
