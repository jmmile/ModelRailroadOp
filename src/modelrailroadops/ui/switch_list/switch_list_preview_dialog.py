from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from modelrailroadops.services.switch_list_service import (
    SwitchListService,
)


class SwitchListPreviewDialog(QDialog):
    """
    Preview and print an Operations Session switch list.

    The preview may represent either:

        All Trains in the Operations Session

    or:

        One selected Train

    The displayed and printed rows are generated from the
    same CarMove-driven switch-list data used by the main
    Switch List table.
    """

    def __init__(
        self,
        operations_session_id,
        session_name,
        session_date=None,
        train_id=None,
        train_name=None,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.operations_session_id = (
            operations_session_id
        )

        self.session_name = (
            session_name
        )

        self.session_date = (
            session_date
        )

        self.train_id = (
            train_id
        )

        self.train_name = (
            train_name
            or ""
        )

        self.setWindowTitle(
            "Switch List Preview"
        )

        self.resize(
            1000,
            750,
        )

        layout = QVBoxLayout(
            self
        )

        #
        # Title
        #

        self.title_label = QLabel(
            "SWITCH LIST"
        )

        title_font = QFont()

        title_font.setBold(
            True
        )

        title_font.setPointSize(
            18
        )

        self.title_label.setFont(
            title_font
        )

        self.title_label.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.title_label
        )

        #
        # Session / Train description
        #

        session_text = (
            f"Operations Session: "
            f"{self.session_name}"
        )

        if self.session_date is not None:
            session_text += (
                f"    Operating Date: "
                f"{self.session_date}"
            )

        if self.train_id is not None:
            display_train_name = (
                self.train_name
                or f"Train {self.train_id}"
            )

            session_text += (
                f"    Train: "
                f"{display_train_name}"
            )

        else:
            session_text += (
                "    Train: All Trains"
            )

        self.session_label = QLabel(
            session_text
        )

        self.session_label.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.session_label
        )

        #
        # Preview area
        #

        self.preview_text = QTextEdit()

        self.preview_text.setReadOnly(
            True
        )

        self.preview_text.setAcceptRichText(
            True
        )

        preview_font = QFont(
            "Arial"
        )

        preview_font.setPointSize(
            10
        )

        self.preview_text.setFont(
            preview_font
        )

        layout.addWidget(
            self.preview_text
        )

        #
        # Buttons
        #

        button_layout = QHBoxLayout()

        self.print_button = QPushButton(
            "Print"
        )

        self.close_button = QPushButton(
            "Close"
        )

        button_layout.addWidget(
            self.print_button
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.close_button
        )

        layout.addLayout(
            button_layout
        )

        #
        # Signals
        #

        self.print_button.clicked.connect(
            self.print_switch_list
        )

        self.close_button.clicked.connect(
            self.accept
        )

        #
        # Initial preview
        #

        self.load_preview()

    #
    # Escape HTML
    #

    @staticmethod
    def escape_html(
        value,
    ):
        if value is None:
            return ""

        return (
            str(value)
            .replace(
                "&",
                "&amp;",
            )
            .replace(
                "<",
                "&lt;",
            )
            .replace(
                ">",
                "&gt;",
            )
            .replace(
                '"',
                "&quot;",
            )
        )

    #
    # Load Preview
    #

    def load_preview(
        self,
    ):
        rows = (
            SwitchListService.get_switch_list_rows(
                self.operations_session_id,
                train_id=self.train_id,
            )
        )

        pickup_rows = (
            SwitchListService.get_pickup_rows(
                self.operations_session_id,
                train_id=self.train_id,
            )
        )

        setout_rows = (
            SwitchListService.get_setout_rows(
                self.operations_session_id,
                train_id=self.train_id,
            )
        )

        train_names = {
            row.get(
                "train"
            )
            for row in rows
            if row.get(
                "train"
            )
        }

        session_name = (
            self.escape_html(
                self.session_name
            )
        )

        session_date = ""

        if self.session_date is not None:
            session_date = (
                "&nbsp;&nbsp;&nbsp;&nbsp;"
                "<b>Operating Date:</b> "
                f"{self.escape_html(self.session_date)}"
            )

        train_text = ""

        if self.train_id is None:
            train_text = (
                "&nbsp;&nbsp;&nbsp;&nbsp;"
                "<b>Train:</b> All Trains"
            )

        else:
            display_train_name = (
                self.train_name
                or f"Train {self.train_id}"
            )

            train_text = (
                "&nbsp;&nbsp;&nbsp;&nbsp;"
                "<b>Train:</b> "
                f"{self.escape_html(display_train_name)}"
            )

        html = [
            """
            <html>
            <head>
            <style>
            body {
                font-family: Arial, sans-serif;
                font-size: 10pt;
                margin: 0;
            }

            h1 {
                text-align: center;
                font-size: 18pt;
                margin-bottom: 4px;
            }

            .session {
                text-align: center;
                font-size: 10pt;
                margin-bottom: 14px;
            }

            .summary {
                font-size: 10pt;
                margin-bottom: 12px;
            }

            h2 {
                font-size: 13pt;
                margin-top: 16px;
                margin-bottom: 6px;
                border-bottom: 1px solid #777;
                padding-bottom: 3px;
            }

            h3 {
                font-size: 11pt;
                margin-top: 12px;
                margin-bottom: 4px;
                padding: 4px;
                background-color: #eee;
                border: 1px solid #999;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
                margin-bottom: 8px;
            }

            th {
                background-color: #e6e6e6;
                border: 1px solid #777;
                padding: 4px;
                font-weight: bold;
                text-align: left;
            }

            td {
                border: 1px solid #999;
                padding: 4px;
                vertical-align: top;
                word-wrap: break-word;
            }

            .delivered {
                width: 8%;
                text-align: center;
                font-size: 14pt;
            }

            .car {
                width: 13%;
            }

            .type {
                width: 14%;
            }

            .length {
                width: 6%;
                text-align: center;
            }

            .destination {
                width: 21%;
            }

            .track {
                width: 12%;
            }

            .spot {
                width: 6%;
                text-align: center;
            }

            .origin {
                width: 41%;
            }

            .empty {
                padding: 6px;
                font-style: italic;
            }

            .footer {
                margin-top: 12px;
                border-top: 1px solid #777;
                padding-top: 5px;
                font-size: 9pt;
            }
            </style>
            </head>
            <body>
            """,
            "<h1>SWITCH LIST</h1>",
            (
                '<div class="session">'
                "<b>Operations Session:</b> "
                f"{session_name}"
                f"{session_date}"
                f"{train_text}"
                "</div>"
            ),
            (
                '<div class="summary">'
                f"<b>Total Moves:</b> {len(rows)}"
                "&nbsp;&nbsp;&nbsp;&nbsp;"
                f"<b>Trains:</b> {len(train_names)}"
                "&nbsp;&nbsp;&nbsp;&nbsp;"
                f"<b>Pickups:</b> {len(pickup_rows)}"
                "&nbsp;&nbsp;&nbsp;&nbsp;"
                f"<b>Set-outs:</b> {len(setout_rows)}"
                "</div>"
            ),
            "<h2>PICKUPS</h2>",
            (
                self.build_pickup_tables(
                    pickup_rows
                )
                if pickup_rows
                else (
                    '<div class="empty">'
                    "No industry pickups."
                    "</div>"
                )
            ),
            "<h2>SET-OUTS</h2>",
            (
                self.build_setout_tables(
                    setout_rows
                )
                if setout_rows
                else (
                    '<div class="empty">'
                    "No set-outs."
                    "</div>"
                )
            ),
            (
                '<div class="footer">'
                "Model Railroad Operations"
                "</div>"
            ),
            "</body></html>",
        ]

        self.preview_text.setHtml(
            "".join(
                html
            )
        )

    #
    # Build display location
    #

    def _location(
        self,
        row,
        prefix,
        fallback,
    ):
        industry = (
            row.get(
                f"{prefix}_industry",
                "",
            )
            or ""
        )

        track = (
            row.get(
                f"{prefix}_track",
                "",
            )
            or ""
        )

        spot = (
            row.get(
                f"{prefix}_spot",
                "",
            )
            or ""
        )

        parts = [
            industry
        ]

        if track:
            parts.append(
                f"Track {track}"
            )

        if spot:
            parts.append(
                f"Spot {spot}"
            )

        return (
            " - ".join(
                part
                for part in parts
                if part
            )
            or fallback
        )

    #
    # Build Pickup tables
    #

    def build_pickup_tables(
        self,
        rows,
    ):
        return self._build_grouped_tables(
            rows,
            lambda row: self._location(
                row,
                "origin",
                (
                    row.get(
                        "origin_location",
                        "",
                    )
                    or "Unknown Location"
                ),
            ),
            "pickup",
        )

    #
    # Build Setout tables
    #

    def build_setout_tables(
        self,
        rows,
    ):
        return self._build_grouped_tables(
            rows,
            lambda row: self._location(
                row,
                "destination",
                "Unknown Destination",
            ),
            "setout",
        )

    #
    # Build grouped tables
    #

    def _build_grouped_tables(
        self,
        rows,
        location_for_row,
        kind,
    ):
        html = []

        current_group = None

        for row in rows:
            location = (
                location_for_row(
                    row
                )
            )

            train = (
                row.get(
                    "train"
                )
                or "Train Not Generated"
            )

            route_sequence = (
                row.get(
                    (
                        "pickup_sequence"
                        if kind == "pickup"
                        else "setout_sequence"
                    )
                )
            )

            group = (
                train,
                route_sequence,
                location,
            )

            if group != current_group:
                if current_group is not None:
                    html.append(
                        "</tbody></table>"
                    )

                current_group = (
                    group
                )

                stop_text = ""

                if route_sequence is not None:
                    stop_text = (
                        f"Stop {route_sequence}: "
                    )

                heading = (
                    f"{train} — "
                    f"{stop_text}"
                    f"{location}"
                )

                html.append(
                    (
                        "<h3>"
                        f"{self.escape_html(heading)}"
                        "</h3>"
                    )
                )

                html.append(
                    self._table_start(
                        kind
                    )
                )

            if kind == "pickup":
                html.append(
                    self.build_pickup_row(
                        row
                    )
                )

            else:
                html.append(
                    self.build_setout_row(
                        row
                    )
                )

        if current_group is not None:
            html.append(
                "</tbody></table>"
            )

        return "".join(
            html
        )

    #
    # Table header
    #

    @staticmethod
    def _table_start(
        kind,
    ):
        common_columns = (
            '<col class="delivered">'
            '<col class="car">'
            '<col class="type">'
            '<col class="length">'
        )

        if kind == "pickup":
            columns = (
                common_columns
                + '<col class="destination">'
                + '<col class="track">'
                + '<col class="spot">'
            )

            headings = (
                '<th class="delivered">Done</th>'
                '<th class="car">Car</th>'
                '<th class="type">Type</th>'
                '<th class="length">Len</th>'
                '<th class="destination">Destination</th>'
                '<th class="track">Track</th>'
                '<th class="spot">Spot</th>'
            )

        else:
            columns = (
                common_columns
                + '<col class="origin">'
            )

            headings = (
                '<th class="delivered">Done</th>'
                '<th class="car">Car</th>'
                '<th class="type">Type</th>'
                '<th class="length">Len</th>'
                '<th class="origin">Origin</th>'
            )

        return (
            "<table>"
            f"<colgroup>{columns}</colgroup>"
            "<thead>"
            f"<tr>{headings}</tr>"
            "</thead>"
            "<tbody>"
        )

    #
    # Table cell
    #

    def _cell(
        self,
        css_class,
        value,
    ):
        return (
            f'<td class="{css_class}">'
            f"{self.escape_html(value or '')}"
            "</td>"
        )

    #
    # Paper checkbox
    #

    @staticmethod
    def _delivered_cell():
        """
        A blank paper checkbox.

        This is not a database control.
        """

        return (
            '<td class="delivered">'
            "&#9744;"
            "</td>"
        )

    #
    # Pickup row
    #

    def build_pickup_row(
        self,
        row,
    ):
        return (
            "<tr>"
            + "".join(
                [
                    self._delivered_cell(),
                    self._cell(
                        "car",
                        row.get(
                            "car"
                        ),
                    ),
                    self._cell(
                        "type",
                        row.get(
                            "car_type"
                        ),
                    ),
                    self._cell(
                        "length",
                        row.get(
                            "length"
                        ),
                    ),
                    self._cell(
                        "destination",
                        row.get(
                            "destination"
                        ),
                    ),
                    self._cell(
                        "track",
                        row.get(
                            "destination_track"
                        ),
                    ),
                    self._cell(
                        "spot",
                        row.get(
                            "destination_spot"
                        ),
                    ),
                ]
            )
            + "</tr>"
        )

    #
    # Setout row
    #

    def build_setout_row(
        self,
        row,
    ):
        return (
            "<tr>"
            + "".join(
                [
                    self._delivered_cell(),
                    self._cell(
                        "car",
                        row.get(
                            "car"
                        ),
                    ),
                    self._cell(
                        "type",
                        row.get(
                            "car_type"
                        ),
                    ),
                    self._cell(
                        "length",
                        row.get(
                            "length"
                        ),
                    ),
                    self._cell(
                        "origin",
                        row.get(
                            "origin"
                        ),
                    ),
                ]
            )
            + "</tr>"
        )

    #
    # Print
    #

    def print_switch_list(
        self,
    ):
        printer = QPrinter(
            QPrinter.HighResolution
        )

        if self.train_id is None:
            document_name = (
                "Model Railroad Operations "
                "Switch List"
            )

        else:
            display_train_name = (
                self.train_name
                or f"Train {self.train_id}"
            )

            document_name = (
                "Model Railroad Operations "
                f"Switch List - {display_train_name}"
            )

        printer.setDocName(
            document_name
        )

        print_dialog = QPrintDialog(
            printer,
            self,
        )

        if (
            print_dialog.exec()
            != QPrintDialog.Accepted
        ):
            return

        document = QTextDocument()

        document.setHtml(
            self.preview_text.toHtml()
        )

        default_font = QFont(
            "Arial"
        )

        default_font.setPointSize(
            10
        )

        document.setDefaultFont(
            default_font
        )

        try:
            document.print_(
                printer
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Print Error",
                (
                    "The switch list could not be printed."
                    f"\n\n{error}"
                ),
            )

            return

        QMessageBox.information(
            self,
            "Print Complete",
            "The switch list was sent to the printer.",
        )