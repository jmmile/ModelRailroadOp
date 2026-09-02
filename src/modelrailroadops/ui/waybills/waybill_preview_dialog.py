from PySide6.QtCore import (
    Qt,
)

from PySide6.QtGui import (
    QPainter,
    QPixmap,
)

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from modelrailroadops.ui.dialogs.add_waybill_dialog import (
    AddWaybillDialog,
)

from modelrailroadops.ui.waybills.waybill_form import (
    WaybillFormRenderer,
)


class WaybillPreviewDialog(QDialog):

    def __init__(
        self,
        waybill,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.waybill = waybill

        self.edited = False

        self.setWindowTitle(
            f"Waybill Preview #{waybill.id}"
        )

        self.setModal(
            True
        )

        self.setMinimumSize(
            500,
            650,
        )

        layout = QVBoxLayout(
            self
        )

        #
        # Preview
        #

        self.preview_label = QLabel()

        self.preview_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.preview_label.setStyleSheet(
            """
            QLabel {
                background-color: white;
                border: 1px solid #888888;
            }
            """
        )

        layout.addWidget(
            self.preview_label,
            1,
        )

        #
        # Buttons
        #

        self.button_box = QDialogButtonBox()

        self.edit_button = (
            self.button_box.addButton(
                "Edit Waybill",
                QDialogButtonBox.ButtonRole.ActionRole,
            )
        )

        self.close_button = (
            self.button_box.addButton(
                QDialogButtonBox.StandardButton.Close
            )
        )

        self.edit_button.clicked.connect(
            self.edit_waybill
        )

        self.close_button.clicked.connect(
            self.reject
        )

        layout.addWidget(
            self.button_box
        )

        #
        # Create preview
        #

        self.create_preview()

    #
    # Create Preview
    #

    def create_preview(
        self,
    ):

        preview_width = 600

        preview_height = int(
            preview_width
            * (
                WaybillFormRenderer.HEIGHT_INCHES
                / WaybillFormRenderer.WIDTH_INCHES
            )
        )

        pixmap = QPixmap(
            preview_width,
            preview_height,
        )

        pixmap.fill(
            Qt.GlobalColor.white
        )

        renderer = WaybillFormRenderer(
            self.waybill
        )

        painter = QPainter(
            pixmap
        )

        renderer.draw(
            painter,
            pixmap.rect()
        )

        painter.end()

        self.preview_label.setPixmap(
            pixmap
        )

    #
    # Edit Waybill
    #

    def edit_waybill(
        self,
    ):

        dialog = AddWaybillDialog(
            self,
            waybill=self.waybill,
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):

            return

        #
        # The waybill was successfully edited.
        #

        self.edited = True

        self.accept()