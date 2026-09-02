import os
from dataclasses import dataclass

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import modelrailroadops.models  # noqa: F401
from modelrailroadops.database.base import Base
from modelrailroadops.services import (
    car_location_service,
    car_move_generation_service,
    car_move_service,
    operations_session_service,
    operations_session_train_service,
    switch_list_move_service,
    switch_list_service,
    train_route_service,
    waybill_service,
)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@dataclass(frozen=True)
class TestDatabase:
    SessionLocal: sessionmaker


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    """Give each test a new SQLite database and leave railroad.db untouched."""

    database_path = tmp_path / "railroad-test.db"
    engine = create_engine(f"sqlite:///{database_path}")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    session_factory = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    for service_module in (
        car_location_service,
        car_move_generation_service,
        car_move_service,
        operations_session_service,
        operations_session_train_service,
        switch_list_service,
        switch_list_move_service,
        train_route_service,
        waybill_service,
    ):
        monkeypatch.setattr(service_module, "SessionLocal", session_factory)

    yield TestDatabase(SessionLocal=session_factory)

    engine.dispose()


@pytest.fixture(scope="session")
def qapp():
    """Provide one offscreen Qt application for presentation smoke tests."""

    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    yield application
