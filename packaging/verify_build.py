"""Exercise the actual bundled runtime without touching normal user data."""

import json
import os
from pathlib import Path
import traceback


def verify_desktop_companion(report):
    import time
    from modelrailroadops.services.companion_controller import CompanionController

    controller = CompanionController(port=0)
    try:
        controller.start()
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            controller.poll()
            if controller.status == "Running":
                break
            time.sleep(0.05)
        assert controller.status == "Running", controller.status
        assert len(controller.code) == 6
    finally:
        controller.stop()
        deadline = time.monotonic() + 15
        while controller.busy and time.monotonic() < deadline:
            controller.poll()
            time.sleep(0.05)
        assert not controller.busy, "Desktop companion failed to stop"
        controller.poll()
    report["desktop_companion"] = "background start, pairing code, shutdown passed"


def verify_companion(report):
    """Exercise the bundled HTTP server on an ephemeral loopback port."""
    import http.cookiejar
    import socket
    import threading
    import time
    import urllib.error
    import urllib.request
    import uvicorn
    from modelrailroadops.web import server

    assert server.INDEX_FILE.is_file(), "Missing bundled companion HTML"
    assert "refreshMovesAutomatically" in server.INDEX_FILE.read_text(encoding="utf-8")
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    address = f"http://127.0.0.1:{sock.getsockname()[1]}"
    host = uvicorn.Server(
        uvicorn.Config(
            server.app,
            loop="asyncio",
            http="h11",
            ws="none",
            log_config=None,
            access_log=False,
        )
    )
    thread = threading.Thread(target=host.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 15
        while not host.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert host.started, "Bundled web server did not start"
        client = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        with client.open(address + "/", timeout=5) as response:
            assert b"companion-screen" in response.read()
        try:
            client.open(address + "/api/sessions", timeout=5)
            raise AssertionError("Unpaired web access was accepted")
        except urllib.error.HTTPError as error:
            assert error.code == 401
        request = urllib.request.Request(
            address + "/api/pair",
            data=json.dumps({"code": server.PAIRING_CODE}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with client.open(request, timeout=5) as response:
            assert response.status == 200
        with client.open(address + "/api/sessions", timeout=5) as response:
            assert isinstance(json.load(response), list)
        report["web_companion"] = (
            "passed: HTML, HTTP, authentication, pairing, sessions"
        )
    finally:
        host.should_exit = True
        thread.join(timeout=10)
        sock.close()
        assert not thread.is_alive(), "Web verification server failed to stop"


def verify_pictures(root, report):
    from PySide6.QtGui import QImage, QColor
    from modelrailroadops.services import locomotive_image_service as locomotive_images
    from modelrailroadops.services import passenger_image_service as passenger_images
    from modelrailroadops.services.locomotive_service import LocomotiveService
    from modelrailroadops.services.passenger_car_service import PassengerCarService
    from modelrailroadops.ui.dialogs.add_locomotive_dialog import AddLocomotiveDialog
    from modelrailroadops.ui.dialogs.add_passenger_car_dialog import (
        AddPassengerCarDialog,
    )

    source = root / "generated-verification.jpg"
    image = QImage(120, 40, QImage.Format.Format_RGB32)
    image.fill(QColor("blue"))
    assert image.save(str(source), "JPEG"), "Missing bundled JPEG encoder"
    payload = locomotive_images.import_picture(source)
    locomotive = LocomotiveService.add("VERIFY", "L1", picture=payload)
    passenger = PassengerCarService.add("VERIFY", "P1", picture=payload)
    for dialog in [
        AddLocomotiveDialog(locomotive=locomotive),
        AddPassengerCarDialog(passenger_car=passenger),
    ]:
        assert not dialog.picture_preview.pixmap().isNull()
        dialog.close()
    assert locomotive_images.find_image("VERIFY", "L1").read_bytes() == payload
    assert passenger_images.find_image("VERIFY", "P1").read_bytes() == payload
    car_folder = root / "Car_Images"
    car_folder.mkdir(exist_ok=True)
    assert image.save(str(car_folder / "verification.png"), "PNG")
    report["picture_editors"] = (
        "passed: locomotive/passenger previews, JPEG import, PNG storage"
    )
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for folder in ["Car_Images", "Locomotive_Images", "Passenger_Images"]
        for path in (root / folder).iterdir()
        if path.is_file()
    }


def verify():
    directory = os.environ.get("MODELRAILROADOPS_DATA_DIR")
    if not directory:
        return 2
    root = Path(directory).resolve()
    # Caller explicitly prepares this marker in a disposable test directory.
    if not (root / ".build-verification").is_file():
        return 2
    # Never verify against a populated directory, even if somebody adds a marker.
    if any(path.name != ".build-verification" for path in root.iterdir()):
        return 2
    report = {}
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QImage
        from sqlalchemy import text
        from modelrailroadops.database import database
        from modelrailroadops.ui.main_window import MainWindow
        from modelrailroadops.services.database_backup_service import (
            DatabaseBackupService,
        )
        from modelrailroadops.services.waybill_service import WaybillService
        from modelrailroadops.ui.waybills.waybill_preview_dialog import (
            WaybillPreviewDialog,
        )

        app = QApplication([])
        database.initialize_database()
        assert database.DATABASE_FILE.resolve() == root / "railroad.db"
        pictures = verify_pictures(root, report)
        verify_companion(report)
        verify_desktop_companion(report)
        window = MainWindow()
        assert not window.windowIcon().isNull(), "Application icon missing"
        report["application_icon"] = "passed: bundled Qt window icon"
        window.show()
        app.processEvents()
        report["tabs"] = [window.tabs.tabText(i) for i in range(window.tabs.count())]
        for index in range(window.tabs.count()):
            window.tabs.setCurrentIndex(index)
            app.processEvents()
        window.open_dashboard()
        app.processEvents()
        assert window.grab().save(str(root / "dashboard.png"))
        with database.engine.connect() as connection:
            report["cars"] = connection.scalar(text("SELECT count(*) FROM cars"))
            report["waybills"] = connection.scalar(
                text("SELECT count(*) FROM waybills")
            )
        waybills = WaybillService.get_all()
        if waybills:
            preview = WaybillPreviewDialog(waybills[0], window)
            preview.show()
            app.processEvents()
            assert preview.grab().save(str(root / "waybill.png"))
            preview.close()
            report["waybill_preview"] = "passed"
        images = list((root / "Car_Images").glob("*.png"))
        report["image_count"] = len(images)
        if images:
            assert not QImage(str(images[0])).isNull()
        archive = root / "verification-layout.zip"
        ok, result = DatabaseBackupService.create_backup(archive)
        assert ok, result
        for name in pictures:
            (root / name).unlink()
        ok, result = DatabaseBackupService.restore_backup(archive)
        assert ok, result
        for name, contents in pictures.items():
            assert (root / name).read_bytes() == contents
        with database.engine.connect() as connection:
            assert (
                connection.scalar(text("SELECT count(*) FROM cars")) == report["cars"]
            )
        report["backup_restore"] = "passed"
        window.close()
        report["result"] = "passed"
    except Exception:
        report["result"] = "failed"
        report["error"] = traceback.format_exc()
    (root / "verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return 0 if report["result"] == "passed" else 1
