"""Exercise the actual bundled runtime without touching normal user data."""
import json
import os
from pathlib import Path
import traceback


def verify():
    directory = os.environ.get("MODELRAILROADOPS_DATA_DIR")
    if not directory:
        return 2
    root = Path(directory).resolve()
    # Caller explicitly prepares this marker in a disposable test directory.
    if not (root / ".build-verification").is_file():
        return 2
    report = {}
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QImage
        from sqlalchemy import text
        from modelrailroadops.database import database
        from modelrailroadops.ui.main_window import MainWindow
        from modelrailroadops.services.database_backup_service import DatabaseBackupService
        from modelrailroadops.services.waybill_service import WaybillService
        from modelrailroadops.ui.waybills.waybill_preview_dialog import WaybillPreviewDialog
        app = QApplication([])
        database.initialize_database()
        assert database.DATABASE_FILE.resolve() == root / "railroad.db"
        window = MainWindow()
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
            report["waybills"] = connection.scalar(text("SELECT count(*) FROM waybills"))
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
        ok, result = DatabaseBackupService.restore_backup(archive)
        assert ok, result
        with database.engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM cars")) == report["cars"]
        report["backup_restore"] = "passed"
        window.close()
        report["result"] = "passed"
    except Exception:
        report["result"] = "failed"
        report["error"] = traceback.format_exc()
    (root / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["result"] == "passed" else 1
