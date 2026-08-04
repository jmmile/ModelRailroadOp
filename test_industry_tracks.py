import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).parent / "src")
)

from PySide6.QtWidgets import QApplication

from modelrailroadops.ui.widgets.industry_tracks_widget import (
    IndustryTracksWidget
)


app = QApplication(sys.argv)

window = IndustryTracksWidget()
window.resize(600, 400)
window.show()

sys.exit(app.exec())