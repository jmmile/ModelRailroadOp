from datetime import UTC, datetime

import pytest
from PySide6.QtCore import Qt

from modelrailroadops.models.car import Car
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.waybill_print_services import WaybillPrintService
from modelrailroadops.ui.switch_list.switch_list_preview_dialog import (
    SwitchListPreviewDialog,
)
from modelrailroadops.ui.waybills.waybill_form import WaybillFormRenderer
from modelrailroadops.ui.waybills.waybill_preview_dialog import WaybillPreviewDialog
from modelrailroadops.ui.waybills.waybill_table_model import WaybillTableModel


def build_waybill(*, load_state="LOADED", cargo_weight_lbs=81_000, number="8181"):
    car = Car(
        id=int(number),
        reporting_mark="RPDX",
        number=number,
        owner="RPDX",
        car_type="Tank Car",
        length=50,
        empty_weight_lbs=40_400,
        load_limit_lbs=81_000,
        status="AVAILABLE",
        location="Staging Yard",
    )
    return Waybill(
        id=int(number),
        car=car,
        car_id=car.id,
        origin_location="Staging Yard",
        load_state=load_state,
        commodity="Gasoline" if load_state == "LOADED" else None,
        cargo_weight_lbs=cargo_weight_lbs,
        status="ACTIVE",
        created_at=datetime(2026, 9, 2, 10, 30, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    ("load_state", "cargo_weight_lbs", "gross_weight", "tonnage", "display"),
    (
        ("LOADED", 81_000, 121_400, 60.7, "121,400 lb\n60.7 short tons"),
        ("EMPTY", 0, 40_400, 20.2, "40,400 lb\n20.2 short tons"),
    ),
)
def test_waybill_weight_calculation_and_print_text(
    load_state,
    cargo_weight_lbs,
    gross_weight,
    tonnage,
    display,
):
    waybill = build_waybill(
        load_state=load_state,
        cargo_weight_lbs=cargo_weight_lbs,
    )

    assert waybill.gross_weight_lbs == gross_weight
    assert waybill.tonnage == pytest.approx(tonnage)
    assert WaybillFormRenderer._weight_text(waybill) == display


def test_waybill_table_displays_weights_and_tonnage(qapp, monkeypatch):
    monkeypatch.setattr(WaybillTableModel, "refresh", lambda self: None)
    model = WaybillTableModel()
    model.set_waybills([build_waybill()])

    assert model.data(model.index(0, 1)) == "RPDX 8181"
    assert model.data(model.index(0, 2)) == "Tank Car"
    assert model.data(model.index(0, 3)) == "40,400"
    assert model.data(model.index(0, 4)) == "81,000"
    assert model.data(model.index(0, 5)) == "Loaded"
    assert model.data(model.index(0, 6)) == "Gasoline"
    assert model.data(model.index(0, 7)) == "121,400"
    assert model.data(model.index(0, 8)) == "60.7"


def test_waybill_table_sorts_tonnage_numerically(qapp, monkeypatch):
    monkeypatch.setattr(WaybillTableModel, "refresh", lambda self: None)
    model = WaybillTableModel()
    loaded = build_waybill(number="8181")
    empty = build_waybill(
        load_state="EMPTY",
        cargo_weight_lbs=0,
        number="8182",
    )
    model.set_waybills([loaded, empty])

    model.sort(8, Qt.AscendingOrder)

    assert [waybill.car.number for waybill in model.waybills] == ["8182", "8181"]


def test_waybill_preview_renders_expected_form_size(qapp):
    dialog = WaybillPreviewDialog(build_waybill())
    pixmap = dialog.preview_label.pixmap()

    assert pixmap is not None
    assert pixmap.width() == 600
    assert pixmap.height() == 640
    dialog.close()


def test_switch_list_preview_builds_printable_escaped_html(qapp, monkeypatch):
    row = {
        "train": "M225 - Weston & Inbound",
        "pickup_sequence": 1,
        "setout_sequence": 3,
        "car": "GN <33103>",
        "car_type": "Gondola",
        "length": 45,
        "origin": "Staging Yard - Eastbound",
        "origin_location": "Staging Yard",
        "origin_industry": "Staging Yard",
        "origin_track": "Eastbound",
        "origin_spot": "1",
        "destination": "Weston - Arrival",
        "destination_industry": "Weston",
        "destination_track": "Arrival",
        "destination_spot": "2",
    }
    monkeypatch.setattr(
        "modelrailroadops.ui.switch_list.switch_list_preview_dialog."
        "SwitchListService.get_switch_list_rows",
        lambda _session_id: [row],
    )
    monkeypatch.setattr(
        "modelrailroadops.ui.switch_list.switch_list_preview_dialog."
        "SwitchListService.get_pickup_rows",
        lambda _session_id: [row],
    )
    monkeypatch.setattr(
        "modelrailroadops.ui.switch_list.switch_list_preview_dialog."
        "SwitchListService.get_setout_rows",
        lambda _session_id: [row],
    )

    dialog = SwitchListPreviewDialog(
        1,
        "Session <One>",
        "2026-09-02",
    )
    html = dialog.preview_text.toHtml()
    plain_text = dialog.preview_text.toPlainText()

    assert "Session &lt;One&gt;" in html
    assert "GN &lt;33103&gt;" in html
    assert "M225 - Weston &amp; Inbound" in html
    assert "Total Moves: 1" in plain_text
    assert "Stop 1" in plain_text
    assert "Stop 3" in plain_text
    dialog.close()


def test_print_dimensions_convert_inches_to_device_units():
    assert WaybillPrintService.inches_to_printer_units(3.75, 300) == 1125
    assert WaybillPrintService.inches_to_printer_units(4.00, 300) == 1200


def test_car_image_lookup_accepts_case_insensitive_png_name(tmp_path, monkeypatch):
    image_directory = tmp_path / "data" / "Car_Images"
    image_directory.mkdir(parents=True)
    expected_path = image_directory / "rpdx_8181.PNG"
    expected_path.write_bytes(b"test image placeholder")
    monkeypatch.setattr(
        WaybillFormRenderer,
        "_project_root",
        staticmethod(lambda: tmp_path),
    )

    result = WaybillFormRenderer.find_car_image_path("RPDX", "8181")

    assert result == expected_path
