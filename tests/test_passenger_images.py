"""Passenger editor/storage and real-picture backup integration, isolated data only."""

from pathlib import Path
import zipfile

import pytest
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QFileDialog, QMessageBox
from sqlalchemy import event

from modelrailroadops import paths
from modelrailroadops.database import database
from modelrailroadops.services import locomotive_image_service as locomotive_images
from modelrailroadops.services import locomotive_service, passenger_car_service
from modelrailroadops.services import passenger_image_service as images
from modelrailroadops.services.database_backup_service import DatabaseBackupService
from modelrailroadops.services.locomotive_service import LocomotiveService
from modelrailroadops.services.passenger_car_service import (
    PassengerCarService as Service,
)
from modelrailroadops.ui.dialogs.add_passenger_car_dialog import AddPassengerCarDialog


@pytest.fixture
def storage(tmp_path, monkeypatch, test_database):
    monkeypatch.setattr(paths, "DATA_DIRECTORY", tmp_path)
    monkeypatch.setattr(
        passenger_car_service, "SessionLocal", test_database.SessionLocal
    )
    monkeypatch.setattr(locomotive_service, "SessionLocal", test_database.SessionLocal)
    return tmp_path


def photo(root, name="coach.jpg", color="red"):
    file = root / name
    image = QImage(360, 120, QImage.Format.Format_RGB32)
    image.fill(QColor(color))
    assert image.save(str(file))
    return file


def add(root):
    return Service.add(
        "GN",
        "A1",
        name="Test Coach",
        length=85,
        picture=images.import_picture(photo(root)),
    )


def choose(dialog, file, monkeypatch):
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(file), ""))
    dialog.choose_picture()


@pytest.mark.parametrize("extension", ["png", "jpg", "jpeg", "JPG"])
def test_import_save_and_discovery(storage, extension):
    source = photo(storage, "coach." + extension)
    before = source.read_bytes()
    car = Service.add("GN", "A1", picture=images.import_picture(source))
    managed = images.find_image(car.reporting_mark, car.number)
    assert managed == storage / "Passenger_Images" / "P_GN_A1.png"
    assert not QImage(str(managed)).isNull()
    assert source.read_bytes() == before


def test_replace_rename_remove(storage):
    car = add(storage)
    payload = images.import_picture(photo(storage, "blue.png", "blue"))
    Service.update(car.id, "GN", "A1", picture=payload)
    assert images.find_image("GN", "A1").read_bytes() == payload
    Service.update(car.id, "UP", "B 2")
    assert images.find_image("GN", "A1") is None
    assert images.find_image("UP", "B 2").read_bytes() == payload
    Service.update(car.id, "UP", "B 2", remove_picture=True)
    assert images.find_image("UP", "B 2") is None
    assert (storage / "blue.png").exists()


def test_collections_do_not_share_identity(storage):
    car = add(storage)
    payload = images.import_picture(photo(storage, "loco.png", "blue"))
    LocomotiveService.add("GN", "A1", picture=payload)
    assert images.find_image("GN", "A1") != locomotive_images.find_image("GN", "A1")
    Service.update(car.id, "GN", "A1", remove_picture=True)
    assert locomotive_images.find_image("GN", "A1").read_bytes() == payload


def test_collision_and_case_protection(storage):
    car = add(storage)
    before = images.find_image("GN", "A1").read_bytes()
    collision = photo(images.image_directory(), "P_UP_2.jpeg", "blue")
    collision_bytes = collision.read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        Service.update(car.id, "UP", "2")
    with pytest.raises(ValueError, match="same picture identity"):
        Service.add("gn", "a1")
    assert images.find_image("GN", "A1").read_bytes() == before
    assert collision.read_bytes() == collision_bytes
    assert Service.get_by_id(car.id).reporting_mark == "GN"


@pytest.mark.parametrize("action", ["add", "replace", "rename", "remove"])
def test_failed_database_save_restores_images(storage, test_database, action):
    car = add(storage)
    before = {p.name: p.read_bytes() for p in images.image_directory().iterdir()}

    def fail(session):
        raise RuntimeError("Simulated commit failure")

    session_class = test_database.SessionLocal.class_
    event.listen(session_class, "before_commit", fail)
    try:
        with pytest.raises(RuntimeError, match="Simulated"):
            payload = images.import_picture(photo(storage, "new.png", "blue"))
            if action == "add":
                Service.add("UP", "2", picture=payload)
            else:
                Service.update(
                    car.id,
                    "UP" if action == "rename" else "GN",
                    "A1",
                    picture=payload if action == "replace" else None,
                    remove_picture=action == "remove",
                )
    finally:
        event.remove(session_class, "before_commit", fail)
    assert {
        p.name: p.read_bytes() for p in images.image_directory().iterdir()
    } == before
    assert Service.get_by_id(car.id).reporting_mark == "GN"
    assert len(Service.get_all()) == 1


def test_add_cancel_and_source_independence(storage, qapp, monkeypatch):
    dialog = AddPassengerCarDialog()
    source = photo(storage)
    choose(dialog, source, monkeypatch)
    dialog.reject()
    assert not images.image_directory().exists()
    assert Service.get_all() == []
    second = AddPassengerCarDialog()
    second.reporting_mark.setText("GN")
    second.number.setText("A1")
    choose(second, source, monkeypatch)
    source.unlink()  # The selected picture is already staged in memory.
    second.save()
    assert second.result() == second.DialogCode.Accepted
    assert images.find_image("GN", "A1").exists()


@pytest.mark.parametrize("action", ["replace", "remove", "rename"])
def test_edit_cancel_preserves_image(storage, qapp, monkeypatch, action):
    car = add(storage)
    before = images.find_image("GN", "A1").read_bytes()
    dialog = AddPassengerCarDialog(passenger_car=car)
    if action == "replace":
        choose(dialog, photo(storage, "new.png", "blue"), monkeypatch)
    elif action == "remove":
        dialog.clear_picture()
    else:
        dialog.number.setText("2")
    dialog.reject()
    assert images.find_image("GN", "A1").read_bytes() == before
    assert Service.get_by_id(car.id).number == "A1"


def test_editor_reopen_remove_and_fields(storage, qapp):
    car = add(storage)
    dialog = AddPassengerCarDialog(passenger_car=car)
    assert dialog.name.text() == "Test Coach"
    assert dialog.length.text() == "85"
    preview = dialog.picture_preview.pixmap()
    assert not preview.isNull()
    assert abs(preview.width() / preview.height() - 3) < 0.05
    assert preview.width() <= 400 and preview.height() <= 150
    dialog.clear_picture()
    dialog.equipment_type.setCurrentText("Sleeper")
    dialog.save()
    saved = Service.get_by_id(car.id)
    assert saved.name == "Test Coach" and saved.length == 85
    assert saved.equipment_type == "Sleeper"
    reopened = AddPassengerCarDialog(passenger_car=saved)
    assert reopened.picture_preview.text() == "No Image Available"
    assert not reopened.remove_picture_button.isEnabled()


def test_no_picture_and_invalid_selection(storage, qapp, monkeypatch):
    car = Service.add("GN", "3")
    dialog = AddPassengerCarDialog(passenger_car=car)
    assert dialog.picture_preview.text() == "No Image Available"
    messages = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: messages.append(args[2]))
    invalid = storage / "bad.jpg"
    invalid.write_bytes(b"broken")
    choose(dialog, invalid, monkeypatch)
    assert messages and dialog.picture is None
    dialog.save()
    assert dialog.result() == dialog.DialogCode.Accepted
    assert not images.image_directory().exists()


def test_runtime_override(storage, monkeypatch):
    monkeypatch.setenv("MODELRAILROADOPS_DATA_DIR", str(storage / "override"))
    monkeypatch.setattr(paths, "DATA_DIRECTORY", paths.data_directory())
    assert images.image_directory() == storage / "override" / "Passenger_Images"


def test_real_passenger_and_locomotive_backup_roundtrip(
    storage, test_database, monkeypatch
):
    engine = test_database.SessionLocal.kw["bind"]
    monkeypatch.setattr(database, "DATABASE_FILE", Path(engine.url.database))
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "initialize_database", lambda: None)
    car = add(storage)
    LocomotiveService.add(
        "GN", "A1", picture=images.import_picture(photo(storage, "loco.png", "blue"))
    )
    (storage / "Car_Images").mkdir()
    freight = photo(storage / "Car_Images", "GN_100.png")
    expected = {
        "Passenger_Images/P_GN_A1.png": images.find_image("GN", "A1").read_bytes(),
        "Locomotive_Images/L_GN_A1.png": locomotive_images.find_image(
            "GN", "A1"
        ).read_bytes(),
        "Car_Images/GN_100.png": freight.read_bytes(),
    }
    archive = storage / "all-pictures.zip"
    saved, message = DatabaseBackupService.create_backup(archive)
    assert saved, message
    Service.update(car.id, "GN", "A1", remove_picture=True)
    restored, safety = DatabaseBackupService.restore_backup(archive)
    assert restored, safety
    with zipfile.ZipFile(archive) as contents:
        for name, payload in expected.items():
            assert contents.read(name) == payload
            assert (storage / name).read_bytes() == payload
    assert Service.get_by_id(car.id).name == "Test Coach"
