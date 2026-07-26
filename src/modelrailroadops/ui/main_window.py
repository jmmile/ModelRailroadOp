from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMainWindow


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Locate the .ui file
        project_root = Path(__file__).resolve().parents[3]
        ui_path = project_root / "resources" / "ui" / "main_window.ui"

        loader = QUiLoader()

        ui_file = QFile(str(ui_path))

        if not ui_file.open(QFile.ReadOnly):
            raise RuntimeError(f"Cannot open UI file:\n{ui_path}")

        self.ui = loader.load(ui_file)
        ui_file.close()

        if self.ui is None:
            raise RuntimeError("Qt Designer UI failed to load.")

        # Make the loaded UI the central widget
        self.setCentralWidget(self.ui.centralWidget())

        # Copy title
        self.setWindowTitle(self.ui.windowTitle())

        # Copy menu bar
        if self.ui.menuBar():
            self.setMenuBar(self.ui.menuBar())

        # Copy status bar
        if self.ui.statusBar():
            self.setStatusBar(self.ui.statusBar())

        self.resize(1400, 900)