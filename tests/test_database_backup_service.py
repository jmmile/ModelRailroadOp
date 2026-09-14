import sqlite3
from types import SimpleNamespace

from sqlalchemy import create_engine

from modelrailroadops.database import database
from modelrailroadops.services.database_backup_service import (
    DatabaseBackupService,
)


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
