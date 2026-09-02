from datetime import datetime

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
)
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.waybill import Waybill


class WaybillTableModel(QAbstractTableModel):

    HEADERS = [
        "Waybill",
        "Car",
        "Car Type",
        "Empty Weight (lb)",
        "Load Limit (lb)",
        "Load",
        "Commodity",
        "Gross Weight (lb)",
        "Tonnage",
        "Origin",
        "Destination",
        "Status",
        "Created",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.waybills = []
        self.refresh()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.waybills)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        column = index.column()
        if row < 0 or row >= len(self.waybills):
            return None
        waybill = self.waybills[row]
        if role == Qt.DisplayRole:
            if column == 0:
                return str(waybill.id)
            if column == 1:
                if waybill.car is None:
                    return ""
                return f"{waybill.car.reporting_mark} {waybill.car.number}"
            if column == 2:
                if waybill.car is None:
                    return ""
                return waybill.car.car_type or ""
            if column == 3:
                if (
                    waybill.car is None
                    or waybill.car.empty_weight_lbs is None
                ):
                    return ""
                return f"{waybill.car.empty_weight_lbs:,}"
            if column == 4:
                if (
                    waybill.car is None
                    or waybill.car.load_limit_lbs is None
                ):
                    return ""
                return f"{waybill.car.load_limit_lbs:,}"
            if column == 5:
                if waybill.load_state == "LOADED":
                    return "Loaded"
                if waybill.load_state == "EMPTY":
                    return "Empty"
                return "Not specified"
            if column == 6:
                return waybill.commodity or ""
            if column == 7:
                if waybill.gross_weight_lbs is None:
                    return ""
                return f"{waybill.gross_weight_lbs:,}"
            if column == 8:
                if waybill.tonnage is None:
                    return ""
                return f"{waybill.tonnage:,.1f}"
            if column == 9:
                parts = []
                if waybill.origin_operating_location is not None:
                    parts.append(waybill.origin_operating_location.name)
                elif waybill.origin_location:
                    parts.append(waybill.origin_location)
                if waybill.origin_operating_track is not None:
                    parts.append(waybill.origin_operating_track.name)
                if waybill.origin_spot is not None:
                    parts.append(f"Spot {waybill.origin_spot.spot_number}")
                return " - ".join(parts)
            if column == 10:
                parts = []
                if waybill.destination_operating_location is not None:
                    parts.append(waybill.destination_operating_location.name)
                elif waybill.destination_industry is not None:
                    parts.append(waybill.destination_industry.name)
                if waybill.destination_operating_track is not None:
                    parts.append(waybill.destination_operating_track.name)
                elif waybill.destination_track is not None:
                    parts.append(waybill.destination_track.name)
                if waybill.destination_spot is not None:
                    parts.append(f"Spot {waybill.destination_spot.spot_number}")
                return " - ".join(parts)
            if column == 11:
                return waybill.status or ""
            if column == 12:
                if waybill.created_at is None:
                    return ""
                return waybill.created_at.strftime("%Y-%m-%d %H:%M")
        if role == Qt.TextAlignmentRole and column in (
            0,
            3,
            4,
            5,
            7,
            8,
            11,
        ):
            return Qt.AlignCenter
        return None

    def _car_sort_key(self, waybill):
        """Sort cars by reporting mark, then numeric car number."""
        if waybill.car is None:
            return ("", 0, 0, "", waybill.id)
        reporting_mark = str(waybill.car.reporting_mark or "").casefold()
        number_text = str(waybill.car.number or "").strip()
        if number_text.isdigit():
            return (reporting_mark, 1, int(number_text), "", waybill.id)
        return (
            reporting_mark,
            1,
            0,
            number_text.casefold(),
            waybill.id,
        )

    def _destination_sort_key(self, waybill):
        location = waybill.destination_operating_location
        industry = waybill.destination_industry
        operating_track = waybill.destination_operating_track
        track = waybill.destination_track
        spot = waybill.destination_spot
        return (
            str(
                location.name
                if location
                else industry.name if industry else ""
            ).casefold(),
            str(
                operating_track.name
                if operating_track
                else track.name if track else ""
            ).casefold(),
            str(spot.spot_number if spot else "").casefold(),
            waybill.id,
        )

    def _sort_key(self, column):
        if column == 0:
            return lambda waybill: (waybill.id,)
        if column == 1:
            return self._car_sort_key
        if column == 2:
            return lambda waybill: (
                str(
                    waybill.car.car_type
                    if waybill.car is not None
                    else ""
                ).casefold(),
                waybill.id,
            )
        if column == 3:
            return lambda waybill: (
                waybill.car.empty_weight_lbs
                if (
                    waybill.car is not None
                    and waybill.car.empty_weight_lbs is not None
                )
                else -1,
                waybill.id,
            )
        if column == 4:
            return lambda waybill: (
                waybill.car.load_limit_lbs
                if (
                    waybill.car is not None
                    and waybill.car.load_limit_lbs is not None
                )
                else -1,
                waybill.id,
            )
        if column == 5:
            return lambda waybill: (
                str(waybill.load_state or "").casefold(),
                waybill.id,
            )
        if column == 6:
            return lambda waybill: (
                str(waybill.commodity or "").casefold(),
                waybill.id,
            )
        if column == 7:
            return lambda waybill: (
                waybill.gross_weight_lbs
                if waybill.gross_weight_lbs is not None
                else -1,
                waybill.id,
            )
        if column == 8:
            return lambda waybill: (
                waybill.tonnage if waybill.tonnage is not None else -1,
                waybill.id,
            )
        if column == 9:
            return lambda waybill: (
                str(waybill.origin_location or "").casefold(),
                waybill.id,
            )
        if column == 10:
            return self._destination_sort_key
        if column == 11:
            return lambda waybill: (
                str(waybill.status or "").casefold(),
                waybill.id,
            )
        if column == 12:
            return lambda waybill: (
                waybill.created_at or datetime.min,
                waybill.id,
            )
        return lambda waybill: (waybill.id,)

    def sort(self, column, order=Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self.waybills.sort(
            key=self._sort_key(column),
            reverse=(order == Qt.DescendingOrder),
        )
        self.layoutChanged.emit()

    def set_waybills(self, waybills):
        self.beginResetModel()
        self.waybills = list(waybills)
        self.endResetModel()

    def refresh(self):
        self.beginResetModel()
        with SessionLocal() as session:
            self.waybills = session.execute(
                select(Waybill)
                .options(
                    joinedload(Waybill.car),
                    joinedload(Waybill.operations_session),
                    joinedload(Waybill.origin_industry),
                    joinedload(Waybill.origin_track),
                    joinedload(Waybill.origin_spot),
                    joinedload(Waybill.origin_operating_location),
                    joinedload(Waybill.origin_operating_track),
                    joinedload(Waybill.destination_industry),
                    joinedload(Waybill.destination_track),
                    joinedload(Waybill.destination_spot),
                    joinedload(Waybill.destination_operating_location),
                    joinedload(Waybill.destination_operating_track),
                )
                .order_by(Waybill.created_at.desc(), Waybill.id.desc())
            ).scalars().all()
        self.endResetModel()

    def get_waybill(self, row):
        if row < 0 or row >= len(self.waybills):
            return None
        return self.waybills[row]
