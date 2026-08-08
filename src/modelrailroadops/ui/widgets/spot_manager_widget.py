from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QPushButton,
    QLabel,
    QMessageBox,
    QHeaderView,
    QCheckBox,
    QAbstractItemView,
)

from PySide6.QtCore import Qt

from modelrailroadops.services.car_location_service import (
    CarLocationService,
)

from modelrailroadops.ui.models.spot_manager_table_model import (
    SpotManagerTableModel,
)

from modelrailroadops.ui.dialogs.assign_car_dialog import (
    AssignCarDialog,
)

from modelrailroadops.ui.dialogs.edit_spot_dialog import (
    EditSpotDialog,
)

from modelrailroadops.ui.styles import (
    TABLE_SELECTION_STYLE,
)



class SpotManagerWidget(QWidget):
    """
    Manage spot occupancy, restrictions,
    and car assignments.
    """

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(parent)


        layout = QVBoxLayout(self)


        layout.addWidget(
            QLabel(
                "Spot Occupancy - Configure Restrictions and Assign Cars"
            )
        )


        #
        # Filter
        #

        self.violation_filter = QCheckBox(
            "Show Violations Only"
        )

        layout.addWidget(
            self.violation_filter
        )


        #
        # Table
        #

        self.table = QTableView()


        self.table.setStyleSheet(
            TABLE_SELECTION_STYLE
        )


        self.model = SpotManagerTableModel()


        self.table.setModel(
            self.model
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
        # Buttons
        #

        button_layout = QHBoxLayout()


        self.assign_button = QPushButton(
            "Assign Car"
        )

        self.move_button = QPushButton(
            "Move Car"
        )

        self.remove_button = QPushButton(
            "Remove Car"
        )

        self.edit_button = QPushButton(
            "Edit Restriction"
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )


        button_layout.addWidget(
            self.assign_button
        )

        button_layout.addWidget(
            self.move_button
        )

        button_layout.addWidget(
            self.remove_button
        )

        button_layout.addWidget(
            self.edit_button
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.refresh_button
        )


        layout.addLayout(
            button_layout
        )


        #
        # Signals
        #

        self.assign_button.clicked.connect(
            self.assign_car
        )

        self.move_button.clicked.connect(
            self.move_car
        )

        self.remove_button.clicked.connect(
            self.remove_car
        )

        self.edit_button.clicked.connect(
            self.edit_spot
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        self.violation_filter.stateChanged.connect(
            self.filter_changed
        )

        self.table.selectionModel().selectionChanged.connect(
            self.selection_changed
        )


        self.selection_changed()



    def filter_changed(
        self,
        state
    ):

        self.model.set_violation_filter(
            state == Qt.Checked.value
        )

        self.selection_changed()



    def get_selected_row(self):

        index = self.table.currentIndex()


        if not index.isValid():

            return None


        return self.model.rows[
            index.row()
        ]



    def selection_changed(self, *args):

        row = self.get_selected_row()


        if row is None:

            self.assign_button.setEnabled(False)
            self.move_button.setEnabled(False)
            self.remove_button.setEnabled(False)
            self.edit_button.setEnabled(False)

            return


        occupied = (
            row["car_id"] is not None
        )


        self.assign_button.setEnabled(
            not occupied
        )

        self.move_button.setEnabled(
            occupied
        )

        self.remove_button.setEnabled(
            occupied
        )

        self.edit_button.setEnabled(
            True
        )



    def assign_car(self):

        row = self.get_selected_row()

        if row is None:
            return


        dialog = AssignCarDialog(
            spot_id=row["spot_id"],
            parent=self,
        )


        if dialog.exec():

            self.refresh()



    def move_car(self):

        row = self.get_selected_row()

        if row is None:
            return


        car_id = row["car_id"]


        if car_id is None:
            return


        dialog = AssignCarDialog(
            car_id=car_id,
            parent=self
        )


        if dialog.exec():

            new_spot_id = getattr(
                dialog,
                "selected_spot_id",
                None
            )


            if new_spot_id is None:
                return


            result = CarLocationService.move_car(
                car_id,
                new_spot_id
            )


            if result:

                self.refresh()

            else:

                QMessageBox.warning(
                    self,
                    "Move Failed",
                    "Unable to move car."
                )



    def remove_car(self):

        row = self.get_selected_row()

        if row is None:
            return


        car_id = row["car_id"]

        if car_id is None:
            return


        answer = QMessageBox.question(
            self,
            "Remove Car",
            (
                f"Remove {row['car']} from "
                f"{row['industry']} - "
                f"{row['track']} "
                f"Spot {row['spot']}?"
            )
        )


        if answer != QMessageBox.Yes:
            return


        result = CarLocationService.clear_car_location(
            car_id
        )


        if result:

            self.refresh()

        else:

            QMessageBox.warning(
                self,
                "Remove Failed",
                "Unable to remove car."
            )



    def edit_spot(self):

        row = self.get_selected_row()

        if row is None:
            return


        dialog = EditSpotDialog(
            row["spot_id"],
            self,
        )


        if dialog.exec():

            self.refresh()



    def refresh(self):

        self.model.load_data()


        if self.violation_filter.isChecked():

            self.model.set_violation_filter(
                True
            )


        self.table.resizeColumnsToContents()

        self.selection_changed()