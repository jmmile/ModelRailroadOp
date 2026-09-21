"""Selection previews use temporary equipment records and images only."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QColor

from modelrailroadops import paths
from modelrailroadops.services import locomotive_service, passenger_car_service
from modelrailroadops.services import locomotive_image_service, passenger_image_service
from modelrailroadops.ui.locomotives.locomotives_widget import LocomotivesWidget
from modelrailroadops.ui.passenger_cars.passenger_cars_widget import PassengerCarsWidget


@pytest.fixture(params=["locomotive", "passenger"])
def roster(request, qapp, test_database, tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "DATA_DIRECTORY", tmp_path)
    if request.param == "locomotive":
        module, service, images, widget_type = (
            locomotive_service, locomotive_service.LocomotiveService,
            locomotive_image_service, LocomotivesWidget,
        )
    else:
        module, service, images, widget_type = (
            passenger_car_service, passenger_car_service.PassengerCarService,
            passenger_image_service, PassengerCarsWidget,
        )
    monkeypatch.setattr(module, "SessionLocal", test_database.SessionLocal)
    image = QImage(600, 200, QImage.Format.Format_RGB32)
    image.fill(QColor("red"))
    source = tmp_path / "source.png"
    assert image.save(str(source))
    pictured = service.add("AA", "1", picture=images.import_picture(source))
    empty = service.add("ZZ", "2")
    widget = widget_type()
    widget.resize(950, 650)
    widget.show()
    qapp.processEvents()
    yield widget, service, images, pictured, empty, qapp
    widget.close()
    widget.deleteLater()
    qapp.processEvents()


def select(widget, mark):
    for row in range(widget.proxy.rowCount()):
        if widget.proxy.index(row, 0).data() == mark:
            widget.table.selectRow(row)
            return
    raise AssertionError(f"Missing row: {mark}")


def test_selection_missing_picture_and_clear(roster):
    widget, _, _, _, _, _ = roster
    preview = widget.picture_preview
    assert preview.picture_label.pixmap().isNull()
    assert "Select a" in preview.picture_label.text()
    select(widget, "AA")
    assert not preview.picture_label.pixmap().isNull()
    assert preview.equipment_label.text().startswith("AA 1")
    select(widget, "ZZ")
    assert preview.picture_label.pixmap().isNull()
    assert "No picture available for ZZ 2" in preview.picture_label.text()
    widget.table.clearSelection()
    assert "Select a" in preview.picture_label.text()
    assert preview.picture_label.toolTip() == ""


def test_sort_filter_and_refresh_follow_identity(roster):
    widget, _, _, _, _, app = roster
    select(widget, "AA")
    widget.proxy.sort(0, Qt.SortOrder.DescendingOrder)
    app.processEvents()
    assert widget.picture_preview.equipment_label.text().startswith("AA 1")
    widget.refresh()
    assert widget.picture_preview.equipment_label.text().startswith("AA 1")
    assert not widget.picture_preview.picture_label.pixmap().isNull()
    widget.search_box.setText("ZZ")
    app.processEvents()
    assert widget.picture_preview.picture_label.pixmap().isNull()
    assert "AA 1" not in widget.picture_preview.equipment_label.text()
    select(widget, "ZZ")
    assert "ZZ 2" in widget.picture_preview.picture_label.text()


def test_replaced_removed_and_deleted_picture_refresh(roster):
    widget, service, images, pictured, _, _ = roster
    select(widget, "AA")
    path = images.find_image("AA", "1")
    image = QImage(600, 200, QImage.Format.Format_RGB32)
    image.fill(QColor("blue"))
    assert image.save(str(path))
    widget.refresh()
    assert widget.picture_preview.picture_label.original.toImage().pixelColor(10, 10) == QColor("blue")
    service.update(pictured.id, "AA", "1", remove_picture=True)
    widget.refresh()
    assert "No picture" in widget.picture_preview.picture_label.text()
    service.delete(pictured.id)
    widget.refresh()
    assert "Select a" in widget.picture_preview.picture_label.text()


def test_corrupt_or_ambiguous_picture_is_nonfatal(roster):
    widget, _, images, _, _, _ = roster
    path = images.find_image("AA", "1")
    path.write_bytes(b"invalid image")
    select(widget, "AA")
    assert "could not be loaded" in widget.picture_preview.picture_label.text()
    path.with_suffix(".jpg").write_bytes(b"duplicate")
    widget.refresh()
    assert "could not be loaded" in widget.picture_preview.picture_label.text()
    assert "Multiple pictures" in widget.picture_preview.picture_label.toolTip()


def test_resize_preserves_aspect_ratio_and_table_space(roster):
    widget, _, _, _, _, app = roster
    select(widget, "AA")
    widget.resize(1200, 800)
    app.processEvents()
    label = widget.picture_preview.picture_label
    pixmap = label.pixmap()
    assert abs(pixmap.width() / pixmap.height() - 3) < 0.02
    assert pixmap.width() <= label.width() and pixmap.height() <= label.height()
    assert label.height() == 190
    assert widget.table.height() > label.height()
