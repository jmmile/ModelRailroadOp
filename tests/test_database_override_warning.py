"""Tests for visible database-override startup warnings."""

import uvicorn
from types import SimpleNamespace
from unittest.mock import Mock

import modelrailroadops.__main__ as application_module
from modelrailroadops.web import server


def test_desktop_warns_when_database_override_is_active(
    tmp_path,
    monkeypatch,
):
    """
    Desktop startup visibly warns when a data-directory override
    is active and identifies the database being used.
    """

    override_directory = tmp_path / "test-data"
    database_file = override_directory / "railroad.db"

    warning_calls = []
    companion_start = Mock()

    class FakeApplication:
        def __init__(self, arguments):
            self.arguments = arguments

        def exec(self):
            return 0

    class FakeMainWindow:
        dashboard_widget = SimpleNamespace(
            companion_panel=SimpleNamespace(start_automatically=companion_start)
        )

        def show(self):
            return None

    def fake_warning(
        parent,
        title,
        message,
    ):
        warning_calls.append(
            (
                parent,
                title,
                message,
            )
        )

        return None

    monkeypatch.setattr(
        application_module,
        "QApplication",
        FakeApplication,
    )

    monkeypatch.setattr(
        application_module,
        "DATA_DIRECTORY",
        override_directory,
    )

    monkeypatch.setattr(
        application_module,
        "DATABASE_FILE",
        database_file,
    )

    monkeypatch.setattr(
        application_module,
        "data_directory_override",
        lambda: override_directory,
    )

    monkeypatch.setattr(
        application_module,
        "initialize_database",
        lambda: None,
    )

    monkeypatch.setattr(
        application_module,
        "MainWindow",
        FakeMainWindow,
    )

    monkeypatch.setattr(
        application_module.QMessageBox,
        "warning",
        fake_warning,
    )

    result = application_module.Application().run()

    assert result == 0
    companion_start.assert_called_once_with()
    assert len(warning_calls) == 1

    _parent, title, message = warning_calls[0]

    assert title == "Database Override Active"
    assert "DATABASE OVERRIDE ACTIVE" in message
    assert str(database_file) in message
    assert "normal data directory" in message


def test_companion_banner_warns_when_database_override_is_active(
    tmp_path,
    monkeypatch,
    capsys,
):
    """
    Companion startup prominently identifies an active database
    override and the database selected for the server.
    """

    override_directory = tmp_path / "test-data"
    database_file = override_directory / "railroad.db"

    monkeypatch.setattr(
        server,
        "DATABASE_FILE",
        database_file,
    )

    monkeypatch.setattr(
        server,
        "data_directory_override",
        lambda: override_directory,
    )

    monkeypatch.setattr(
        uvicorn,
        "run",
        lambda *args, **kwargs: None,
    )

    server.run()

    output = capsys.readouterr().out

    assert "*** DATABASE OVERRIDE ACTIVE ***" in output

    assert (
        "The companion server is not using "
        "the normal data directory."
        in output
    )

    assert f"Database: {database_file}" in output


def test_companion_banner_has_no_override_warning_during_normal_startup(
    tmp_path,
    monkeypatch,
    capsys,
):
    """
    Normal companion startup reports its database without falsely
    claiming that a data-directory override is active.
    """

    database_file = tmp_path / "railroad.db"

    monkeypatch.setattr(
        server,
        "DATABASE_FILE",
        database_file,
    )

    monkeypatch.setattr(
        server,
        "data_directory_override",
        lambda: None,
    )

    monkeypatch.setattr(
        uvicorn,
        "run",
        lambda *args, **kwargs: None,
    )

    server.run()

    output = capsys.readouterr().out

    assert "DATABASE OVERRIDE ACTIVE" not in output
    assert f"Database: {database_file}" in output
