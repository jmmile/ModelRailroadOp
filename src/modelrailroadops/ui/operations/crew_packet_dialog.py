"""Crew-oriented paper packet. Printing never completes a move or session."""
from html import escape
import os
from pathlib import Path
import tempfile

from PySide6.QtCore import QMarginsF
from PySide6.QtGui import QFont, QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewWidget
from PySide6.QtWidgets import QDialog, QFileDialog, QHBoxLayout, QMessageBox, QPushButton, QVBoxLayout

from modelrailroadops.services.crew_packet_service import CrewPacketService


def text(value):
    return escape(str(value if value not in (None, "") else "-"))


def checks(items):
    return "".join(f"<p>&#x2610; {escape(item)}</p>" for item in items)


def table(headings, rows, empty):
    if not rows:
        return f"<p><i>{escape(empty)}</i></p>"
    return ('<table width="100%" border="1" cellspacing="0" cellpadding="5"><thead><tr>'
            + "".join(f'<th bgcolor="#eeeeee">{escape(h)}</th>' for h in headings)
            + "</tr></thead>" + "".join("<tr>" + "".join(f"<td>{text(c)}</td>" for c in row)
                                            + "</tr>" for row in rows) + "</table>")


def packet_html(packet):
    summary = packet["summary"]
    identity = f"{text(summary['name'])} | {text(summary['date'])} | Session #{summary['id']}"
    pages = []

    def page(title, body):
        pages.append(f"<h1>{escape(title)}</h1><p>{identity}<br>Prepared: {text(summary['generated_at'])} | "
                     f"Status at preparation: {text(summary['status'])}</p>{body}")

    page("CREW OPERATING CHECKLIST", "<p>Crew: ____________________ Train: ____________________</p>"
         "<p><b>Paper checkmarks do not update the application.</b> Record each physical move once, "
         "using either Switch List or the companion. This packet is a snapshot; refresh it after plan changes.</p>"
         "<h2>1. Prepare and build your train</h2>" + checks([
             "Operations Sessions: select the correct session and operating date. Run Validate Session; resolve errors and review warnings.",
             "Overview: confirm your assigned train and motive power. Review the route, train limits, and local operating instructions with the dispatcher.",
             "Freight: review waybills and destinations. If instructions are missing, have the session organizer generate car moves before printing.",
             "Use the train preparation pages to locate and arrange equipment. Pick up only cars listed at the starting location; en-route pickups stay at their origins until reached.",
             "Check physical car identities and starting tracks against Car Spotting / Car Locations. Assemble assigned passenger equipment in consist order where applicable.",
             "Switch List: select the same session, Load Switch List, then select your train. Start the session if directed; the first successful pickup can also activate a planned session.",
         ]) + "<h2>2. Work the route</h2>" + checks([
             "Follow the printed route sequence, dispatcher instructions, and actual track conditions. Review each car and exact track/spot before moving it.",
             "PICKUP: couple and physically collect the car, then select its PICKUP row and Complete Move (or confirm Pickup on the companion). Verify it appears in Cars On Train.",
             "SET-OUT: confirm the car is aboard and the destination is available and compatible. Physically spot it, then complete its SETOUT instruction. Verify it leaves Cars On Train.",
             "Mark the corresponding paper instruction after the application confirms success. If blocked, stop and resolve the warning; do not mark the move complete or manually bypass it.",
         ]) + "<h2>3. Close out</h2><p>Use the closing checklist at the end of this packet. "
         "Do not cancel a session as a substitute for completing it.</p>")

    for train in packet["trains"]:
        body = f"<h2>{text(train['name'])}</h2><p>Engineer: ____________________ Conductor: ____________________</p>"
        if not train["assigned"]:
            body += "<p><b>Warning: moves reference this train, but it is not assigned on Overview. Ask the organizer to resolve this.</b></p>"
        body += "<h2>Motive power - assigned order</h2>" + table(
            ("Order", "Locomotive", "Model"), train["locomotives"], "No locomotive assigned - confirm with the organizer.")
        body += "<h2>Passenger equipment - assigned order</h2>" + table(
            ("Order", "Car", "Type"), train["passenger_cars"], "No passenger equipment assigned.")
        body += "<h2>Route / timetable</h2>" + table(
            ("Stop", "Location", "Track", "Arrive", "Depart"), train["route"], "No route defined - confirm with the organizer.")
        body += "<p>Freight car order is determined by the crew; route sequence is work order, not consist order. "
        body += "Passenger service is performed according to the timetable; freight move counts do not track passenger stops.</p>"
        page("TRAIN PREPARATION", body)
        moves = train["moves"]
        if not moves:
            page("TRAIN WORK", f"<h2>{text(train['name'])}</h2><p>No generated freight instructions. "
                 "For freight service, ask the organizer to check waybills and generate moves. For passenger-only service, follow the timetable.</p>")
        for start in range(0, len(moves), 4):
            body = f"<h2>{text(train['name'])}</h2><p>Work in route order. Already-completed instructions are reference only - do not repeat them.</p>"
            for move in moves[start:start + 4]:
                mark = "COMPLETED - reference only" if move["move_status"] == "COMPLETED" else "&#x2610; Physical move done  &#x2610; Recorded in app"
                body += (f"<h3>Stop {text(move['route_sequence'])}: {text(move['move_type'])} - {text(move['car'])}</h3>"
                         f"<p>{mark}<br>Move #{move['car_move_id']} | Waybill #{move['waybill_id']} | Status: {text(move['move_status'])}<br>"
                         f"Type: {text(move['car_type'])} | Length: {text(move['length'])} ft<br>"
                         f"<b>Work at:</b> {text(move['instruction_location'])}<br>"
                         f"Origin: {text(move['origin'])}<br>Destination: {text(move['destination'])}<br>"
                         f"Location when printed: {text(move['current_location'])}")
                if move.get("notes") or move.get("move_notes"):
                    body += f"<br>Instructions: {text(move.get('move_notes'))} / {text(move.get('notes'))}"
                body += "</p>"
            page("FREIGHT WORK CHECKLIST", body)

    if not packet["trains"]:
        page("NO TRAINS ASSIGNED", "<p>Assign trains on Operations Sessions / Overview and prepare the work before departure.</p>")
    page("SESSION CLOSEOUT", "<h2>Before releasing your train</h2>" + checks([
        "Switch List: review Cars On Train for your train. Set out remaining cars at their authorized destinations, or coordinate unresolved work with the dispatcher.",
        "If a car must return to its pickup location: physically return it, then select it in Cars On Train and use Return Car to Pickup Location. Review the reset pickup instruction; a return is not a completed delivery.",
        "Car Spotting / Car Locations: compare physical car positions with the application. For industries confirm track and spot; for yard, staging, or interchange confirm the general track (a freight spot may not apply).",
        "Secure the train and equipment as directed by the layout owner. Record missed work, blocked tracks, and equipment issues below.",
        "Tell the session organizer your train is finished. The organizer must review ALL trains before closing the whole session.",
    ]) + "<h2>Session organizer</h2>" + checks([
        "Operations Sessions: select this session, open End-of-Session Summary, and Refresh Review. Reconcile pending moves, unfinished waybills, and cars aboard trains.",
        "Record unresolved work for planning; it is not automatically transferred to the next session. Resolve completion warnings instead of forcing completion.",
        "When ready, click Complete Session, review the summary and check its three boxes, then Continue to Complete Session and confirm.",
        "Confirm session status is COMPLETED. Make a complete ZIP backup from the Dashboard or File menu when appropriate.",
    ]) + f"<h2>Snapshot when this packet was prepared</h2><p>Completed pickups: {summary['pickups']} | "
         f"Completed set-outs: {summary['setouts']}<br>Unfinished moves: {len(summary['pending'])} | "
         f"Unfinished waybills: {len(summary['unfinished_waybills'])} | Session cars aboard: {len(summary['aboard'])}</p>"
         "<p>These printed counts do not update during operation. Use the live summary for the final review.</p>"
         "<h2>Follow-up / exceptions</h2><p>Car / location / required action: __________________________________________________</p>"
         "<p>__________________________________________________________________________</p>"
         "<p>Crew initials: __________ Organizer: __________ Finish time: __________</p>")
    return ('<html><head><style>body { font-family: Arial; font-size: 10pt; color: #111; }'
            'h1 { font-size: 18pt; } h2 { font-size: 12pt; } h3 { font-size: 11pt; }'
            'p { margin-top: 5px; margin-bottom: 8px; } th { text-align: left; }</style></head><body>'
            + '<p style="page-break-before: always;"></p>'.join(pages) + '</body></html>')


def make_printer():
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageSize(QPageSize(QPageSize.Letter))
    printer.setPageMargins(QMarginsF(13, 13, 13, 13), QPageLayout.Millimeter)
    printer.setDocName("Model Railroad Operations - Crew Packet")
    return printer


def export_pdf(document, filename):
    """Finish a PDF before replacing the user-selected destination."""
    target = Path(filename)
    descriptor, temporary = tempfile.mkstemp(suffix=".pdf", dir=target.parent)
    os.close(descriptor)
    try:
        printer = make_printer()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(temporary)
        document.print_(printer)
        with open(temporary, "rb") as stream:
            valid = stream.read(5) == b"%PDF-"
        if printer.printerState() == QPrinter.Error or not valid:
            raise OSError("The PDF could not be written. Check the destination and available disk space.")
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class CrewPacketDialog(QDialog):
    def __init__(self, session_id, parent=None):
        super().__init__(parent)
        self.session_id = session_id
        self.setWindowTitle("Crew Operating Packet - Preview / Print")
        self.resize(1000, 800)
        self.document = QTextDocument(self)
        self.document.setDefaultFont(QFont("Arial", 10))
        self.printer = make_printer()
        layout = QVBoxLayout(self)
        self.preview = QPrintPreviewWidget(self.printer, self)
        self.preview.setViewMode(QPrintPreviewWidget.AllPagesView)
        self.preview.paintRequested.connect(self.document.print_)
        layout.addWidget(self.preview)
        row = QHBoxLayout()
        for label, callback in (("Refresh Packet", self.refresh), ("Print", self.print_packet),
                                ("Save PDF", self.save_pdf), ("Close", self.reject)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            row.addWidget(button)
        layout.addLayout(row)
        self.refresh()

    def refresh(self):
        # Clear the previous document before querying so failed refreshes cannot print stale work.
        self.document.clear()
        self.packet = None
        try:
            self.packet = CrewPacketService.get_packet(self.session_id)
            self.document.setHtml(packet_html(self.packet))
        except Exception as exc:
            QMessageBox.warning(self, "Crew Packet", f"Unable to load packet: {exc}")
        self.preview.updatePreview()

    def print_packet(self):
        if not self.packet:
            return
        printer = make_printer()
        if QPrintDialog(printer, self).exec() == QDialog.Accepted:
            try:
                self.document.print_(printer)
                if printer.printerState() == QPrinter.Error:
                    raise OSError("The printer reported an error.")
            except Exception as exc:
                QMessageBox.warning(self, "Print Failed", str(exc))

    def save_pdf(self):
        if not self.packet:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save Crew Packet", "Crew-Packet.pdf", "PDF (*.pdf)")
        if not filename:
            return
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
            if Path(filename).exists() and QMessageBox.question(
                self, "Replace PDF?", f"Replace the existing file?\n{filename}",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            ) != QMessageBox.Yes:
                return
        try:
            export_pdf(self.document, filename)
        except Exception as exc:
            QMessageBox.warning(self, "Save PDF Failed", str(exc))
