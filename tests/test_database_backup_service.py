import sqlite3
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from sqlalchemy import create_engine

from modelrailroadops.database import database
from modelrailroadops.services.database_backup_service import (
    DatabaseBackupService,
)
from modelrailroadops.services.image_storage import MANAGED_IMAGE_FOLDERS


@pytest.fixture
def layout(tmp_path, monkeypatch):
    active = tmp_path / "railroad.db"
    _create_application_database(active, "CURRENT")
    monkeypatch.setattr(database, "DATABASE_FILE", active)
    monkeypatch.setattr(database.engine, "dispose", lambda: None)
    monkeypatch.setattr(database, "initialize_database", lambda: None)
    for folder in MANAGED_IMAGE_FOLDERS:
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "picture.png").write_bytes(folder.encode())
    return tmp_path


def test_layout_backup_restores_all_picture_collections(layout):
    archive = layout / "layout.zip"
    saved, result = DatabaseBackupService.create_backup(archive)
    assert saved, result
    with zipfile.ZipFile(archive) as contents:
        for folder in MANAGED_IMAGE_FOLDERS:
            assert contents.read(folder + "/picture.png") == folder.encode()
            (layout / folder / "picture.png").write_bytes(b"changed")
    restored, safety = DatabaseBackupService.restore_backup(archive)
    assert restored, safety
    for folder in MANAGED_IMAGE_FOLDERS:
        assert (layout / folder / "picture.png").read_bytes() == folder.encode()
    with zipfile.ZipFile(safety) as contents:
        for folder in MANAGED_IMAGE_FOLDERS:
            assert contents.read(folder + "/picture.png") == b"changed"


def test_legacy_zip_preserves_new_picture_collections(layout):
    archive = layout / "old.zip"
    with zipfile.ZipFile(archive, "w") as contents:
        contents.write(layout / "railroad.db", "railroad.db")
        contents.writestr("Car_Images/old.jpg", b"old-car")
    restored, result = DatabaseBackupService.restore_backup(archive)
    assert restored, result
    assert (layout / "Car_Images" / "old.jpg").read_bytes() == b"old-car"
    assert not (layout / "Car_Images" / "picture.png").exists()
    for folder in MANAGED_IMAGE_FOLDERS[1:]:
        assert (layout / folder / "picture.png").read_bytes() == folder.encode()


def test_empty_collection_round_trip(layout):
    picture = layout / "Locomotive_Images" / "picture.png"
    picture.unlink()
    saved, result = DatabaseBackupService.create_backup(layout / "empty.zip")
    assert saved, result
    picture.write_bytes(b"added later")
    restored, safety = DatabaseBackupService.restore_backup(layout / "empty.zip")
    assert restored, safety
    assert not picture.exists()
    with zipfile.ZipFile(safety) as contents:
        assert contents.read("Locomotive_Images/picture.png") == b"added later"


def test_picture_restore_failure_rolls_back_all_collections(layout, monkeypatch):
    archive = layout / "layout.zip"
    assert DatabaseBackupService.create_backup(archive)[0]
    for folder in MANAGED_IMAGE_FOLDERS:
        (layout / folder / "picture.png").write_bytes(b"current")
    original_rename = Path.rename

    def fail_install(path, target):
        if path.parent.name == "incoming" and path.name == "Locomotive_Images":
            raise OSError("Simulated image restore failure")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_install)
    restored, message = DatabaseBackupService.restore_backup(archive)
    assert not restored
    assert "previous layout restored" in message
    for folder in MANAGED_IMAGE_FOLDERS:
        assert (layout / folder / "picture.png").read_bytes() == b"current"
    assert _car_number(layout / "railroad.db") == "CURRENT"


@pytest.mark.parametrize(
    "name",
    [
        "Locomotive_Images/../railroad.db",
        "Passenger_Images/../../outside",
        "Other_Images/x.png",
    ],
)
def test_picture_archive_rejects_unsafe_paths(layout, name):
    archive = layout / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as contents:
        contents.write(layout / "railroad.db", "railroad.db")
        contents.writestr(name, b"bad")
    restored, message = DatabaseBackupService.restore_backup(archive)
    assert not restored
    assert "unsafe" in message
    for folder in MANAGED_IMAGE_FOLDERS:
        assert (layout / folder / "picture.png").read_bytes() == folder.encode()


def test_automatic_backup_retention_preserves_manual_files(tmp_path):
    source = tmp_path / "railroad.db"
    _create_application_database(source, "BEFORE")
    engine = create_engine(f"sqlite:///{source}")
    session = SimpleNamespace(get_bind=lambda: engine)
    folder = tmp_path / "backups" / "automatic"
    folder.mkdir(parents=True)
    manual = folder / "manual.db"
    _create_application_database(manual, "MANUAL")
    for _ in range(12):
        success, result = DatabaseBackupService.automatic_backup(session)
        assert success, result
    assert len(list(folder.glob("railroad-auto-*.db"))) == 10
    assert _car_number(manual) == "MANUAL"
    assert _car_number(result) == "BEFORE"
    engine.dispose()


def _create_application_database(path, car_number):
    connection = sqlite3.connect(path)
    try:
        for table in ("cars", "industries", "locations", "waybills"):
            connection.execute(f"CREATE TABLE {table} (value TEXT)")
        connection.execute("INSERT INTO cars VALUES (?)", (car_number,))
        connection.commit()
    finally:
        connection.close()


def _car_number(path):
    connection = sqlite3.connect(path)
    try:
        return connection.execute("SELECT value FROM cars").fetchone()[0]
    finally:
        connection.close()


def test_create_backup_is_independent_snapshot(tmp_path, monkeypatch):
    active_database = tmp_path / "railroad.db"
    backup_path = tmp_path / "saved" / "layout.db"
    _create_application_database(active_database, "33103")
    monkeypatch.setattr(database, "DATABASE_FILE", active_database)

    created, result = DatabaseBackupService.create_backup(backup_path)
    assert created
    assert result == backup_path

    connection = sqlite3.connect(active_database)
    try:
        connection.execute("UPDATE cars SET value = '99999'")
        connection.commit()
    finally:
        connection.close()

    assert _car_number(backup_path) == "33103"


def test_restore_creates_safety_backup_and_replaces_data(tmp_path, monkeypatch):
    active_database = tmp_path / "railroad.db"
    restore_source = tmp_path / "earlier.db"
    _create_application_database(active_database, "CURRENT")
    _create_application_database(restore_source, "BACKUP")
    monkeypatch.setattr(database, "DATABASE_FILE", active_database)
    monkeypatch.setattr(database.engine, "dispose", lambda: None)
    monkeypatch.setattr(database, "initialize_database", lambda: None)

    restored, safety_backup = DatabaseBackupService.restore_backup(restore_source)

    assert restored
    assert _car_number(active_database) == "BACKUP"
    assert _car_number(safety_backup) == "CURRENT"


def test_restore_rejects_unrelated_sqlite_database(tmp_path):
    invalid_backup = tmp_path / "unrelated.db"
    connection = sqlite3.connect(invalid_backup)
    try:
        connection.execute("CREATE TABLE unrelated (value TEXT)")
        connection.commit()
    finally:
        connection.close()

    restored, message = DatabaseBackupService.restore_backup(invalid_backup)

    assert not restored
    assert "not a Model Railroad Operations backup" in message
