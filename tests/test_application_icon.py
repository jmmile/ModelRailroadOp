import struct
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QImage
from PySide6.QtWidgets import QApplication


def test_windows_icon_has_all_sizes():
    path = Path(__file__).resolve().parents[1] / "src/modelrailroadops/resources/application.ico"
    data = path.read_bytes()
    assert struct.unpack_from("<HHH", data) == (0, 1, 7)
    sizes = []
    for index in range(7):
        width, height, _, _, _, bits, length, offset = struct.unpack_from(
            "<BBBBHHII", data, 6 + index * 16
        )
        size = width or 256
        assert (height or 256) == size and bits == 32
        image = QImage.fromData(data[offset:offset + length], "PNG")
        assert not image.isNull() and image.width() == size
        sizes.append(size)
    assert sizes == [16, 24, 32, 48, 64, 128, 256]
    app = QApplication.instance() or QApplication([])
    icon = QIcon(str(path))
    assert not icon.isNull()
    for size in sizes:
        assert not icon.pixmap(QSize(size, size)).isNull()
