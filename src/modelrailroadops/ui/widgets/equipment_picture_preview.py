"""Read-only selected-equipment preview shared by the two equipment rosters."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QGroupBox, QLabel, QSizePolicy, QVBoxLayout


class ScaledPictureLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.original = QPixmap()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(440)
        self.setFixedHeight(190)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            "QLabel { background-color: white; border: 1px solid #b8b8b8; }"
        )

    def show_message(self, message):
        self.original = QPixmap()
        self.clear()
        self.setToolTip("")
        self.setText(message)

    def show_image(self, image):
        self.original = QPixmap.fromImage(image)
        self.scale_picture()

    def scale_picture(self):
        if not self.original.isNull():
            self.setPixmap(self.original.scaled(
                self.contentsRect().size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scale_picture()


class EquipmentPicturePreview(QGroupBox):
    def __init__(self, title, noun, find_image, parent=None):
        super().__init__(title, parent)
        self.noun = noun
        self.find_image = find_image
        layout = QVBoxLayout(self)
        self.equipment_label = QLabel()
        self.picture_label = ScaledPictureLabel()
        layout.addWidget(self.equipment_label)
        layout.addWidget(self.picture_label)
        self.show_equipment(None)

    def show_equipment(self, equipment):
        if equipment is None:
            self.equipment_label.setText(f"No {self.noun} selected")
            self.picture_label.show_message(f"Select a {self.noun} to view its picture.")
            return
        name = f"{equipment.reporting_mark} {equipment.number}"
        detail = getattr(equipment, "model", None) or getattr(equipment, "name", None)
        self.equipment_label.setText(name + (f" — {detail}" if detail else ""))
        self.picture_label.show_message(f"No picture available for {name}.")
        try:
            path = self.find_image(equipment.reporting_mark, equipment.number)
            if path is None:
                return
            # QImage reloads the file rather than reusing QPixmap's filename cache.
            image = QImage(str(path))
            if image.isNull():
                self.picture_label.show_message("The picture could not be loaded.")
            else:
                self.picture_label.show_image(image)
            self.picture_label.setToolTip(str(path))
        except (OSError, ValueError) as error:
            self.picture_label.show_message("The picture could not be loaded.")
            self.picture_label.setToolTip(str(error))


def restore_equipment_selection(table, proxy, get_record, record_id):
    """Retain the selected record after a roster reset, never by its old row."""
    if record_id is None:
        return
    for row in range(proxy.sourceModel().rowCount()):
        if get_record(row).id == record_id:
            index = proxy.mapFromSource(proxy.sourceModel().index(row, 0))
            if index.isValid():
                table.selectRow(index.row())
            return
