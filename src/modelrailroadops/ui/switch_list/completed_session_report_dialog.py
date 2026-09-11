from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from modelrailroadops.services.switch_list_service import (
    SwitchListService,
)


class CompletedSessionReportDialog(QDialog):
    """Preview and print the final results of an Operations Session."""

    def __init__(
        self,
        operations_session_id,
        train_id=None,
        parent=None,
    ):
        super().__init__(parent)
        self.operations_session_id = operations_session_id
        self.train_id = train_id
        self.report = SwitchListService.get_completed_session_report(
            operations_session_id,
            train_id=train_id,
        )

        self.setWindowTitle("Completed Session Report")
        self.resize(1000, 750)

        layout = QVBoxLayout(self)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setAcceptRichText(True)
        layout.addWidget(self.preview_text)

        button_layout = QHBoxLayout()
        self.print_button = QPushButton("Print")
        self.close_button = QPushButton("Close")
        button_layout.addWidget(self.print_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.print_button.clicked.connect(self.print_report)
        self.close_button.clicked.connect(self.accept)
        self.load_report()

    @staticmethod
    def escape_html(value):
        if value is None:
            return ""
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def load_report(self):
        if self.report is None:
            self.preview_text.setPlainText(
                "The Operations Session could not be found."
            )
            self.print_button.setEnabled(False)
            return

        report = self.report
        completion = (
            self.escape_html(report["completed_at"])
            if report["completed_at"] is not None
            else "Not recorded"
        )
        train_text = (
            ", ".join(report["trains"])
            if report["trains"]
            else "No trains"
        )

        car_rows = []
        for car in report["cars"]:
            location_class = "on-train" if car["on_train"] else ""
            car_rows.append(
                "<tr>"
                f"<td>{self.escape_html(car['car'])}</td>"
                f"<td>{self.escape_html(car['car_type'])}</td>"
                f"<td>{self.escape_html(car['train'])}</td>"
                f'<td class="{location_class}">'
                f"{self.escape_html(car['final_location'])}</td>"
                "</tr>"
            )

        if not car_rows:
            car_rows.append(
                '<tr><td colspan="4"><i>'
                'No freight cars were recorded.'
                '</i></td></tr>'
            )

        warning = ""
        if report["on_train_count"]:
            warning = (
                '<div class="warning">Warning: '
                f"{report['on_train_count']} car(s) are still recorded "
                "aboard a train.</div>"
            )

        html = f"""
        <html><head><style>
        body {{ font-family: Arial, sans-serif; font-size: 10pt; }}
        h1 {{ text-align: center; font-size: 18pt; margin-bottom: 4px; }}
        .session {{ text-align: center; margin-bottom: 14px; }}
        .summary {{ border: 1px solid #777; background: #f3f3f3;
                    padding: 8px; margin-bottom: 12px; }}
        .warning {{ color: #9c2f00; font-weight: bold; margin: 8px 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #e6e6e6; border: 1px solid #777;
              padding: 5px; text-align: left; }}
        td {{ border: 1px solid #999; padding: 5px; }}
        .on-train {{ background: #f8d7da; font-weight: bold; }}
        .footer {{ margin-top: 12px; border-top: 1px solid #777;
                   padding-top: 5px; font-size: 9pt; }}
        </style></head><body>
        <h1>COMPLETED SESSION REPORT</h1>
        <div class="session">
        <b>Operations Session:</b> {self.escape_html(report['session_name'])}
        &nbsp;&nbsp;&nbsp; <b>Date:</b> {self.escape_html(report['session_date'])}
        &nbsp;&nbsp;&nbsp; <b>Status:</b> {self.escape_html(report['session_status'])}
        <br><b>Completed:</b> {completion}
        <br><b>Trains:</b> {self.escape_html(train_text)}
        </div>
        <div class="summary">
        <b>Total Moves:</b> {report['total_moves']}&nbsp;&nbsp;&nbsp;
        <b>Pickups:</b> {report['pickup_count']}&nbsp;&nbsp;&nbsp;
        <b>Set-outs:</b> {report['setout_count']}&nbsp;&nbsp;&nbsp;
        <b>Completed:</b> {report['completed_count']}&nbsp;&nbsp;&nbsp;
        <b>Pending:</b> {report['pending_count']}&nbsp;&nbsp;&nbsp;
        <b>Returns:</b> {report['return_count']}
        </div>
        {warning}
        <h2>FINAL CAR LOCATIONS</h2>
        <table>
        <thead><tr><th>Car</th><th>Type</th><th>Train</th>
        <th>Final Location</th></tr></thead>
        <tbody>{''.join(car_rows)}</tbody>
        </table>
        <div class="footer">Model Railroad Operations</div>
        </body></html>
        """
        self.preview_text.setHtml(html)

    def print_report(self):
        if self.report is None:
            return

        printer = QPrinter(QPrinter.HighResolution)
        printer.setDocName(
            "Model Railroad Operations - Completed Session Report"
        )
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() != QPrintDialog.Accepted:
            return

        document = QTextDocument()
        document.setHtml(self.preview_text.toHtml())
        default_font = QFont("Arial")
        default_font.setPointSize(10)
        document.setDefaultFont(default_font)

        try:
            document.print_(printer)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Print Error",
                f"The completed-session report could not be printed.\n\n{error}",
            )
