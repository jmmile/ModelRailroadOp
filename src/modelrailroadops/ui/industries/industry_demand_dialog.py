from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.services.industry_demand_service import (
    IndustryDemandService,
)


class IndustryDemandDialog(QDialog):
    """Show open industry spots and generate matched-car waybills."""

    def __init__(self, parent=None, selected_spot_id=None):
        super().__init__(parent)
        self.demands = []
        self.selected_spot_id = selected_spot_id
        self.focused_demand = None
        self.setWindowTitle(
            "Matching Cars" if selected_spot_id is not None
            else "Industry Demand"
        )
        self.resize(950, 560)
        layout = QVBoxLayout(self)
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Operations Session"))
        self.session_combo = QComboBox()
        self.session_combo.addItem("No Operations Session", None)
        with SessionLocal() as session:
            sessions = session.execute(
                select(OperationsSession)
                .where(OperationsSession.status == "PLANNED")
                .order_by(OperationsSession.session_date.desc())
            ).scalars().all()
            for item in sessions:
                self.session_combo.addItem(item.name, item.id)
        controls.addWidget(self.session_combo)
        controls.addStretch()
        self.generate_button = QPushButton("Generate Waybill")
        self.refresh_button = QPushButton("Refresh")
        controls.addWidget(self.generate_button)
        controls.addWidget(self.refresh_button)
        layout.addLayout(controls)

        if self.selected_spot_id is not None:
            self.table = QTableWidget(0, 4)
            self.table.setHorizontalHeaderLabels((
                "Matching Car", "Type", "Status", "Current Location"
            ))
        else:
            self.table = QTableWidget(0, 6)
            self.table.setHorizontalHeaderLabels((
                "Town", "Industry", "Track", "Spot", "Requires", "Matching Cars"
            ))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.refresh_button.clicked.connect(self.refresh)
        self.generate_button.clicked.connect(self.generate_waybill)
        self.refresh()

    def refresh(self):
        self.demands = IndustryDemandService.get_open_demands()
        if self.selected_spot_id is not None:
            self.focused_demand = next(
                (
                    demand for demand in self.demands
                    if demand["spot_id"] == self.selected_spot_id
                ),
                None,
            )
            matches = (
                self.focused_demand["matches"]
                if self.focused_demand is not None
                else []
            )
            if self.focused_demand is None:
                self.description_label.setText(
                    "This spot is no longer open or is already reserved."
                )
            else:
                demand = self.focused_demand
                self.description_label.setText(
                    f"Compatible cars for {demand['industry']} — "
                    f"{demand['track']} — Spot {demand['spot']} "
                    f"({demand['requirements']})"
                )
            self.table.setRowCount(len(matches))
            for row, car in enumerate(matches):
                for column, value in enumerate((
                    car["name"],
                    car["car_type"],
                    car["status"],
                    car["location"],
                )):
                    self.table.setItem(row, column, QTableWidgetItem(str(value)))
            if matches:
                self.table.selectRow(0)
            return

        self.description_label.setText(
            "Open, unreserved industry spots and compatible cars."
        )
        self.table.setRowCount(len(self.demands))
        for row, demand in enumerate(self.demands):
            values = (
                demand["town"], demand["industry"], demand["track"],
                str(demand["spot"]), demand["requirements"],
                ", ".join(item["name"] for item in demand["matches"])
                or "No matching car",
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
            if demand["spot_id"] == self.selected_spot_id:
                self.table.selectRow(row)
                self.table.scrollToItem(self.table.item(row, 0))

    def generate_waybill(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(
                self,
                "Industry Demand",
                "Select a matching car."
                if self.selected_spot_id is not None
                else "Select a demand row.",
            )
            return
        demand = (
            self.focused_demand
            if self.selected_spot_id is not None
            else self.demands[row]
        )
        if demand is None:
            QMessageBox.information(
                self, "Industry Demand", "This demand is no longer available."
            )
            return
        if not demand["matches"]:
            QMessageBox.information(
                self, "Industry Demand", "No compatible available car was found."
            )
            return
        if self.selected_spot_id is not None:
            selected_car = demand["matches"][row]
            selected = selected_car["name"]
            car_id = selected_car["id"]
        else:
            names = [item["name"] for item in demand["matches"]]
            selected, accepted = QInputDialog.getItem(
                self, "Select Car", "Compatible car:", names, 0, False
            )
            if not accepted:
                return
            car_id = next(
                item["id"] for item in demand["matches"]
                if item["name"] == selected
            )
        success, result = IndustryDemandService.create_waybill(
            demand["spot_id"], car_id, self.session_combo.currentData()
        )
        if not success:
            QMessageBox.warning(self, "Generate Waybill", str(result))
            return
        QMessageBox.information(
            self, "Generate Waybill", f"Waybill #{result.id} created for {selected}."
        )
        self.refresh()
