"""Convert the approved artwork into a multi-resolution Windows ICO."""
import struct
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage


def convert(source, target):
    original = QImage(str(source))
    if original.isNull() or original.width() != original.height():
        raise ValueError("Icon artwork must be a readable square image")
    sizes = (16, 24, 32, 48, 64, 128, 256)
    entries, payloads = [], []
    offset = 6 + 16 * len(sizes)
    for size in sizes:
        scaled = original.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        if not scaled.save(buffer, "PNG"):
            raise ValueError("Could not encode icon")
        payload = bytes(buffer.data())
        entries.append(struct.pack("<BBBBHHII", size % 256, size % 256,
                                   0, 0, 1, 32, len(payload), offset))
        payloads.append(payload)
        offset += len(payload)
    Path(target).write_bytes(struct.pack("<HHH", 0, 1, len(sizes))
                             + b"".join(entries) + b"".join(payloads))


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    convert(root / "packaging/artwork/concept-c.png",
            root / "src/modelrailroadops/resources/application.ico")
