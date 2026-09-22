from datetime import date

import pytest
from PySide6.QtWidgets import QApplication

from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.services.operations_session_service import OperationsSessionService
from modelrailroadops.services.switch_list_move_service import SwitchListMoveService
from modelrailroadops.ui.operations.session_summary_dialog import SessionSummaryDialog, summary_text
from test_operations_session_lifecycle import seed_general_track_waybill


def test_summary_cycle_read_only_and_isolated(test_database):
    ids = seed_general_track_waybill(test_database)
    with test_database.SessionLocal() as db:
        other = OperationsSession(name="Unrelated", session_date=date.today(), status="PLANNED")
        db.add(other)
        db.commit()
        other_id = other.id
    sid = ids["operations_session_id"]
    before = OperationsSessionService.end_summary(sid)
    assert before["status"] == "PLANNED"
    assert len(before["pending"]) == 2
    assert before["pickups"] == before["setouts"] == 0
    assert not before["ready"] and not before["aboard"]
    assert {r["id"] for r in before["moves"]} == {ids["pickup_id"], ids["setout_id"]}
    assert SwitchListMoveService.complete_move(ids["pickup_id"])[0]
    during = OperationsSessionService.end_summary(sid)
    assert during["status"] == "ACTIVE"
    assert during["pickups"] == 1 and during["setouts"] == 0
    assert len(during["pending"]) == len(during["aboard"]) == 1
    assert not during["ready"]
    assert SwitchListMoveService.complete_move(ids["setout_id"])[0]
    ready = OperationsSessionService.end_summary(sid)
    assert ready["ready"] and ready["setouts"] == 1
    assert not ready["pending"] and not ready["aboard"]
    assert OperationsSessionService.get_by_id(sid).status == "ACTIVE"
    assert OperationsSessionService.complete(sid)[0]
    finished = OperationsSessionService.end_summary(sid)
    assert finished["status"] == "COMPLETED" and not finished["ready"]
    assert finished["pickups"] == finished["setouts"] == 1
    assert OperationsSessionService.get_by_id(other_id).status == "PLANNED"


@pytest.mark.parametrize("status", ["PLANNED", "ACTIVE", "COMPLETED", "CANCELLED"])
def test_empty_summary(test_database, status):
    with test_database.SessionLocal() as db:
        row = OperationsSession(name="Empty", session_date=date.today(), status=status)
        db.add(row)
        db.commit()
        sid = row.id
    result = OperationsSessionService.end_summary(sid)
    assert not result["moves"] and not result["aboard"]
    assert result["ready"] == (status == "ACTIVE")
    assert "No generated freight moves" in summary_text(result)
    with pytest.raises(ValueError):
        OperationsSessionService.end_summary(999999)


def test_checklist_refresh_and_completion_gate(test_database):
    app = QApplication.instance() or QApplication([])
    ids = seed_general_track_waybill(test_database)
    dialog = SessionSummaryDialog(ids["operations_session_id"], allow_complete=True)
    try:
        for check in dialog.checks:
            check.setChecked(True)
        assert not dialog.complete_button.isEnabled()
        assert SwitchListMoveService.complete_move(ids["pickup_id"])[0]
        assert SwitchListMoveService.complete_move(ids["setout_id"])[0]
        dialog.refresh()
        assert not any(c.isChecked() for c in dialog.checks)
        for check in dialog.checks:
            check.setChecked(True)
        assert dialog.complete_button.isEnabled()
        dialog.refresh()
        assert not dialog.complete_button.isEnabled()
        assert OperationsSessionService.get_by_id(ids["operations_session_id"]).status == "ACTIVE"
    finally:
        dialog.close()


def test_missing_session_fails_closed(test_database):
    app = QApplication.instance() or QApplication([])
    dialog = SessionSummaryDialog(999999, allow_complete=True)
    assert "Unable to load" in dialog.report.toPlainText()
    assert not dialog.complete_button.isEnabled()
    dialog.close()
