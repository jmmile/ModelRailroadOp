from statistics import median

from PySide6.QtCore import (
    QPoint,
    QRect,
    QSize,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QImage,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class CropPreviewLabel(QLabel):
    """Display an image and allow a crop rectangle to be dragged over it."""

    def __init__(self, image, parent=None):
        super().__init__(parent)

        self.source_image = image
        self.preview_image = image.scaled(
            QSize(900, 540),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.crop_rect = QRect(self.preview_image.rect())
        self.drag_start = None
        self.previous_crop_rect = QRect(self.crop_rect)

        self.setPixmap(
            QPixmap.fromImage(self.preview_image)
        )
        self.setFixedSize(self.preview_image.size())
        self.setCursor(Qt.CrossCursor)

    def set_image_crop_rect(self, image_rect):
        x_scale = self.preview_image.width() / self.source_image.width()
        y_scale = self.preview_image.height() / self.source_image.height()

        self.crop_rect = QRect(
            round(image_rect.x() * x_scale),
            round(image_rect.y() * y_scale),
            max(1, round(image_rect.width() * x_scale)),
            max(1, round(image_rect.height() * y_scale)),
        ).intersected(self.preview_image.rect())

        self.update()

    def image_crop_rect(self):
        x_scale = self.source_image.width() / self.preview_image.width()
        y_scale = self.source_image.height() / self.preview_image.height()

        return QRect(
            round(self.crop_rect.x() * x_scale),
            round(self.crop_rect.y() * y_scale),
            max(1, round(self.crop_rect.width() * x_scale)),
            max(1, round(self.crop_rect.height() * y_scale)),
        ).intersected(self.source_image.rect())

    def _bounded_point(self, point):
        return QPoint(
            min(max(point.x(), 0), self.width() - 1),
            min(max(point.y(), 0), self.height() - 1),
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.previous_crop_rect = QRect(self.crop_rect)
            self.drag_start = self._bounded_point(
                event.position().toPoint()
            )
            self.crop_rect = QRect(self.drag_start, self.drag_start)
            self.update()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_start is not None:
            current = self._bounded_point(
                event.position().toPoint()
            )
            self.crop_rect = QRect(
                self.drag_start,
                current,
            ).normalized()
            self.update()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_start is not None:
            current = self._bounded_point(
                event.position().toPoint()
            )
            proposed_rect = QRect(
                self.drag_start,
                current,
            ).normalized()

            if proposed_rect.width() >= 10 and proposed_rect.height() >= 10:
                self.crop_rect = proposed_rect
            else:
                self.crop_rect = self.previous_crop_rect

            self.drag_start = None
            self.update()

        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.crop_rect.isEmpty():
            return

        painter = QPainter(self)
        shade = QColor(0, 0, 0, 105)
        crop = self.crop_rect.intersected(self.rect())

        painter.fillRect(
            QRect(0, 0, self.width(), crop.top()),
            shade,
        )
        painter.fillRect(
            QRect(0, crop.bottom() + 1, self.width(), self.height()),
            shade,
        )
        painter.fillRect(
            QRect(0, crop.top(), crop.left(), crop.height()),
            shade,
        )
        painter.fillRect(
            QRect(
                crop.right() + 1,
                crop.top(),
                self.width() - crop.right() - 1,
                crop.height(),
            ),
            shade,
        )

        painter.setPen(
            QPen(QColor("#ffd54f"), 3)
        )
        painter.drawRect(crop)
        painter.end()


class CarImageCropDialog(QDialog):
    """Preview and approve a pixel-preserving crop of a car photograph."""

    def __init__(self, image, parent=None):
        super().__init__(parent)

        self.image = image

        self.setWindowTitle("Crop Car Picture")
        self.resize(960, 680)

        layout = QVBoxLayout(self)

        instructions = QLabel(
            "The yellow rectangle is the portion that will be saved. "
            "Drag anywhere on the picture to choose a different crop."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        preview_layout = QHBoxLayout()
        preview_layout.addStretch()
        self.preview = CropPreviewLabel(image, self)
        preview_layout.addWidget(self.preview)
        preview_layout.addStretch()
        layout.addLayout(preview_layout)

        crop_button_layout = QHBoxLayout()
        self.auto_crop_button = QPushButton("Auto Crop")
        self.full_image_button = QPushButton("Use Full Image")
        crop_button_layout.addWidget(self.auto_crop_button)
        crop_button_layout.addWidget(self.full_image_button)
        crop_button_layout.addStretch()
        layout.addLayout(crop_button_layout)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.buttons.button(QDialogButtonBox.Save).setText(
            "Use This Crop"
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.auto_crop_button.clicked.connect(self.apply_auto_crop)
        self.full_image_button.clicked.connect(self.use_full_image)

        self.apply_auto_crop()

    @staticmethod
    def _rgb(pixel):
        return (
            (pixel >> 16) & 255,
            (pixel >> 8) & 255,
            pixel & 255,
        )

    @staticmethod
    def _dominant_run(indices, counts):
        """Return the strongest nearly-contiguous foreground run."""

        if not indices:
            return None

        runs = []
        run_start = indices[0]
        previous = indices[0]

        for index in indices[1:]:
            if index - previous > 3:
                runs.append((run_start, previous))
                run_start = index
            previous = index

        runs.append((run_start, previous))

        return max(
            runs,
            key=lambda run: sum(
                counts[index]
                for index in range(run[0], run[1] + 1)
            ),
        )

    @classmethod
    def detect_auto_crop(cls, image):
        """Estimate the main object's bounds against a mostly even backdrop."""

        analysis = image.scaled(
            QSize(800, 600),
            Qt.KeepAspectRatio,
            Qt.FastTransformation,
        ).convertToFormat(QImage.Format_RGB32)

        width = analysis.width()
        height = analysis.height()

        if width < 10 or height < 10:
            return QRect(image.rect())

        # Estimate the background independently for every row. This handles
        # photos where the car rests on paper but the upper part of the image
        # shows a differently-colored wall or tabletop.
        edge_width = max(4, width // 30)
        edge_step = max(1, edge_width // 6)
        edge_positions = list(range(0, edge_width, edge_step))
        edge_positions.extend(
            range(width - edge_width, width, edge_step)
        )

        row_backgrounds = []

        for y in range(height):
            row_samples = [
                cls._rgb(analysis.pixel(x, y))
                for x in edge_positions
            ]
            row_backgrounds.append(
                tuple(
                    int(
                        median(
                            sample[channel]
                            for sample in row_samples
                        )
                    )
                    for channel in range(3)
                )
            )

        row_counts = [0] * height
        column_counts = [0] * width
        threshold = 34

        for y in range(height):
            background = row_backgrounds[y]
            background_luminance = sum(background) / 3.0
            background_saturation = max(background) - min(background)

            for x in range(width):
                red, green, blue = cls._rgb(analysis.pixel(x, y))
                difference = max(
                    abs(red - background[0]),
                    abs(green - background[1]),
                    abs(blue - background[2]),
                )

                luminance = (red + green + blue) / 3.0
                saturation = max(red, green, blue) - min(red, green, blue)
                meaningful_contrast = (
                    saturation >= max(42, background_saturation + 24)
                    or abs(luminance - background_luminance) >= 48
                )

                if difference >= threshold and meaningful_contrast:
                    row_counts[y] += 1
                    column_counts[x] += 1

        minimum_row_pixels = max(4, width // 90)
        minimum_column_pixels = max(4, height // 90)

        foreground_rows = [
            index
            for index, count in enumerate(row_counts)
            if count >= minimum_row_pixels
        ]
        foreground_columns = [
            index
            for index, count in enumerate(column_counts)
            if count >= minimum_column_pixels
        ]

        if not foreground_rows or not foreground_columns:
            return QRect(image.rect())

        horizontal_run = cls._dominant_run(
            foreground_columns,
            column_counts,
        )
        vertical_run = cls._dominant_run(
            foreground_rows,
            row_counts,
        )

        left, right = horizontal_run
        top, bottom = vertical_run

        # Very wide images are normally already car-shaped crops. Retain
        # their complete horizontal frame so ladders and couplers at either
        # edge are never trimmed by background estimation.
        if width / height >= 2.5:
            left = 0
            right = width - 1

        detected_width = right - left + 1
        detected_height = bottom - top + 1
        horizontal_padding = max(4, round(detected_width * 0.025))
        vertical_padding = max(4, round(detected_height * 0.04))

        detected = QRect(
            max(0, left - horizontal_padding),
            max(0, top - vertical_padding),
            min(width, right + horizontal_padding + 1)
            - max(0, left - horizontal_padding),
            min(height, bottom + vertical_padding + 1)
            - max(0, top - vertical_padding),
        )

        x_scale = image.width() / width
        y_scale = image.height() / height

        return QRect(
            round(detected.x() * x_scale),
            round(detected.y() * y_scale),
            max(1, round(detected.width() * x_scale)),
            max(1, round(detected.height() * y_scale)),
        ).intersected(image.rect())

    def apply_auto_crop(self):
        self.preview.set_image_crop_rect(
            self.detect_auto_crop(self.image)
        )

    def use_full_image(self):
        self.preview.set_image_crop_rect(
            self.image.rect()
        )

    def cropped_image(self):
        return self.image.copy(
            self.preview.image_crop_rect()
        )
