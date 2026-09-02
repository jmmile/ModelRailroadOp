
from pathlib import Path

from PySide6.QtCore import (
    QSize,
    Qt,
    QSortFilterProxyModel,
)

from PySide6.QtGui import (
    QImageReader,
    QPixmap,
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableView,
    QMessageBox,
    QLineEdit,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QFileDialog,
    QGroupBox,
)

from modelrailroadops.services.car_service import (
    CarService,
)

from modelrailroadops.ui.dialogs.add_car_dialog import (
    AddCarDialog,
)

from modelrailroadops.ui.dialogs.car_image_crop_dialog import (
    CarImageCropDialog,
)

from modelrailroadops.ui.cars.car_table_model import (
    CarTableModel,
)

from modelrailroadops.ui.waybills.waybill_form import (
    WaybillFormRenderer,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)


class RosterTab(QWidget):
    """
    Displays and manages the freight car roster.
    """

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        #
        # Status
        #

        self.status_label = QLabel()

        layout.addWidget(
            self.status_label
        )

        #
        # Search
        #

        search_layout = QHBoxLayout()

        search_layout.addWidget(
            QLabel("Search")
        )

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            "Reporting Mark, Number, Owner, Type, "
            "Empty Weight, Load Limit, Status, Current Location..."
        )

        search_layout.addWidget(
            self.search_box
        )

        layout.addLayout(
            search_layout
        )

        #
        # Buttons
        #

        button_layout = QHBoxLayout()

        self.add_button = QPushButton(
            "Add Car"
        )

        self.edit_button = QPushButton(
            "Edit Car"
        )

        self.delete_button = QPushButton(
            "Delete Car"
        )

        self.import_button = QPushButton(
            "Import CSV"
        )

        self.export_button = QPushButton(
            "Export CSV"
        )

        button_layout.addWidget(
            self.add_button
        )

        button_layout.addWidget(
            self.edit_button
        )

        button_layout.addWidget(
            self.delete_button
        )

        button_layout.addWidget(
            self.import_button
        )

        button_layout.addWidget(
            self.export_button
        )

        button_layout.addStretch()

        layout.addLayout(
            button_layout
        )

        #
        # Model
        #

        self.model = CarTableModel()

        self.proxy = QSortFilterProxyModel(
            self
        )

        self.proxy.setSourceModel(
            self.model
        )

        self.proxy.setFilterCaseSensitivity(
            Qt.CaseInsensitive
        )

        self.proxy.setFilterKeyColumn(
            -1
        )

        #
        # Sort using displayed text.
        #
        # This allows Type to sort alphabetically
        # without changing the actual car_type values
        # stored in the database.
        #

        self.proxy.setSortRole(
            Qt.DisplayRole
        )

        #
        # Table
        #

        self.table = QTableView()

        self.table.setModel(
            self.proxy
        )

        self.table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )

        self.table.setFocusPolicy(
            Qt.StrongFocus
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
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

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        layout.addWidget(
            self.table
        )

        #
        # Picture preview for the selected car.
        #

        picture_group = QGroupBox(
            "Selected Car Picture"
        )

        picture_layout = QHBoxLayout(
            picture_group
        )

        picture_preview_layout = QVBoxLayout()

        self.picture_car_label = QLabel(
            "No car selected"
        )

        self.picture_label = QLabel(
            "Select a car to view its picture."
        )

        self.picture_label.setAlignment(
            Qt.AlignCenter
        )

        self.picture_label.setMinimumSize(
            440,
            190
        )

        self.picture_label.setStyleSheet(
            "QLabel { background-color: white; "
            "border: 1px solid #b8b8b8; }"
        )

        picture_preview_layout.addWidget(
            self.picture_car_label
        )

        picture_preview_layout.addWidget(
            self.picture_label
        )

        picture_button_layout = QVBoxLayout()

        self.add_picture_button = QPushButton(
            "Add/Change Picture"
        )

        self.remove_picture_button = QPushButton(
            "Remove Picture"
        )

        self.add_picture_button.setEnabled(
            False
        )

        self.remove_picture_button.setEnabled(
            False
        )

        picture_button_layout.addWidget(
            self.add_picture_button
        )

        picture_button_layout.addWidget(
            self.remove_picture_button
        )

        picture_button_layout.addStretch()

        picture_layout.addLayout(
            picture_preview_layout
        )

        picture_layout.addLayout(
            picture_button_layout
        )

        layout.addWidget(
            picture_group
        )

        #
        # Signals
        #

        self.search_box.textChanged.connect(
            self.proxy.setFilterRegularExpression
        )

        self.add_button.clicked.connect(
            self.add_car
        )

        self.edit_button.clicked.connect(
            self.edit_car
        )

        self.delete_button.clicked.connect(
            self.delete_car
        )

        self.import_button.clicked.connect(
            self.import_csv
        )

        self.export_button.clicked.connect(
            self.export_csv
        )

        self.table.doubleClicked.connect(
            self.edit_car
        )

        self.table.selectionModel().selectionChanged.connect(
            self.update_car_picture
        )

        self.add_picture_button.clicked.connect(
            self.add_or_change_picture
        )

        self.remove_picture_button.clicked.connect(
            self.remove_picture
        )

        #
        # Initial load
        #

        self.refresh()

        #
        # Start the roster sorted by Car Type.
        #

        self.proxy.sort(
            3,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            3,
            Qt.AscendingOrder
        )

    #
    # Refresh when the tab becomes visible
    #

    def showEvent(self, event):

        super().showEvent(
            event
        )

        #
        # Reload the roster from the database
        # every time the user returns to the tab.
        #
        # This is important because cars can be
        # assigned, moved, or released from other
        # tabs while this model still contains
        # older Car objects.
        #

        self.refresh()

        #
        # Keep the roster sorted by Car Type.
        #

        self.proxy.sort(
            3,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            3,
            Qt.AscendingOrder
        )

    #
    # Refresh
    #

    def refresh(self):

        self.model.refresh()

        #
        # Re-evaluate the proxy model.
        #

        self.proxy.invalidate()

        #
        # Resize columns after the model changes.
        #

        self.table.resizeColumnsToContents()

        #
        # Update roster count.
        #

        total = self.model.rowCount()

        self.status_label.setText(
            f"{total} Cars"
        )

        self.update_car_picture()

    #
    # Selected car and picture helpers
    #

    def selected_car(self):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:
            return None

        source_index = self.proxy.mapToSource(
            indexes[0]
        )

        return self.model.get_car(
            source_index.row()
        )

    @staticmethod
    def picture_filename_part(value):

        return "".join(
            character
            if character.isalnum() or character in "-_"
            else "_"
            for character in str(value or "").strip()
        )

    def canonical_picture_path(self, car):

        image_directory = (
            WaybillFormRenderer._project_root()
            / WaybillFormRenderer.IMAGE_DIRECTORY
        )

        reporting_mark = self.picture_filename_part(
            car.reporting_mark
        )

        number = self.picture_filename_part(
            car.number
        )

        return (
            image_directory
            / f"{reporting_mark}_{number}.png"
        )

    def picture_paths(self, car):

        image_directory = (
            WaybillFormRenderer._project_root()
            / WaybillFormRenderer.IMAGE_DIRECTORY
        )

        if not image_directory.is_dir():
            return []

        reporting_mark = str(
            car.reporting_mark or ""
        ).strip()

        number = str(
            car.number or ""
        ).strip()

        expected_names = {
            f"{reporting_mark}_{number}.png".casefold(),
            f"{reporting_mark} {number}.png".casefold(),
            f"{reporting_mark}{number}.png".casefold(),
            self.canonical_picture_path(car).name.casefold(),
        }

        try:
            return [
                path
                for path in image_directory.iterdir()
                if path.is_file()
                and path.name.casefold() in expected_names
            ]
        except OSError:
            return []

    def update_car_picture(self, *_args):

        car = self.selected_car()

        if car is None:
            self.picture_car_label.setText(
                "No car selected"
            )
            self.picture_label.clear()
            self.picture_label.setText(
                "Select a car to view its picture."
            )
            self.picture_label.setToolTip("")
            self.add_picture_button.setEnabled(False)
            self.remove_picture_button.setEnabled(False)
            return

        car_name = (
            f"{car.reporting_mark} {car.number}"
        ).strip()

        self.picture_car_label.setText(
            car_name
        )

        self.add_picture_button.setEnabled(True)

        image_path = WaybillFormRenderer.find_car_image_path(
            car.reporting_mark,
            car.number,
        )

        if image_path is None:
            self.picture_label.clear()
            self.picture_label.setText(
                f"No picture available for {car_name}."
            )
            self.picture_label.setToolTip("")
            self.remove_picture_button.setEnabled(False)
            return

        pixmap = QPixmap(
            str(image_path)
        )

        if pixmap.isNull():
            self.picture_label.clear()
            self.picture_label.setText(
                "The picture could not be loaded."
            )
            self.picture_label.setToolTip(
                str(image_path)
            )
            self.remove_picture_button.setEnabled(False)
            return

        self.picture_label.setPixmap(
            pixmap.scaled(
                self.picture_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

        self.picture_label.setToolTip(
            str(image_path)
        )

        self.remove_picture_button.setEnabled(True)

    def add_or_change_picture(self):

        car = self.selected_car()

        if car is None:
            QMessageBox.information(
                self,
                "Car Picture",
                "Please select a car."
            )
            return

        source_filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Car Picture",
            "",
            "Image Files (*.jpg *.jpeg *.png)"
        )

        if not source_filename:
            return

        reader = QImageReader(
            source_filename
        )

        reader.setAutoTransform(
            True
        )

        image = reader.read()

        if image.isNull():
            QMessageBox.warning(
                self,
                "Car Picture",
                reader.errorString() or "The selected picture could not be read."
            )
            return

        crop_dialog = CarImageCropDialog(
            image,
            self,
        )

        if not crop_dialog.exec():
            return

        image = crop_dialog.cropped_image()

        image = image.scaled(
            QSize(2400, 1400),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        destination = self.canonical_picture_path(
            car
        )

        try:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temporary_destination = Path(
                str(destination) + ".tmp"
            )

            if not image.save(
                str(temporary_destination),
                "PNG",
            ):
                raise OSError(
                    "The converted PNG picture could not be saved."
                )

            temporary_destination.replace(
                destination
            )

            for old_path in self.picture_paths(car):
                if old_path.resolve() != destination.resolve():
                    old_path.unlink()

        except OSError as ex:
            QMessageBox.warning(
                self,
                "Car Picture",
                str(ex)
            )
            return

        self.update_car_picture()

        QMessageBox.information(
            self,
            "Car Picture",
            (
                f"The picture for {car.reporting_mark} "
                f"{car.number} was saved."
            )
        )

    def remove_picture(self):

        car = self.selected_car()

        if car is None:
            QMessageBox.information(
                self,
                "Car Picture",
                "Please select a car."
            )
            return

        image_paths = self.picture_paths(
            car
        )

        if not image_paths:
            QMessageBox.information(
                self,
                "Car Picture",
                "This car does not have a picture."
            )
            return

        result = QMessageBox.question(
            self,
            "Remove Car Picture",
            (
                f"Remove the picture for {car.reporting_mark} "
                f"{car.number}?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        try:
            for image_path in image_paths:
                image_path.unlink()
        except OSError as ex:
            QMessageBox.warning(
                self,
                "Remove Car Picture",
                str(ex)
            )
            return

        self.update_car_picture()

    #
    # Add car
    #

    def add_car(self):

        dialog = AddCarDialog(
            self
        )

        if dialog.exec():

            self.refresh()

            self.proxy.sort(
                3,
                Qt.AscendingOrder
            )

    #
    # Edit car
    #

    def edit_car(
        self,
        index=None
    ):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Edit Car",
                "Please select a car."
            )

            return

        source_index = self.proxy.mapToSource(
            indexes[0]
        )

        car = self.model.get_car(
            source_index.row()
        )

        if car is None:

            return

        dialog = AddCarDialog(
            self,
            car
        )

        if dialog.exec():

            self.refresh()

            self.proxy.sort(
                3,
                Qt.AscendingOrder
            )

    #
    # Delete car
    #

    def delete_car(self):

        indexes = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not indexes:

            QMessageBox.information(
                self,
                "Delete Car",
                "Please select a car."
            )

            return

        source_index = self.proxy.mapToSource(
            indexes[0]
        )

        car = self.model.get_car(
            source_index.row()
        )

        if car is None:

            return

        result = QMessageBox.question(
            self,
            "Delete Car",
            (
                f"Are you sure you want to delete "
                f"{car.reporting_mark} {car.number}?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:

            return

        CarService.delete(
            car.id
        )

        self.refresh()

        self.proxy.sort(
            3,
            Qt.AscendingOrder
        )

    #
    # Export CSV
    #

    def export_csv(self):

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Roster",
            "",
            "CSV Files (*.csv)"
        )

        if not filepath:

            return

        try:

            self.model.export_to_csv(
                filepath
            )

            QMessageBox.information(
                self,
                "Export Complete",
                "The car roster was exported successfully."
            )

        except Exception as ex:

            QMessageBox.warning(
                self,
                "Export Failed",
                str(ex)
            )

    #
    # Import CSV
    #

    def import_csv(self):

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Roster",
            "",
            "CSV Files (*.csv)"
        )

        if not filepath:

            return

        try:

            added, skipped = (
                self.model.import_from_csv(
                    filepath
                )
            )

        except Exception as ex:

            QMessageBox.critical(
                self,
                "Import Failed",
                str(ex)
            )

            return

        #
        # Refresh through the normal UI path.
        #

        self.refresh()

        #
        # Reapply Type sorting after import.
        #

        self.proxy.sort(
            3,
            Qt.AscendingOrder
        )

        self.table.horizontalHeader().setSortIndicator(
            3,
            Qt.AscendingOrder
        )

        total = self.model.rowCount()

        QMessageBox.information(
            self,
            "Import Complete",
            (
                f"Imported: {added}\n"
                f"Skipped: {skipped}\n\n"
                f"Roster now contains {total} cars."
            )
        )
