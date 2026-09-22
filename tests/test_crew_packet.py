from copy import deepcopy

import pytest
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter

from modelrailroadops.models.operations_session_train import OperationsSessionTrain
from modelrailroadops.services.crew_packet_service import CrewPacketService
from modelrailroadops.services.switch_list_move_service import SwitchListMoveService
from modelrailroadops.ui.operations.crew_packet_dialog import packet_html, make_printer, CrewPacketDialog, export_pdf
from test_operations_session_lifecycle import seed_general_track_waybill


def sample_packet():
    """Fictional print specimen; never read a user's railroad database."""
    moves = []
    for index in range(2):
        moves.append({"car_move_id": index + 1, "waybill_id": 1,
                      "move_type": "PICKUP" if index == 0 else "SETOUT",
                      "route_sequence": index + 1, "move_status": "PENDING",
                      "car": "DEMO 1001", "car_type": "Boxcar", "length": 50,
                      "instruction_location": "Example Yard - Departure" if index == 0 else "Example Lumber - Receiving - Spot 1",
                      "origin": "Example Yard - Departure", "destination": "Example Lumber - Receiving - Spot 1",
                      "current_location": "Example Yard - Departure", "notes": "Handle with care.", "move_notes": ""})
    return {"summary": {"name": "DEMONSTRATION ONLY - Morning Turn", "id": 1, "date": "2026-09-21",
                        "generated_at": "2026-09-21 08:00", "status": "PLANNED", "pickups": 0, "setouts": 0,
                        "pending": moves, "unfinished_waybills": [1], "aboard": []},
            "trains": [{"id": 1, "name": "L101 - Example Turn", "assigned": True,
                        "locomotives": [(1, "DEMO 10", "GP38")], "passenger_cars": [],
                        "route": [(1, "Example Yard", "Departure", "-", "08:00"),
                                  (2, "Example Lumber", "Receiving", "08:30", "08:45")], "moves": moves}]}


def test_packet_reads_session_without_changing_it(test_database):
    ids = seed_general_track_waybill(test_database)
    with test_database.SessionLocal() as db:
        db.add(OperationsSessionTrain(operations_session_id=ids["operations_session_id"], train_id=ids["train_id"]))
        db.commit()
    packet = CrewPacketService.get_packet(ids["operations_session_id"])
    assert packet["summary"]["status"] == "PLANNED"
    assert len(packet["trains"]) == 1
    train = packet["trains"][0]
    assert train["assigned"]
    assert [row["car_move_id"] for row in train["moves"]] == [ids["pickup_id"], ids["setout_id"]]
    assert "Eastbound" in train["moves"][0]["instruction_location"]
    assert "Arrival" in train["moves"][1]["instruction_location"]
    assert SwitchListMoveService.complete_move(ids["pickup_id"])[0]
    refreshed = CrewPacketService.get_packet(ids["operations_session_id"])
    assert "COMPLETED - reference only" in packet_html(refreshed)
    assert packet["summary"]["status"] == "PLANNED"  # detached printable snapshot


def test_unassigned_train_is_not_silently_omitted(test_database):
    ids = seed_general_track_waybill(test_database)
    packet = CrewPacketService.get_packet(ids["operations_session_id"])
    assert not packet["trains"][0]["assigned"]
    assert "Warning: moves reference" in packet_html(packet)
    with pytest.raises(ValueError):
        CrewPacketService.get_packet(99999)


def test_packet_escapes_data_and_keeps_work_order():
    packet = sample_packet()
    packet["trains"][0]["name"] = '<script> & "Train"'
    html = packet_html(packet)
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert html.index("Move #1") < html.index("Move #2")
    assert "Paper checkmarks do not update" in html
    assert "Return Car to Pickup Location" in html
    assert "SESSION CLOSEOUT" in html


def test_empty_and_passenger_packet():
    packet = sample_packet()
    packet["trains"][0]["moves"] = []
    packet["trains"][0]["passenger_cars"] = [(1, "DEMO 50", "Coach")]
    html = packet_html(packet)
    assert "DEMO 50" in html and "No generated freight instructions" in html
    packet["trains"] = []
    assert "NO TRAINS ASSIGNED" in packet_html(packet)


def test_pdf_export(qapp, tmp_path):
    printer = make_printer()
    printer.setOutputFormat(QPrinter.PdfFormat)
    path = tmp_path / "crew-packet.pdf"
    printer.setOutputFileName(str(path))
    document = QTextDocument()
    document.setHtml(packet_html(sample_packet()))
    document.print_(printer)
    assert path.read_bytes().startswith(b"%PDF-")
    assert path.stat().st_size > 10000


def test_dialog_refresh_and_cancel_save(qapp, monkeypatch):
    import modelrailroadops.ui.operations.crew_packet_dialog as ui
    packet = sample_packet()
    monkeypatch.setattr(CrewPacketService, "get_packet", lambda sid: deepcopy(packet))
    dialog = CrewPacketDialog(1)
    try:
        assert "CREW OPERATING CHECKLIST" in dialog.document.toPlainText()
        packet["summary"]["status"] = "ACTIVE"
        dialog.refresh()
        assert "ACTIVE" in dialog.document.toPlainText()
        monkeypatch.setattr(ui.QFileDialog, "getSaveFileName", lambda *args: ("", ""))
        dialog.save_pdf()
    finally:
        dialog.close()


def test_failed_export_preserves_existing_file(qapp, tmp_path):
    path = tmp_path / "existing.pdf"
    path.write_bytes(b"original")
    class BrokenDocument:
        def print_(self, printer):
            raise OSError("test print failure")
    with pytest.raises(OSError, match="test print failure"):
        export_pdf(BrokenDocument(), path)
    assert path.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_export(qapp, tmp_path):
    document = QTextDocument()
    document.setHtml(packet_html(sample_packet()))
    path = tmp_path / "packet.pdf"
    export_pdf(document, path)
    assert path.read_bytes().startswith(b"%PDF-")


def test_many_moves_and_multiple_trains():
    packet = sample_packet()
    rows = packet["trains"][0]["moves"]
    original = deepcopy(rows[0])
    for index in range(3, 13):
        row = deepcopy(original)
        row.update(car_move_id=index, route_sequence=index, car=f"DEMO {index}",
                   notes="Long operating instructions " * 20)
        rows.append(row)
    second = deepcopy(packet["trains"][0])
    second.update(id=2, name="P202 - Passenger", moves=[])
    packet["trains"].append(second)
    html = packet_html(packet)
    assert html.count("FREIGHT WORK CHECKLIST") == 3
    assert "P202 - Passenger" in html
    assert all(f"Move #{index} |" in html for index in range(1, 13))


def test_failed_refresh_clears_old_packet(qapp, monkeypatch):
    import modelrailroadops.ui.operations.crew_packet_dialog as ui
    monkeypatch.setattr(CrewPacketService, "get_packet", lambda sid: sample_packet())
    dialog = CrewPacketDialog(1)
    def fail(sid):
        raise ValueError("Session unavailable")
    monkeypatch.setattr(CrewPacketService, "get_packet", fail)
    monkeypatch.setattr(ui.QMessageBox, "warning", lambda *args: None)
    dialog.refresh()
    assert dialog.packet is None and dialog.document.isEmpty()
    dialog.close()
