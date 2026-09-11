from test_switch_list_output import seed_switch_list

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt

from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.ui.widgets.car_history_widget import CarHistoryWidget
from modelrailroadops.ui.switch_list.switch_list_preview_dialog import (
    SwitchListPreviewDialog,
)
from modelrailroadops.ui.switch_list.completed_session_report_dialog import (
    CompletedSessionReportDialog,
)
from modelrailroadops.ui.switch_list.switch_list_widget import SwitchListWidget
from modelrailroadops.services.switch_list_move_service import (
    SwitchListMoveService,
)
from modelrailroadops.services.switch_list_service import (
    SwitchListService,
)


def test_active_session_displays_car_on_selected_train(
    qapp,
    test_database,
    monkeypatch,
):
    record_ids = seed_switch_list(test_database)

    completed, message = SwitchListMoveService.complete_move(
        record_ids["pickup_id"]
    )
    assert completed, message

    monkeypatch.setattr(
        "modelrailroadops.ui.switch_list.switch_list_widget.SessionLocal",
        test_database.SessionLocal,
    )
    monkeypatch.setattr(
        "modelrailroadops.ui.widgets.car_history_widget.SessionLocal",
        test_database.SessionLocal,
    )
    monkeypatch.setattr(
        "modelrailroadops.ui.models.car_history_table_model.SessionLocal",
        test_database.SessionLocal,
    )

    widget = SwitchListWidget()
    session_index = widget.session_combo.findData(
        record_ids["operations_session_id"]
    )
    widget.session_combo.setCurrentIndex(session_index)

    assert widget.on_train_label.text() == "Cars On Train: 1"
    assert widget.on_train_model.rowCount() == 1
    assert (
        widget.on_train_model.rows[0]["car"]
        == "GN 33103"
    )
    assert widget.on_train_model.rows[0]["can_setout"] is True

    train_index = widget.train_combo.findData(
        record_ids["train_id"]
    )
    widget.train_combo.setCurrentIndex(train_index)

    assert widget.on_train_label.text() == "Cars On Train: 1"
    assert widget.on_train_model.rowCount() == 1
    assert widget.progress_bar.value() == 50
    assert widget.progress_bar.format() == "Session Progress: 50%"
    assert (
        widget.progress_summary_label.text()
        == (
            "Pending Pickups: 0 | Cars On Train: 1 | "
            "Pending Set-outs: 1 | Completed: 1 of 2"
        )
    )

    onboard_filter = widget.move_filter_combo.findData("ON_TRAIN")
    widget.move_filter_combo.setCurrentIndex(onboard_filter)
    assert widget.model.rowCount() == 1
    assert widget.model.rows[0]["move_type"] == "SETOUT"

    completed_filter = widget.move_filter_combo.findData("COMPLETED")
    widget.move_filter_combo.setCurrentIndex(completed_filter)
    assert widget.model.rowCount() == 1
    assert widget.model.rows[0]["move_type"] == "PICKUP"
    assert widget.model.data(
        widget.model.index(0, 0),
        Qt.BackgroundRole,
    ) is not None

    all_filter = widget.move_filter_combo.findData("ALL")
    widget.move_filter_combo.setCurrentIndex(all_filter)
    assert widget.model.rowCount() == 2
    assert widget.on_train_model.data(
        widget.on_train_model.index(0, 0),
        Qt.BackgroundRole,
    ) is not None

    widget.on_train_table.selectRow(0)
    assert widget.return_to_pickup_button.isEnabled()

    history_widget = CarHistoryWidget()
    car_id = widget.on_train_model.rows[0]["car_id"]
    car_index = history_widget.car_combo.findData(car_id)
    history_widget.car_combo.setCurrentIndex(car_index)
    assert history_widget.model.rowCount() == 1

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.Yes,
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: QMessageBox.Ok,
    )

    widget.return_selected_car_to_pickup()

    assert widget.on_train_label.text() == "Cars On Train: 0"
    assert widget.on_train_model.rowCount() == 0
    assert not widget.return_to_pickup_button.isEnabled()

    history_widget.refresh()
    assert history_widget.car_combo.currentData() == car_id
    assert history_widget.model.rowCount() == 2
    return_row = next(
        row
        for row in history_widget.model.rows
        if row["movement_type"] == "RETURN"
    )
    assert return_row["from_location"] == "On Train: M225 - Weston Inbound"
    assert (
        return_row["to_location"]
        == "Staging Yard - Eastbound"
    )

    history_widget.close()
    widget.close()


def complete_seeded_session(test_database, record_ids):
    with test_database.SessionLocal() as session:
        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )
        waybill = session.get(
            Waybill,
            record_ids["waybill_id"],
        )

        operations_session.status = "COMPLETED"
        waybill.status = "COMPLETED"
        session.commit()


def test_completed_session_populates_train_and_enables_retained_preview(
    qapp,
    test_database,
    monkeypatch,
):
    record_ids = seed_switch_list(test_database)
    complete_seeded_session(test_database, record_ids)

    monkeypatch.setattr(
        "modelrailroadops.ui.switch_list.switch_list_widget.SessionLocal",
        test_database.SessionLocal,
    )

    widget = SwitchListWidget()
    session_index = widget.session_combo.findData(
        record_ids["operations_session_id"]
    )
    widget.session_combo.setCurrentIndex(session_index)

    train_index = widget.train_combo.findData(
        record_ids["train_id"]
    )

    assert session_index >= 0
    assert widget.train_combo.isEnabled()
    assert train_index >= 0
    assert widget.preview_button.isEnabled()
    assert widget.completed_report_button.isEnabled()
    assert widget.check_session_data_button.isEnabled()
    assert widget.model.rowCount() == 2

    dialog = SwitchListPreviewDialog(
        record_ids["operations_session_id"],
        widget.session_combo.currentText(),
        "2026-09-07",
    )

    assert dialog.print_button.isEnabled()
    assert "Total Moves: 2" in dialog.preview_text.toPlainText()

    dialog.close()
    widget.close()


def test_legacy_completed_session_check_and_cleanup(
    test_database,
):
    record_ids = seed_switch_list(test_database)
    complete_seeded_session(test_database, record_ids)

    result = SwitchListService.check_session_consistency(
        record_ids["operations_session_id"]
    )

    assert result["pending_move_count"] == 2
    assert result["can_remove_stale_pending_moves"] is True
    assert any("still PENDING" in issue for issue in result["issues"])
    assert any("completion timestamp" in issue for issue in result["issues"])

    success, message = SwitchListService.remove_stale_pending_moves(
        record_ids["operations_session_id"]
    )
    assert success, message

    with test_database.SessionLocal() as session:
        moves = session.query(CarMove).filter_by(
            operations_session_id=record_ids["operations_session_id"]
        ).all()
        waybill = session.get(Waybill, record_ids["waybill_id"])

        assert moves == []
        assert waybill.status == "COMPLETED"


def test_completed_session_report_summarizes_moves_and_final_location(
    qapp,
    test_database,
):
    record_ids = seed_switch_list(test_database)

    with test_database.SessionLocal() as session:
        operations_session = session.get(
            OperationsSession,
            record_ids["operations_session_id"],
        )
        waybill = session.get(Waybill, record_ids["waybill_id"])
        pickup = session.get(CarMove, record_ids["pickup_id"])
        setout = session.get(CarMove, record_ids["setout_id"])

        operations_session.status = "COMPLETED"
        waybill.status = "COMPLETED"
        pickup.status = "COMPLETED"
        setout.status = "COMPLETED"
        session.commit()

    dialog = CompletedSessionReportDialog(
        record_ids["operations_session_id"],
    )
    report_text = dialog.preview_text.toPlainText()

    assert dialog.report["total_moves"] == 2
    assert dialog.report["completed_count"] == 2
    assert dialog.report["pending_count"] == 0
    assert dialog.report["pickup_count"] == 1
    assert dialog.report["setout_count"] == 1
    assert dialog.report["on_train_count"] == 0
    assert "COMPLETED SESSION REPORT" in report_text
    assert "GN 33103" in report_text
    assert "Staging Yard - Eastbound" in report_text

    dialog.close()
