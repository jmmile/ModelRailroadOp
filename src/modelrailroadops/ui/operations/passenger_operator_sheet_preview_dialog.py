from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)

from modelrailroadops.services.operations_session_train_locomotive_service import (
    OperationsSessionTrainLocomotiveService,
)
from modelrailroadops.services.operations_session_train_passenger_car_service import (
    OperationsSessionTrainPassengerCarService,
)
from modelrailroadops.services.train_route_service import TrainRouteService


class PassengerOperatorSheetPreviewDialog(QDialog):
    """Read-only on-screen operator sheet for one passenger train assignment."""

    def __init__(
        self,
        operations_session_train_id,
        train,
        session_name,
        session_date=None,
        parent=None,
    ):
        super().__init__(parent)

        self.operations_session_train_id = operations_session_train_id
        self.train = train
        self.session_name = session_name
        self.session_date = session_date

        self.setWindowTitle("Passenger Train Operator Sheet Preview")
        self.resize(1000, 750)

        layout = QVBoxLayout(self)

        title = QLabel("PASSENGER TRAIN OPERATOR SHEET")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setAcceptRichText(True)
        layout.addWidget(self.preview_text)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.refresh_preview()

    @staticmethod
    def _time_text(value):
        return value.strftime("%I:%M %p").lstrip("0") if value else "—"

    @staticmethod
    def _cell(value):
        return f"<td>{escape(str(value if value not in (None, '') else '—'))}</td>"

    @staticmethod
    def _table(title, headings, rows, empty_message):
        if rows:
            body = "".join(
                "<tr>" + "".join(PassengerOperatorSheetPreviewDialog._cell(value) for value in row) + "</tr>"
                for row in rows
            )
            content = (
                "<table><thead><tr>"
                + "".join(f"<th>{escape(heading)}</th>" for heading in headings)
                + f"</tr></thead><tbody>{body}</tbody></table>"
            )
        else:
            content = f'<div class="empty">{escape(empty_message)}</div>'

        return f"<h2>{escape(title)}</h2>{content}"

    def refresh_preview(self):
        locomotives = (
            OperationsSessionTrainLocomotiveService.get_by_operations_session_train(
                self.operations_session_train_id
            )
        )
        passenger_cars = (
            OperationsSessionTrainPassengerCarService.get_by_operations_session_train(
                self.operations_session_train_id
            )
        )
        routes = TrainRouteService.get_by_train(self.train.id)

        locomotive_rows = []
        for assignment in locomotives:
            locomotive = assignment.locomotive
            if locomotive is not None:
                locomotive_rows.append(
                    (
                        assignment.sequence,
                        f"{locomotive.reporting_mark} {locomotive.number}",
                        locomotive.model,
                        locomotive.locomotive_type,
                    )
                )

        passenger_car_rows = []
        for assignment in passenger_cars:
            passenger_car = assignment.passenger_car
            if passenger_car is not None:
                passenger_car_rows.append(
                    (
                        assignment.sequence,
                        f"{passenger_car.reporting_mark} {passenger_car.number}",
                        passenger_car.name,
                        passenger_car.equipment_type,
                    )
                )

        route_rows = [
            (
                route.sequence,
                route.operating_location.name if route.operating_location else route.location,
                route.operating_track.name if route.operating_track else None,
                self._time_text(route.arrival_time),
                self._time_text(route.departure_time),
            )
            for route in routes
        ]

        train_identity = " - ".join(
            part for part in (self.train.symbol, self.train.name) if part
        )
        session_date = f" | Operating Date: {self.session_date}" if self.session_date else ""

        style = """
            body { font-family: Arial; font-size: 10pt; color: #111; }
            h1 { text-align: center; font-size: 16pt; margin-bottom: 4px; }
            .session { text-align: center; margin-bottom: 14px; }
            h2 { font-size: 12pt; margin: 16px 0 5px 0; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #555; padding: 5px; text-align: left; }
            th { background: #e8e8e8; }
            .empty { color: #555; font-style: italic; }
        """

        html = [
            f"<html><head><style>{style}</style></head><body>",
            f"<h1>{escape(train_identity)}</h1>",
            '<div class="session">',
            f"Operations Session: {escape(str(self.session_name))}",
            escape(session_date),
            "</div>",
            self._table(
                "Locomotive Consist",
                ("Sequence", "Locomotive", "Model", "Type"),
                locomotive_rows,
                "No locomotives are assigned.",
            ),
            self._table(
                "Passenger-Car Consist",
                ("Sequence", "Car", "Name", "Type"),
                passenger_car_rows,
                "No passenger cars are assigned.",
            ),
            self._table(
                "Route and Timetable",
                ("Stop", "Location", "Track", "Arrival", "Departure"),
                route_rows,
                "No route stops are defined.",
            ),
            "</body></html>",
        ]
        self.preview_text.setHtml("".join(html))
