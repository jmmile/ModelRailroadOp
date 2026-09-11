from types import SimpleNamespace

from modelrailroadops.ui.operations.operations_sessions_widget import (
    OperationsSessionsWidget,
)


class ControlStub:
    def __init__(self):
        self.enabled = None
        self.visible = None

    def setEnabled(self, enabled):
        self.enabled = enabled

    def setVisible(self, visible):
        self.visible = visible


def passenger_controls_for(status):
    session = (
        SimpleNamespace(status=status)
        if status is not None
        else None
    )
    controls = SimpleNamespace(
        add_passenger_car_button=ControlStub(),
        remove_passenger_car_button=ControlStub(),
        move_passenger_car_up_button=ControlStub(),
        move_passenger_car_down_button=ControlStub(),
        passenger_consist_status_label=ControlStub(),
        get_selected_session_without_message=lambda: session,
    )

    OperationsSessionsWidget.update_passenger_consist_read_only_state(
        controls
    )

    return controls


def test_completed_passenger_session_retains_consist_for_printing():
    controls = passenger_controls_for("COMPLETED")

    assert (
        OperationsSessionsWidget.COMPLETED_PASSENGER_MESSAGE
        == "Completed — retained for printing"
    )
    assert controls.add_passenger_car_button.enabled is False
    assert controls.remove_passenger_car_button.enabled is False
    assert controls.move_passenger_car_up_button.enabled is False
    assert controls.move_passenger_car_down_button.enabled is False
    assert controls.passenger_consist_status_label.visible is True


def test_active_passenger_session_keeps_consist_controls_editable():
    controls = passenger_controls_for("IN_PROGRESS")

    assert controls.add_passenger_car_button.enabled is True
    assert controls.remove_passenger_car_button.enabled is True
    assert controls.move_passenger_car_up_button.enabled is True
    assert controls.move_passenger_car_down_button.enabled is True
    assert controls.passenger_consist_status_label.visible is False


def test_passenger_operator_sheet_preview_has_no_completed_session_guard(
    monkeypatch,
):
    class PreviewHarness:
        get_selected_session_without_message = lambda self: SimpleNamespace(
            status="COMPLETED",
            name="Completed Session",
            session_date=None,
        )
        get_selected_passenger_train_assignment_id_without_message = (
            lambda self: 17
        )
        get_selected_passenger_train_id = lambda self: 23
        get_train = lambda self, _train_id: SimpleNamespace(
            train_type="Passenger"
        )

    # Reaching dialog construction demonstrates that COMPLETED does not block
    # preview. Avoid constructing a real dialog by replacing the module global.
    calls = []

    class PreviewDialogStub:
        def __init__(self, *args):
            calls.append(args)

        def exec(self):
            calls.append("exec")

    monkeypatch.setitem(
        OperationsSessionsWidget.preview_passenger_operator_sheet.__globals__,
        "PassengerOperatorSheetPreviewDialog",
        PreviewDialogStub,
    )

    OperationsSessionsWidget.preview_passenger_operator_sheet(
        PreviewHarness()
    )

    assert calls[-1] == "exec"
    assert calls[0][0] == 17
