from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QVBoxLayout,
)

from modelrailroadops.services.operations_session_train_service import (
    OperationsSessionTrainService,
)

from modelrailroadops.services.train_service import (
    TrainService,
)


class AssignOperationsSessionTrainDialog(QDialog):

    def __init__(
        self,
        operations_session_id,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.operations_session_id = (
            operations_session_id
        )

        self.setWindowTitle(
            "Assign Train to Operations Session"
        )

        self.resize(
            450,
            150
        )

        layout = QVBoxLayout(
            self
        )

        #
        # Form
        #

        form_layout = QFormLayout()

        self.train_combo = QComboBox()

        self.train_combo.setMinimumWidth(
            300
        )

        form_layout.addRow(
            "Train:",
            self.train_combo
        )

        layout.addLayout(
            form_layout
        )

        #
        # Buttons
        #

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.button_box.accepted.connect(
            self.assign_train
        )

        self.button_box.rejected.connect(
            self.reject
        )

        layout.addWidget(
            self.button_box
        )

        #
        # Load trains
        #

        self.load_trains()

    #
    # Load trains
    #

    def load_trains(
        self,
    ):

        self.train_combo.clear()

        trains = (
            TrainService.get_all()
        )

        for train in trains:

            display_text = (
                self.get_train_display_text(
                    train
                )
            )

            self.train_combo.addItem(
                display_text,
                train.id,
            )

        if self.train_combo.count() == 0:

            self.train_combo.addItem(
                "No trains available",
                None,
            )

            self.train_combo.setEnabled(
                False
            )

            self.button_box.button(
                QDialogButtonBox.StandardButton.Ok
            ).setEnabled(
                False
            )

    #
    # Train display text
    #

    @staticmethod
    def get_train_display_text(
        train,
    ):

        train_number = (
            getattr(
                train,
                "train_number",
                None,
            )
        )

        if train_number is None:

            train_number = (
                getattr(
                    train,
                    "number",
                    None,
                )
            )

        if train_number is None:

            train_number = (
                getattr(
                    train,
                    "name",
                    None,
                )
            )

        if train_number is None:

            train_number = (
                f"Train {train.id}"
            )

        train_name = (
            getattr(
                train,
                "name",
                None,
            )
        )

        if train_name is None:

            train_name = (
                getattr(
                    train,
                    "description",
                    None,
                )
            )

        if (
            train_name
            and str(train_name)
            != str(train_number)
        ):

            return (
                f"{train_number} - "
                f"{train_name}"
            )

        return str(
            train_number
        )

    #
    # Assign Train
    #

    def assign_train(
        self,
    ):

        if self.operations_session_id is None:

            QMessageBox.warning(
                self,
                "Assign Train",
                "No Operations Session was specified.",
            )

            return

        train_id = (
            self.train_combo.currentData()
        )

        if train_id is None:

            QMessageBox.warning(
                self,
                "Assign Train",
                "Please select a train.",
            )

            return

        if (
            OperationsSessionTrainService.exists(
                self.operations_session_id,
                train_id,
            )
        ):

            QMessageBox.warning(
                self,
                "Assign Train",
                (
                    "This train is already "
                    "assigned to the Operations Session."
                ),
            )

            return

        success, result = (
            OperationsSessionTrainService.create(
                self.operations_session_id,
                train_id,
            )
        )

        if not success:

            QMessageBox.warning(
                self,
                "Assign Train",
                str(result),
            )

            return

        self.accept()