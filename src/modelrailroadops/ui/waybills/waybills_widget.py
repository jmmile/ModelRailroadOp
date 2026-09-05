from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import (
    QPrinter,
    QPrinterInfo,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from modelrailroadops.services.waybill_service import (
    WaybillService,
)

from modelrailroadops.ui.dialogs.add_waybill_dialog import (
    AddWaybillDialog,
)

from modelrailroadops.ui.dialogs.move_car_dialog import (
    MoveCarDialog,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)

from modelrailroadops.ui.waybills.waybill_preview_dialog import (
    WaybillPreviewDialog,
)

from modelrailroadops.ui.waybills.waybill_table_model import (
    WaybillTableModel,
)

from modelrailroadops.ui.waybills.waybill_form import (
    WaybillFormRenderer,
)


class WaybillsWidget(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(
            self
        )

        #
        # Buttons
        #

        button_layout = QHBoxLayout()

        self.add_button = QPushButton(
            "Add Waybill"
        )

        self.delete_button = QPushButton(
            "Delete Waybill"
        )

        self.progress_button = QPushButton(
            "In Progress"
        )

        self.move_button = QPushButton(
            "Move Car"
        )

        self.cancel_button = QPushButton(
            "Cancel"
        )

        self.preview_button = QPushButton(
            "Preview Waybill"
        )

        self.print_selected_button = QPushButton(
            "Print Selected"
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.archive_button = QPushButton(
            "Archive Waybill"
        )

        self.restore_button = QPushButton(
            "Restore Waybill"
        )

        self.view_label = QLabel(
            "View:"
        )

        self.view_combo = QComboBox()

        self.view_combo.addItem(
            "Open",
            "OPEN",
        )

        self.view_combo.addItem(
            "Completed",
            "COMPLETED",
        )

        self.view_combo.addItem(
            "Archived",
            "ARCHIVED",
        )

        self.view_combo.addItem(
            "All",
            "ALL",
        )

        button_layout.addWidget(
            self.add_button
        )

        button_layout.addWidget(
            self.delete_button
        )

        button_layout.addWidget(
            self.progress_button
        )

        button_layout.addWidget(
            self.move_button
        )

        button_layout.addWidget(
            self.cancel_button
        )

        button_layout.addWidget(
            self.preview_button
        )

        button_layout.addWidget(
            self.print_selected_button
        )

        button_layout.addWidget(
            self.refresh_button
        )

        button_layout.addWidget(
            self.archive_button
        )

        button_layout.addWidget(
            self.restore_button
        )

        button_layout.addSpacing(
            20
        )

        button_layout.addWidget(
            self.view_label
        )

        button_layout.addWidget(
            self.view_combo
        )

        button_layout.addStretch()

        layout.addLayout(
            button_layout
        )

        #
        # Table model
        #

        self.model = WaybillTableModel()

        #
        # Table
        #

        self.table = QTableView()

        self.table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.table.setModel(
            self.model
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSortingEnabled(
            True
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.table.horizontalHeader().setStretchLastSection(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        layout.addWidget(
            self.table
        )

        #
        # Signals
        #

        self.add_button.clicked.connect(
            self.add_waybill
        )

        self.delete_button.clicked.connect(
            self.delete_waybill
        )

        self.progress_button.clicked.connect(
            self.set_in_progress
        )

        self.move_button.clicked.connect(
            self.move_car
        )

        self.cancel_button.clicked.connect(
            self.cancel_waybill
        )

        self.preview_button.clicked.connect(
            self.preview_waybill
        )

        self.print_selected_button.clicked.connect(
            self.print_selected_waybills
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.archive_button.clicked.connect(
            self.archive_waybill
        )

        self.restore_button.clicked.connect(
            self.restore_waybill
        )

        self.view_combo.currentIndexChanged.connect(
            self.refresh
        )

        self.table.doubleClicked.connect(
            self.preview_waybill
        )

        #
        # Initial load
        #

        self.refresh()

    #
    # Refresh
    #

    def refresh(
        self,
        *_args,
    ):

        view = self.view_combo.currentData()

        waybills = WaybillService.get_by_archive_view(
            view
        )

        self.model.set_waybills(
            waybills
        )

        self.table.resizeColumnsToContents()

    #
    # Show Event
    #

    def showEvent(
        self,
        event,
    ):

        self.refresh()

        super().showEvent(
            event
        )

    #
    # Selected Waybill
    #

    def get_selected_waybill(
        self,
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Waybill",
                "Please select a waybill.",
            )

            return None

        return self.model.get_waybill(
            indexes[0].row()
        )

    #
    # Add Waybill
    #

    def add_waybill(
        self,
    ):

        dialog = AddWaybillDialog(
            self
        )

        if dialog.exec():

            self.refresh()

    #
    # Delete Waybill
    #

    def delete_waybill(
        self,
    ):

        waybill = (
            self.get_selected_waybill()
        )

        if waybill is None:

            return

        if waybill.status == "COMPLETED":

            QMessageBox.warning(
                self,
                "Delete Waybill",
                "A completed waybill should not be deleted.",
            )

            return

        answer = QMessageBox.question(
            self,
            "Delete Waybill",
            (
                f"Delete Waybill #{waybill.id}?\n\n"
                "This cannot be undone."
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        if WaybillService.delete(
            waybill.id
        ):

            self.refresh()

        else:

            QMessageBox.warning(
                self,
                "Delete Waybill",
                "The waybill could not be deleted.",
            )

    #
    # Set In Progress
    #

    def set_in_progress(
        self,
    ):

        waybill = (
            self.get_selected_waybill()
        )

        if waybill is None:

            return

        success, result = (
            WaybillService.set_in_progress(
                waybill.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "In Progress",
                str(result),
            )

            return

        self.refresh()

    #
    # Move Car
    #

    def move_car(
        self,
    ):

        waybill = (
            self.get_selected_waybill()
        )

        if waybill is None:

            return

        #
        # A Waybill can only be physically worked
        # when it is in progress.
        #

        if waybill.status != "IN_PROGRESS":

            QMessageBox.information(
                self,
                "Move Car",
                (
                    "The selected waybill must be "
                    "IN_PROGRESS before the car can be moved."
                ),
            )

            return

        #
        # The Waybill must have an assigned car.
        #

        if waybill.car_id is None:

            QMessageBox.warning(
                self,
                "Move Car",
                (
                    f"Waybill #{waybill.id} "
                    "does not have an assigned car."
                ),
            )

            return

        #
        # Open the existing Move Car dialog.
        #
        # MoveCarDialog automatically finds the car's
        # active Waybill and locks the destination to
        # that Waybill.
        #

        dialog = MoveCarDialog(
            waybill.car_id,
            self,
        )

        dialog.exec()

        #
        # The physical move and Waybill completion are
        # handled by MoveCarDialog.
        #
        # Refresh the table afterward so the Waybill
        # status and car/location information are current.
        #

        self.refresh()

    #
    # Cancel
    #

    def cancel_waybill(
        self,
    ):

        waybill = (
            self.get_selected_waybill()
        )

        if waybill is None:

            return

        answer = QMessageBox.question(
            self,
            "Cancel Waybill",
            (
                f"Cancel Waybill #{waybill.id}?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:

            return

        success, result = (
            WaybillService.cancel(
                waybill.id
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Cancel Waybill",
                str(result),
            )

            return

        self.refresh()

    #
    # Archive Waybill
    #

    def archive_waybill(
        self,
    ):

        waybill = self.get_selected_waybill()

        if waybill is None:
            return

        success, result = WaybillService.archive(
            waybill.id
        )

        if not success:
            QMessageBox.warning(
                self,
                "Archive Waybill",
                str(result),
            )

            return

        self.refresh()

    #
    # Restore Waybill
    #

    def restore_waybill(
        self,
    ):

        waybill = self.get_selected_waybill()

        if waybill is None:
            return

        success, result = WaybillService.restore_from_archive(
            waybill.id
        )

        if not success:
            QMessageBox.warning(
                self,
                "Restore Waybill",
                str(result),
            )

            return

        self.refresh()

    #
    # Preview Waybill
    #

    def preview_waybill(
        self,
    ):

        waybill = (
            self.get_selected_waybill()
        )

        if waybill is None:

            return

        waybill_id = waybill.id

        dialog = WaybillPreviewDialog(
            waybill,
            self,
        )

        dialog.exec()

        #
        # The preview dialog closes normally.
        #

        if not dialog.edited:

            return

        #
        # The waybill was edited.
        #
        # Refresh the table so that the model contains
        # a fresh database-backed Waybill object.
        #

        self.refresh()

        #
        # Find the updated waybill in the refreshed model.
        #

        updated_waybill = None

        for row, item in enumerate(
            self.model.waybills
        ):

            if item.id == waybill_id:

                updated_waybill = item

                self.table.selectRow(
                    row
                )

                break

        #
        # Show the updated preview.
        #

        if updated_waybill is not None:

            updated_dialog = WaybillPreviewDialog(
                updated_waybill,
                self,
            )

            updated_dialog.exec()

    #
    # Printer Selection
    #

    def select_printer(
        self,
    ):
        """
        Display a simple printer-selection dialog.

        No QPrinter object is created for printing until the
        user has selected a printer and pressed OK.
        """

        printers = (
            QPrinterInfo.availablePrinters()
        )

        if not printers:

            QMessageBox.warning(
                self,
                "Print Selected",
                "No printers were found.",
            )

            return None

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "Select Printer"
        )

        dialog.setModal(
            True
        )

        layout = QVBoxLayout(
            dialog
        )

        form_layout = QFormLayout()

        printer_combo = QComboBox()

        default_index = 0

        default_printer = (
            QPrinterInfo.defaultPrinter()
        )

        for index, printer_info in enumerate(
            printers
        ):

            printer_name = (
                printer_info.printerName()
            )

            printer_combo.addItem(
                printer_name,
                printer_name,
            )

            if (
                not default_printer.isNull()
                and printer_name
                == default_printer.printerName()
            ):

                default_index = index

        printer_combo.setCurrentIndex(
            default_index
        )

        form_layout.addRow(
            QLabel("Printer:"),
            printer_combo,
        )

        layout.addLayout(
            form_layout
        )

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        button_box.accepted.connect(
            dialog.accept
        )

        button_box.rejected.connect(
            dialog.reject
        )

        layout.addWidget(
            button_box
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):

            return None

        printer_name = (
            printer_combo.currentData()
        )

        if not printer_name:

            return None

        return printer_name

    #
    # Print Selected Waybills
    #

    def print_selected_waybills(
        self,
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Print Selected",
                "Please select one or more waybills.",
            )

            return

        waybills = []

        for index in indexes:

            waybill = (
                self.model.get_waybill(
                    index.row()
                )
            )

            if waybill is not None:

                waybills.append(
                    waybill
                )

        if not waybills:

            return

        #
        # Select printer FIRST.
        #

        printer_name = (
            self.select_printer()
        )

        if printer_name is None:

            return

        #
        # Create printer AFTER selection.
        #

        printer = QPrinter(
            QPrinter.PrinterMode.HighResolution
        )

        printer.setPrinterName(
            printer_name
        )

        printer.setDocName(
            "Model Railroad Operations Waybills"
        )

        #
        # Get actual printer resolution.
        #

        dpi_x = printer.logicalDpiX()
        dpi_y = printer.logicalDpiY()

        if dpi_x <= 0:

            dpi_x = printer.resolution()

        if dpi_y <= 0:

            dpi_y = printer.resolution()

        if dpi_x <= 0 or dpi_y <= 0:

            QMessageBox.critical(
                self,
                "Print Error",
                "The printer did not report a valid resolution.",
            )

            return

        #
        # Physical waybill dimensions.
        #
        # These MUST remain exactly 3.75 x 4.00 inches.
        #

        form_width = (
            WaybillFormRenderer.inches_to_pixels(
                WaybillFormRenderer.WIDTH_INCHES,
                dpi_x,
            )
        )

        form_height = (
            WaybillFormRenderer.inches_to_pixels(
                WaybillFormRenderer.HEIGHT_INCHES,
                dpi_y,
            )
        )

        #
        # Printable page.
        #

        page_rect = printer.pageRect(
            QPrinter.Unit.DevicePixel
        )

        page_width = float(
            page_rect.width()
        )

        page_height = float(
            page_rect.height()
        )

        #
        # Four waybills arranged 2 x 2.
        #

        sheet_width = (
            float(form_width) * 2.0
        )

        sheet_height = (
            float(form_height) * 2.0
        )

        if (
            sheet_width > page_width
            or sheet_height > page_height
        ):

            QMessageBox.warning(
                self,
                "Print Error",
                (
                    "Four 3.75 x 4.00 inch waybills "
                    "will not fit in the printable area.\n\n"
                    f"Required: "
                    f"{int(sheet_width)} x "
                    f"{int(sheet_height)} pixels\n"
                    f"Available: "
                    f"{int(page_width)} x "
                    f"{int(page_height)} pixels"
                ),
            )

            return

        #
        # Center the 2 x 2 group.
        #

        sheet_x = (
            float(page_rect.x())
            + (
                page_width
                - sheet_width
            )
            / 2.0
        )

        sheet_y = (
            float(page_rect.y())
            + (
                page_height
                - sheet_height
            )
            / 2.0
        )

        #
        # Start painting.
        #

        painter = QPainter()

        if not painter.begin(
            printer
        ):

            QMessageBox.critical(
                self,
                "Print Error",
                "The printer could not be started.",
            )

            return

        printed_count = 0
        printed_pages = 0

        try:

            #
            # Process four waybills at a time.
            #

            for page_start in range(
                0,
                len(waybills),
                4,
            ):

                if printed_pages > 0:

                    if not printer.newPage():

                        break

                page_waybills = waybills[
                    page_start:page_start + 4
                ]

                #
                # Draw only the waybills that were selected.
                #
                # Unused positions remain blank.
                #

                for position, waybill in enumerate(
                    page_waybills
                ):

                    column = (
                        position % 2
                    )

                    row = (
                        position // 2
                    )

                    form_x = (
                        sheet_x
                        + (
                            column
                            * float(form_width)
                        )
                    )

                    form_y = (
                        sheet_y
                        + (
                            row
                            * float(form_height)
                        )
                    )

                    form_rect = QRectF(
                        form_x,
                        form_y,
                        float(form_width),
                        float(form_height),
                    )

                    renderer = WaybillFormRenderer(
                        waybill
                    )

                    renderer.draw(
                        painter,
                        form_rect,
                    )

                    printed_count += 1

                printed_pages += 1

        finally:

            painter.end()

        if printed_count == 0:

            QMessageBox.warning(
                self,
                "Print Selected",
                "No waybills were printed.",
            )

            return

        QMessageBox.information(
            self,
            "Print Selected",
            (
                f"{printed_count} waybill(s) "
                f"were sent to the printer "
                f"on {printed_pages} page(s)."
            ),
        )