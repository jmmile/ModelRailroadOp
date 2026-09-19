import sqlite3
import zipfile

from modelrailroadops import paths
from modelrailroadops.database import database
from modelrailroadops.services.database_backup_service import (
    DatabaseBackupService as Backup,
)
from test_database_backup_service import _create_application_database, _car_number


def prepare(tmp_path, monkeypatch):
    db = tmp_path / "railroad.db"
    _create_application_database(db, "ORIGINAL")
    monkeypatch.setattr(database, "DATABASE_FILE", db)
    monkeypatch.setattr(database.engine, "dispose", lambda: None)
    monkeypatch.setattr(database, "initialize_database", lambda: None)
    images = tmp_path / "Car_Images"
    images.mkdir()
    (images / "GN.png").write_bytes(b"original-image")
    return db, images


def test_layout_round_trip_and_safety_copy(tmp_path, monkeypatch):
    db, images = prepare(tmp_path, monkeypatch)
    archive = tmp_path / "layout.zip"
    assert Backup.create_backup(archive)[0]
    with sqlite3.connect(db) as connection:
        connection.execute("UPDATE cars SET value='CURRENT'")
    (images / "GN.png").write_bytes(b"current-image")
    (images / "extra.png").write_bytes(b"extra")
    success, safety = Backup.restore_backup(archive)
    assert success, safety
    assert _car_number(db) == "ORIGINAL"
    assert (images / "GN.png").read_bytes() == b"original-image"
    assert not (images / "extra.png").exists()
    with zipfile.ZipFile(safety) as saved:
        assert saved.read("Car_Images/GN.png") == b"current-image"
        assert saved.read("Car_Images/extra.png") == b"extra"


def test_failed_safety_backup_never_restores_partial_copy(tmp_path, monkeypatch):
    db, images = prepare(tmp_path, monkeypatch)
    incoming = tmp_path / "incoming.db"
    _create_application_database(incoming, "NEW")

    def fail(*args):
        raise OSError("Disk full")

    monkeypatch.setattr(Backup, "_copy_database", fail)
    success, message = Backup.restore_backup(incoming)
    assert not success
    assert "safety backup failed" in message
    assert _car_number(db) == "ORIGINAL"


def test_zip_migration_failure_recovers_database_and_images(tmp_path, monkeypatch):
    db, images = prepare(tmp_path, monkeypatch)
    archive = tmp_path / "layout.zip"
    assert Backup.create_backup(archive)[0]
    with sqlite3.connect(db) as connection:
        connection.execute("UPDATE cars SET value='CURRENT'")
    (images / "GN.png").write_bytes(b"current-image")

    def fail():
        raise RuntimeError("Migration failed")

    monkeypatch.setattr(database, "initialize_database", fail)
    success, message = Backup.restore_backup(archive)
    assert not success
    assert "previous layout restored" in message
    assert _car_number(db) == "CURRENT"
    assert (images / "GN.png").read_bytes() == b"current-image"


def test_unsafe_zip_rejected_without_changes(tmp_path, monkeypatch):
    db, images = prepare(tmp_path, monkeypatch)
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("../escape.txt", "bad")
    assert not Backup.restore_backup(archive)[0]
    assert _car_number(db) == "ORIGINAL"
    assert not (tmp_path / "escape.txt").exists()


def test_missing_backup_source_does_not_create_empty_database(tmp_path):
    assert not Backup._validate_database(tmp_path / "missing.db")[0]
    assert not (tmp_path / "missing.db").exists()


def test_failed_backup_preserves_existing_good_copy(tmp_path, monkeypatch):
    db, images = prepare(tmp_path, monkeypatch)
    destination = tmp_path / "saved.db"
    _create_application_database(destination, "SAVED")
    monkeypatch.setattr(database, "DATABASE_FILE", tmp_path / "missing.db")
    assert not Backup.create_backup(destination)[0]
    assert _car_number(destination) == "SAVED"
    assert not (tmp_path / "missing.db").exists()


def test_packaged_and_source_paths(tmp_path, monkeypatch):
    monkeypatch.delenv("MODELRAILROADOPS_DATA_DIR", raising=False)
    monkeypatch.setattr(paths.sys, "frozen", False, raising=False)
    assert paths.data_directory() == paths.PROJECT_ROOT / "data"
    monkeypatch.setattr(paths.sys, "frozen", True)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert paths.data_directory() == tmp_path / "ModelRailroadOperations"
    monkeypatch.setenv("MODELRAILROADOPS_DATA_DIR", str(tmp_path / "test-data"))
    assert paths.data_directory() == tmp_path / "test-data"


def test_compatibility_imports_share_engine_and_sessions():
    from modelrailroadops.database.engine import engine
    from modelrailroadops.database.session import SessionLocal

    assert engine is database.engine
    assert SessionLocal is database.SessionLocal
