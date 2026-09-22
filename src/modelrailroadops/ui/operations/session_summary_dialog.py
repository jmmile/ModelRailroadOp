"""Read-only closing review and operator checklist, before session completion."""
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout,
)

from modelrailroadops.services.operations_session_service import OperationsSessionService


CHECKS = (
    "I checked physical car positions against Car Spotting / Car Locations.",
    "I reviewed unfinished moves, waybills, and any cars still aboard trains.",
    "I recorded any follow-up work on my operations checklist.",
)


def summary_text(summary):
    lines = [
        f"END OF SESSION — {summary['name']} (#{summary['id']})",
        f"Operating date: {summary['date']} | Status: {summary['status']}",
        f"Completed: {summary['completed_at']} | Reviewed: {summary['generated_at']}",
        "",
        f"Completed pickups: {summary['pickups']} | Completed set-outs: {summary['setouts']}",
        f"Unfinished moves: {len(summary['pending'])} | Unfinished waybills: {len(summary['unfinished_waybills'])}",
        f"Session-related cars currently aboard trains: {len(summary['aboard'])}",
        "",
        "COMPLETION READINESS", summary["readiness"], "",
        "MOVE DETAILS (this session only)",
    ]
    for row in summary["moves"]:
        lines.append(f"#{row['id']} | {row['train']} | {row['car']} | {row['type']} | {row['status']} | Waybill #{row['waybill']}")
        lines.append(f"    {row['origin']} → {row['destination']}")
    if not summary["moves"]:
        lines.append("No generated freight moves.")
    lines += ["", "UNFINISHED WAYBILLS"]
    lines += [f"#{w['id']} | {w['car']} | {w['status']}" for w in summary["unfinished_waybills"]] or ["None."]
    lines += ["", "CARS CURRENTLY ABOARD TRAINS"]
    lines += [f"{c['car']} | {c['location']}" for c in summary["aboard"]] or ["None among this session's cars."]
    lines += ["", "Locations are live, not a historical end-of-session snapshot.",
              "Freight movement counts do not measure passenger service completion.",
              "Unfinished work is NOT automatically moved into another session.",
              "An arrived waybill may still be finalized by the existing Complete Session rules."]
    return "\n".join(lines)


class SessionSummaryDialog(QDialog):
    def __init__(self, session_id, parent=None, allow_complete=False):
        super().__init__(parent)
        self.session_id = session_id
        self.setWindowTitle("End-of-Session Summary & Checklist")
        self.resize(900, 650)
        layout = QVBoxLayout(self)
        note = QLabel("Review the session, then check your layout. Checkmarks apply to this review only and are not saved.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.report = QTextEdit()
        self.report.setReadOnly(True)
        layout.addWidget(self.report)
        self.checks = []
        for text in CHECKS:
            check = QCheckBox(text)
            check.toggled.connect(self.update_button)
            self.checks.append(check)
            layout.addWidget(check)
        controls = QHBoxLayout()
        refresh = QPushButton("Refresh Review")
        refresh.clicked.connect(self.refresh)
        controls.addWidget(refresh)
        self.complete_button = QPushButton("Continue to Complete Session")
        self.complete_button.setVisible(allow_complete)
        self.complete_button.clicked.connect(self.accept)
        controls.addWidget(self.complete_button)
        close = QPushButton("Close")
        close.clicked.connect(self.reject)
        controls.addWidget(close)
        layout.addLayout(controls)
        self.summary = None
        self.refresh()

    def refresh(self):
        self.summary = None
        for check in self.checks:
            check.setChecked(False)
        try:
            self.summary = OperationsSessionService.end_summary(self.session_id)
            self.report.setPlainText(summary_text(self.summary))
        except Exception as exc:
            self.report.setPlainText(f"Unable to load the session summary: {exc}")
        self.update_button()

    def update_button(self):
        self.complete_button.setEnabled(bool(self.summary and self.summary["ready"])
                                        and all(c.isChecked() for c in self.checks))
