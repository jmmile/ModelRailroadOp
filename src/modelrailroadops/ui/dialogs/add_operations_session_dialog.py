from datetime import date

from PySide6.QtCore import QDate

from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from modelrailroadops.services.operations_session_service import (
    OperationsSessionService,
)


class AddOperationsSessionDialog(QDialog):

    def __init__(
        self,
        parent=None,
        operations_session=None,
    ):

        super().__init__(
            parent
        )

        self.operations_session = (
            operations_session
        )

        if operations_session is None:

            self.setWindowTitle(
                "Add Operations Session"
            )

        else:

            self.setWindowTitle(
                "Edit Operations Session"
            )

        self.resize(
            500,
            350,
        )

        layout = QVBoxLayout(
            self
        )

        form = QFormLayout()

        #
        # Session name
        #

        self.name_edit = QLineEdit()

        self.name_edit.setPlaceholderText(
            "Example: Portland Division - August 2026"
        )

        form.addRow(
            "Session Name:",
            self.name_edit,
        )

        #
        # Session date
        #

        self.date_edit = QDateEdit()

        self.date_edit.setCalendarPopup(
            True
        )

        self.date_edit.setDisplayFormat(
            "yyyy-MM-dd"
        )

        today = date.today()

        self.date_edit.setDate(
            QDate(
                today.year,
                today.month,
                today.day,
            )
        )

        form.addRow(
            "Operating Date:",
            self.date_edit,
        )

        #
        # Notes
        #

        self.notes_edit = QTextEdit()

        self.notes_edit.setPlaceholderText(
            "Optional operational notes..."
        )

        self.notes_edit.setMaximumHeight(
            120
        )

        form.addRow(
            "Notes:",
            self.notes_edit,
        )

        layout.addLayout(
            form
        )

        #
        # Buttons
        #

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        layout.addWidget(
            self.buttons
        )

        #
        # Signals
        #

        self.buttons.accepted.connect(
            self.save
        )

        self.buttons.rejected.connect(
            self.reject
        )

        #
        # Load existing session
        #

        if operations_session is not None:

            self.load_existing_session()

    #
    # Load Existing Session
    #

    def load_existing_session(
        self,
    ):

        self.name_edit.setText(
            self.operations_session.name
            or ""
        )

        session_date = (
            self.operations_session.session_date
        )

        if session_date is not None:

            self.date_edit.setDate(
                QDate(
                    session_date.year,
                    session_date.month,
                    session_date.day,
                )
            )

        self.notes_edit.setPlainText(
            self.operations_session.notes
            or ""
        )

    #
    # Save
    #

    def save(
        self,
    ):

        name = (
            self.name_edit.text().strip()
        )

        if not name:

            QMessageBox.warning(
                self,
                "Operations Session",
                "Please enter a session name.",
            )

            return

        qdate = (
            self.date_edit.date()
        )

        session_date = date(
            qdate.year(),
            qdate.month(),
            qdate.day(),
        )

        notes = (
            self.notes_edit
            .toPlainText()
            .strip()
            or None
        )

        #
        # Create
        #

        if self.operations_session is None:

            success, result = (
                OperationsSessionService.create(
                    name=name,
                    session_date=session_date,
                    notes=notes,
                )
            )

            if not success:

                QMessageBox.warning(
                    self,
                    "Add Operations Session",
                    str(result),
                )

                return

        #
        # Edit
        #

        else:

            success, result = (
                OperationsSessionService.update(
                    session_id=(
                        self.operations_session.id
                    ),
                    name=name,
                    session_date=session_date,
                    notes=notes,
                )
            )

            if not success:

                QMessageBox.warning(
                    self,
                    "Edit Operations Session",
                    str(result),
                )

                return

        self.accept()