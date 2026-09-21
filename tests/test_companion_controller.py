import time
from urllib.request import urlopen

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from modelrailroadops.services.companion_controller import CompanionController
from modelrailroadops.ui.widgets.companion_panel import CompanionPanel


def wait_until(controller, predicate):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        controller.poll()
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError(controller.status)


def test_real_server_lifecycle_and_port_conflict():
    app = QApplication.instance() or QApplication([])
    first = CompanionController(port=0)
    try:
        first.start()
        wait_until(first, lambda: first.status == "Running")
        original_thread = first.thread
        first.start()
        assert first.thread is original_thread
        assert len(first.code) == 6 and first.code.isdigit()
        with urlopen(f"http://127.0.0.1:{first.port}/health", timeout=3) as response:
            assert response.status == 200
        second = CompanionController(port=first.port)
        second.start()
        assert not second.busy
        assert "Unavailable" in second.status
        second.stop()
        assert first.busy
        from modelrailroadops.web import server
        old_token = server.AUTH_TOKEN
        first.stop()
        wait_until(first, lambda: not first.busy)
        assert first.status == "Stopped" and not first.code
        first.start()
        wait_until(first, lambda: first.status == "Running")
        assert server.AUTH_TOKEN != old_token
    finally:
        first.stop()
        wait_until(first, lambda: not first.busy)


def test_stop_during_startup():
    app = QApplication.instance() or QApplication([])
    controller = CompanionController(port=0)
    controller.start()
    controller.stop()
    wait_until(controller, lambda: not controller.busy)
    assert controller.status == "Stopped"


def test_preference_and_panel(tmp_path):
    app = QApplication.instance() or QApplication([])
    path = str(tmp_path / "settings.ini")
    controller = CompanionController(port=0)
    panel = CompanionPanel(settings=QSettings(path, QSettings.IniFormat), controller=controller)
    assert panel.automatic.isChecked()
    assert not controller.busy  # constructing widgets/tests never starts a server
    panel.automatic.setChecked(False)
    other = CompanionPanel(settings=QSettings(path, QSettings.IniFormat))
    assert not other.automatic.isChecked()
    other.start_automatically()
    assert not other.controller.busy
    try:
        panel.start_button.click()
        wait_until(controller, lambda: controller.status == "Running")
        assert controller.code in panel.details.text()
        assert not panel.start_button.isEnabled()
        assert panel.stop_button.isEnabled()
        panel.stop_button.click()
        wait_until(controller, lambda: not controller.busy)
        assert panel.start_button.isEnabled()
        assert not panel.stop_button.isEnabled()
    finally:
        controller.stop()
        wait_until(controller, lambda: not controller.busy)
        panel.close()
        other.close()


def test_server_failure_is_reported(monkeypatch):
    import uvicorn
    app = QApplication.instance() or QApplication([])
    def fail(*args, **kwargs):
        raise RuntimeError("test startup failure")
    monkeypatch.setattr(uvicorn.Server, "run", fail)
    controller = CompanionController(port=0)
    controller.start()
    wait_until(controller, lambda: not controller.busy)
    assert controller.status == "Failed: test startup failure"
    assert not controller.code
