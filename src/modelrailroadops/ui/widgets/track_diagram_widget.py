from PySide6.QtCore import QMimeData, QPoint, QTimer, Qt, Signal
from PySide6.QtGui import QDrag, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from modelrailroadops.services.location_service import LocationService
from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car
from modelrailroadops.services.waybill_service import WaybillService
from modelrailroadops.ui.dialogs.add_waybill_dialog import AddWaybillDialog
from modelrailroadops.ui.waybills.waybill_preview_dialog import WaybillPreviewDialog
from modelrailroadops.services.industry_service import IndustryService
from modelrailroadops.services.industry_demand_service import (
    IndustryDemandService,
)
from modelrailroadops.ui.industries.industry_demand_dialog import (
    IndustryDemandDialog,
)


class CarSymbolWidget(QFrame):
    """Compact car identification block used by the track diagram."""

    clicked = Signal(object)
    double_clicked = Signal(object)
    SYMBOL_WIDTH = 126

    STATUS_COLORS = {
        "LOADED": "#d8c39e",
        "EMPTY": "#e7f0f7",
    }

    def __init__(self, car, parent=None):
        super().__init__(parent)
        self.car = car
        self.fill_color = self.STATUS_COLORS.get(
            (car.status or "").upper(),
            "#e8e8e8",
        )
        self.setFixedWidth(self.SYMBOL_WIDTH)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("carSymbol")
        self.setCursor(Qt.PointingHandCursor)
        self.set_selected(False)
        self._drag_start_position = QPoint()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 2, 3, 2)
        layout.setSpacing(2)

        self.number_label = QLabel(
            f"{car.reporting_mark} {car.number}"
        )
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.setStyleSheet(
            "QLabel { border: 1px solid #333; border-radius: 2px; "
            f"background-color: {self.fill_color}; padding: 5px 3px; "
            "font-weight: bold; }"
        )

        self.type_label = QLabel(car.car_type or "Unknown Type")
        self.type_label.setAlignment(Qt.AlignCenter)
        self.type_label.setWordWrap(True)
        self.type_label.setMinimumHeight(28)
        self.type_label.setStyleSheet(
            f"background-color: {self.fill_color};"
        )

        tooltip = (
            f"{car.reporting_mark} {car.number}\n"
            f"Type: {car.car_type or 'Unknown'}\n"
            f"Status: {car.status or 'Unknown'}\n"
            f"Length: {car.length if car.length is not None else 'Unknown'}"
        )
        self.setToolTip(tooltip)
        self.number_label.setToolTip(tooltip)
        self.type_label.setToolTip(tooltip)

        layout.addWidget(self.number_label)
        layout.addWidget(self.type_label)

    def set_selected(self, selected):
        border = "2px solid #1b5eaa" if selected else "2px solid transparent"
        self.setStyleSheet(
            f"#carSymbol {{ border: {border}; border-radius: 3px; }}"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.position().toPoint()
            self.clicked.emit(self.car)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.LeftButton:
            return super().mouseMoveEvent(event)
        if (
            event.position().toPoint() - self._drag_start_position
        ).manhattanLength() < QApplication.startDragDistance():
            return super().mouseMoveEvent(event)

        mime_data = QMimeData()
        mime_data.setData(
            TrackCarRowWidget.MIME_TYPE,
            (
                f"{self.car.id}:{self.car.operating_track_id}"
            ).encode("utf-8"),
        )
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(self.grab())
        drag.setHotSpot(self._drag_start_position)
        drag.exec(Qt.MoveAction)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.car)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class EmptySpotWidget(QFrame):
    """Visible destination for an unoccupied industry spot."""

    clicked = Signal(object)

    def __init__(self, spot, parent=None):
        super().__init__(parent)
        self.spot = spot
        self.setFixedWidth(CarSymbolWidget.SYMBOL_WIDTH)
        self.setMinimumHeight(58)
        self.setCursor(Qt.PointingHandCursor)
        self.set_selected(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        label = QLabel(f"Spot {spot.spot_number}\nEmpty")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

    def set_selected(self, selected):
        border_color = "#1b5eaa" if selected else "#888"
        border_width = "2px" if selected else "1px"
        self.setStyleSheet(
            f"QFrame {{ border: {border_width} dashed {border_color}; "
            "background-color: #f7f7f7; }"
            "QLabel { border: none; color: #666; }"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.spot)
        super().mousePressEvent(event)


class TrackCarRowWidget(QWidget):
    """Same-track drop target with a visible insertion marker."""

    MIME_TYPE = "application/x-modelrailroadops-track-car"
    reorder_requested = Signal(int, int)

    def __init__(self, track_id, parent=None):
        super().__init__(parent)
        self.track_id = track_id
        self.symbols = []
        self.insertion_index = None
        self.setAcceptDrops(True)

    def set_symbols(self, symbols):
        self.symbols = list(symbols)
        self.setMinimumWidth(
            max(1, len(self.symbols))
            * (CarSymbolWidget.SYMBOL_WIDTH + 6)
            + 12
        )

    def _drag_values(self, event):
        mime_data = event.mimeData()
        if not mime_data.hasFormat(self.MIME_TYPE):
            return None
        try:
            value = bytes(mime_data.data(self.MIME_TYPE)).decode("utf-8")
            car_id, track_id = (int(part) for part in value.split(":", 1))
        except (TypeError, ValueError):
            return None
        if track_id != self.track_id:
            return None
        return car_id, track_id

    def _target_index(self, x_position):
        for index, symbol in enumerate(self.symbols):
            if x_position < symbol.geometry().center().x():
                return index
        return len(self.symbols)

    def dragEnterEvent(self, event):
        if self._drag_values(event) is None:
            event.ignore()
            return
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if self._drag_values(event) is None:
            event.ignore()
            return
        self.insertion_index = self._target_index(
            event.position().toPoint().x()
        )
        self.update()
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.insertion_index = None
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        values = self._drag_values(event)
        if values is None:
            event.ignore()
            return
        car_id, _track_id = values
        target_index = (
            self.insertion_index
            if self.insertion_index is not None
            else self._target_index(event.position().toPoint().x())
        )
        self.insertion_index = None
        self.update()
        self.reorder_requested.emit(car_id, target_index)
        event.acceptProposedAction()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.insertion_index is None:
            return

        if self.insertion_index >= len(self.symbols):
            x_position = (
                self.symbols[-1].geometry().right() + 4
                if self.symbols
                else 4
            )
        else:
            x_position = self.symbols[
                self.insertion_index
            ].geometry().left() - 3

        painter = QPainter(self)
        painter.setPen(QPen(Qt.blue, 3))
        painter.drawLine(x_position, 2, x_position, self.height() - 2)


class TrackDiagramWidget(QWidget):
    """Live view of cars on general and town-grouped industry tracks."""

    DISPLAY_LOCATION_TYPES = {
        "YARD",
        "STAGING",
        "INTERCHANGE",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.car_symbols = []
        self.empty_spot_widgets = []
        self.track_sections = []
        self.track_headings = []
        self.diagram_tab_layouts = {}
        self.selected_car_id = None
        self.selected_spot_id = None
        self._diagram_signature = None

        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        title = QLabel("Track Diagram")
        title_font = title.font()
        title_font.setBold(True)
        title.setFont(title_font)
        controls.addWidget(title)

        self.status_label = QLabel(
            "General and industry tracks"
        )
        controls.addWidget(self.status_label)
        controls.addStretch()

        controls.addWidget(QLabel("Find Car"))
        self.find_car_edit = QLineEdit()
        self.find_car_edit.setPlaceholderText("Reporting marks or number")
        self.find_car_edit.setMaximumWidth(190)
        controls.addWidget(self.find_car_edit)
        self.find_car_button = QPushButton("Find")
        controls.addWidget(self.find_car_button)

        self.refresh_button = QPushButton("Refresh")
        controls.addWidget(self.refresh_button)
        layout.addLayout(controls)

        self.legend_label = QLabel(
            '<b>Legend:</b> '
            '<span style="background-color:#d8c39e; padding:2px 8px;">'
            'Loaded</span>&nbsp;&nbsp;'
            '<span style="background-color:#e7f0f7; padding:2px 8px;">'
            'Empty</span>&nbsp;&nbsp;'
            '<span style="background-color:#e8e8e8; padding:2px 8px;">'
            'Other / Available</span>&nbsp;&nbsp;'
            '<span style="color:#b00020; font-weight:bold;">'
            'Red track = over capacity</span>'
        )
        self.legend_label.setTextFormat(Qt.RichText)
        layout.addWidget(self.legend_label)

        self.details_label = QLabel(
            "Select a car to view its details."
        )
        self.details_label.setFrameShape(QFrame.StyledPanel)
        self.details_label.setWordWrap(True)
        self.details_label.setContentsMargins(6, 5, 6, 5)

        detail_layout = QHBoxLayout()
        detail_layout.addWidget(self.details_label, 1)
        self.move_left_button = QPushButton("Move Left")
        self.move_right_button = QPushButton("Move Right")
        self.mark_loaded_button = QPushButton("Mark Loaded")
        self.mark_empty_button = QPushButton("Mark Unloaded")
        self.find_matching_car_button = QPushButton("Find Matching Car")
        self.move_left_button.setEnabled(False)
        self.move_right_button.setEnabled(False)
        self.mark_loaded_button.setEnabled(False)
        self.mark_empty_button.setEnabled(False)
        self.find_matching_car_button.setEnabled(False)
        detail_layout.addWidget(self.move_left_button)
        detail_layout.addWidget(self.move_right_button)
        detail_layout.addWidget(self.mark_loaded_button)
        detail_layout.addWidget(self.mark_empty_button)
        detail_layout.addWidget(self.find_matching_car_button)
        layout.addLayout(detail_layout)

        self.diagram_tabs = QTabWidget()
        layout.addWidget(self.diagram_tabs)

        self.refresh_button.clicked.connect(self.refresh)
        self.find_car_button.clicked.connect(self.find_car)
        self.find_car_edit.returnPressed.connect(self.find_car)
        self.move_left_button.clicked.connect(
            lambda: self.move_selected_car(-1)
        )
        self.move_right_button.clicked.connect(
            lambda: self.move_selected_car(1)
        )
        self.mark_loaded_button.clicked.connect(
            lambda: self.set_selected_car_load_state("LOADED")
        )
        self.mark_empty_button.clicked.connect(
            lambda: self.set_selected_car_load_state("EMPTY")
        )
        self.find_matching_car_button.clicked.connect(
            self.find_matching_car
        )

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(2000)
        self.refresh_timer.timeout.connect(self.refresh)

        self.refresh(force=True)

    @staticmethod
    def _car_sort_key(car):
        return (
            car.operating_track_position
            if car.operating_track_position is not None
            else 999999,
            (car.reporting_mark or "").casefold(),
            (car.number or "").casefold(),
        )

    def _get_diagram_data(self):
        locations = []
        for location in LocationService.get_all():
            if (
                not location.active
                or location.location_type not in self.DISPLAY_LOCATION_TYPES
            ):
                continue

            tracks = []
            for track in location.tracks:
                if not track.active:
                    continue
                cars = sorted(track.cars, key=self._car_sort_key)
                tracks.append((track, cars))

            locations.append((location, tracks))

        towns = {}
        for industry in IndustryService.get_all():
            town = (industry.location or "Unassigned").strip() or "Unassigned"
            tracks = []
            for track in industry.tracks:
                cars = []
                spot_cells = []
                for spot in track.spots:
                    spot.diagram_industry_name = industry.name
                    spot.diagram_track_name = track.name
                    spot.diagram_town = town
                    spot_cells.append((spot, spot.car))
                    if spot.car is None:
                        continue
                    spot.car.diagram_spot_number = spot.spot_number
                    spot.car.diagram_spot_count = len(track.spots)
                    cars.append(spot.car)
                track.diagram_spot_cells = spot_cells
                tracks.append((track, cars, len(track.spots)))
            towns.setdefault(town, []).append((industry, tracks))

        town_groups = [
            (town, sorted(industries, key=lambda item: item[0].name.casefold()))
            for town, industries in sorted(
                towns.items(), key=lambda item: item[0].casefold()
            )
        ]
        return locations, town_groups

    @staticmethod
    def _signature(diagram_data):
        locations, town_groups = diagram_data
        general_signature = tuple(
            (
                location.id,
                location.name,
                location.location_type,
                tuple(
                    (
                        track.id,
                        track.name,
                        track.capacity,
                        tuple(
                            (
                                car.id,
                                car.reporting_mark,
                                car.number,
                                car.car_type,
                                car.status,
                                car.length,
                                car.operating_track_position,
                            )
                            for car in cars
                        ),
                    )
                    for track, cars in tracks
                ),
            )
            for location, tracks in locations
        )
        industry_signature = tuple(
            (
                town,
                tuple(
                    (
                        industry.id,
                        industry.name,
                        tuple(
                            (
                                track.id,
                                track.name,
                                capacity,
                                tuple(
                                    (
                                        car.id,
                                        car.reporting_mark,
                                        car.number,
                                        car.car_type,
                                        car.status,
                                        car.length,
                                        car.operating_track_position,
                                    )
                                    for car in cars
                                ),
                            )
                            for track, cars, capacity in tracks
                        ),
                    )
                    for industry, tracks in industries
                ),
            )
            for town, industries in town_groups
        )
        return general_signature, industry_signature

    def _clear_diagram(self):
        while self.diagram_tabs.count():
            page = self.diagram_tabs.widget(0)
            self.diagram_tabs.removeTab(0)
            page.deleteLater()
        self.car_symbols = []
        self.empty_spot_widgets = []
        self.track_sections = []
        self.track_headings = []
        self.diagram_tab_layouts = {}

    def _add_diagram_tab(self, name):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(content)
        self.diagram_tabs.addTab(scroll_area, name)
        self.diagram_tab_layouts[name] = content_layout
        return content_layout

    @staticmethod
    def _rail_line():
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setLineWidth(2)
        return line

    def _build_track(
        self,
        owner_name,
        track,
        cars,
        capacity=None,
        row_track_id=None,
        target_layout=None,
        tab_name=None,
    ):
        section = QFrame()
        section.setFrameShape(QFrame.StyledPanel)
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(8, 6, 8, 6)
        section_layout.setSpacing(3)

        if capacity is None:
            capacity = track.capacity
        available = (
            max(capacity - len(cars), 0)
            if capacity is not None
            else None
        )
        capacity_text = (
            f"{len(cars)} occupied / {capacity} capacity / "
            f"{available} available"
            if capacity is not None
            else f"{len(cars)} occupied / no capacity limit"
        )
        heading = QLabel(
            f"{owner_name} — {track.name}  ({capacity_text})"
        )
        heading_font = heading.font()
        heading_font.setBold(True)
        heading.setFont(heading_font)
        if capacity is not None and len(cars) > capacity:
            heading.setStyleSheet("color: #b00020; font-weight: bold;")
            section.setObjectName("overCapacityTrack")
            section.setStyleSheet(
                "#overCapacityTrack { border: 2px solid #b00020; }"
            )
        section_layout.addWidget(heading)
        self.track_headings.append(heading)
        section_layout.addWidget(self._rail_line())

        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("← Left End"))
        end_layout.addStretch()
        end_layout.addWidget(QLabel("Right End →"))
        section_layout.addLayout(end_layout)

        car_scroll = QScrollArea()
        car_scroll.setWidgetResizable(True)
        car_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        car_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        car_scroll.setFrameShape(QFrame.NoFrame)
        car_scroll.setMinimumHeight(82)

        car_content = TrackCarRowWidget(
            row_track_id if row_track_id is not None else track.id
        )
        car_layout = QHBoxLayout(car_content)
        car_layout.setContentsMargins(0, 0, 0, 0)
        car_layout.setSpacing(6)

        track_symbols = []
        row_items = []
        spot_cells = getattr(track, "diagram_spot_cells", None)
        if spot_cells is not None:
            for spot, car in spot_cells:
                if car is None:
                    placeholder = EmptySpotWidget(spot)
                    placeholder.clicked.connect(self.show_spot_details)
                    if spot.id == self.selected_spot_id:
                        placeholder.set_selected(True)
                    self.empty_spot_widgets.append(placeholder)
                    row_items.append(placeholder)
                    car_layout.addWidget(placeholder)
                    continue
                symbol = CarSymbolWidget(car)
                symbol.clicked.connect(self.show_car_details)
                symbol.double_clicked.connect(self.create_pickup_waybill)
                symbol.setToolTip(symbol.toolTip() + "\nDouble-click to assign a pickup waybill.")
                if car.id == self.selected_car_id:
                    symbol.set_selected(True)
                self.car_symbols.append(symbol)
                symbol.diagram_tab_name = tab_name
                track_symbols.append(symbol)
                row_items.append(symbol)
                car_layout.addWidget(symbol)
        elif cars:
            for car in cars:
                symbol = CarSymbolWidget(car)
                symbol.clicked.connect(self.show_car_details)
                if car.id == self.selected_car_id:
                    symbol.set_selected(True)
                self.car_symbols.append(symbol)
                symbol.diagram_tab_name = tab_name
                track_symbols.append(symbol)
                row_items.append(symbol)
                car_layout.addWidget(symbol)
        else:
            empty_label = QLabel("No cars")
            empty_label.setStyleSheet("color: #666; font-style: italic;")
            car_layout.addWidget(empty_label)

        car_layout.addStretch()
        car_content.set_symbols(row_items)
        car_content.reorder_requested.connect(
            self.reorder_car_on_track
        )
        car_scroll.setWidget(car_content)
        section_layout.addWidget(car_scroll)
        section_layout.addWidget(self._rail_line())

        self.track_sections.append(section)
        target_layout.addWidget(section)

    def create_pickup_waybill(self, selected_car):
        # Re-read the location because the diagram may predate a recent move.
        with SessionLocal() as session:
            car = session.get(Car, selected_car.id)
            if car is None or car.spot_id is None or car.industry_id is None:
                return
            car_id = car.id
            load_state = (car.status or "").upper()

        timer_running = self.refresh_timer.isActive()
        self.refresh_timer.stop()
        try:
            existing = WaybillService.get_active_for_car(car_id)
            if existing:
                WaybillPreviewDialog(existing[0], self).exec()
                return
            dialog = AddWaybillDialog(self)
            index = dialog.car_combo.findData(car_id)
            if index < 0:
                QMessageBox.information(self, "Pickup Waybill", "This car is no longer available for a new waybill.")
                return
            dialog.car_combo.setCurrentIndex(index)
            dialog.car_changed()
            dialog.car_combo.setEnabled(False)
            load_index = dialog.load_state_combo.findData(load_state)
            if load_index >= 0:
                dialog.load_state_combo.setCurrentIndex(load_index)
            dialog.setWindowTitle("Assign Pickup Waybill")
            dialog.exec()
        finally:
            if timer_running:
                self.refresh_timer.start()

    def show_car_details(self, car):
        self.selected_car_id = car.id
        self.selected_spot_id = None
        for symbol in self.car_symbols:
            symbol.set_selected(symbol.car.id == car.id)
        for spot_widget in self.empty_spot_widgets:
            spot_widget.set_selected(False)

        length = (
            f"{car.length} ft"
            if car.length is not None
            else "Unknown"
        )
        self.details_label.setText(
            f"Car: {car.reporting_mark} {car.number}  |  "
            f"Type: {car.car_type or 'Unknown'}  |  "
            f"Status: {car.status or 'Unknown'}  |  "
            f"Length: {length}  |  "
            f"Location: {car.location or 'Unassigned'}  |  "
            f"Track Position: "
            f"{self._track_position_text(car)}"
        )
        self._update_move_buttons(car)
        is_industry_car = car.industry_id is not None and car.spot_id is not None
        self.mark_loaded_button.setEnabled(
            is_industry_car and (car.status or "").upper() != "LOADED"
        )
        self.mark_empty_button.setEnabled(
            is_industry_car and (car.status or "").upper() != "EMPTY"
        )
        self.find_matching_car_button.setEnabled(False)

    def show_spot_details(self, spot):
        self.selected_car_id = None
        self.selected_spot_id = spot.id
        for symbol in self.car_symbols:
            symbol.set_selected(False)
        for spot_widget in self.empty_spot_widgets:
            spot_widget.set_selected(spot_widget.spot.id == spot.id)

        requirements = []
        if spot.allowed_car_type:
            requirements.append(f"Car Type: {spot.allowed_car_type}")
        if spot.allowed_owner:
            requirements.append(f"Owner: {spot.allowed_owner}")
        if spot.max_length is not None:
            requirements.append(f"Maximum Length: {spot.max_length} ft")
        if spot.load_only:
            requirements.append("Loaded only")
        if spot.empty_only:
            requirements.append("Empty only")
        if not spot.hazardous_allowed:
            requirements.append("No hazardous cars")

        self.details_label.setText(
            f"Empty Spot: {spot.diagram_industry_name} — "
            f"{spot.diagram_track_name} — Spot {spot.spot_number}  |  "
            f"Town: {spot.diagram_town}  |  "
            f"Requirements: {', '.join(requirements) or 'Any car'}"
        )
        self.move_left_button.setEnabled(False)
        self.move_right_button.setEnabled(False)
        self.mark_loaded_button.setEnabled(False)
        self.mark_empty_button.setEnabled(False)
        self.find_matching_car_button.setEnabled(True)

    def find_matching_car(self):
        if self.selected_spot_id is None:
            return
        demand = next(
            (
                row for row in IndustryDemandService.get_open_demands()
                if row["spot_id"] == self.selected_spot_id
            ),
            None,
        )
        if demand is None:
            QMessageBox.information(
                self,
                "Find Matching Car",
                "This spot is occupied or already reserved by a waybill.",
            )
            self.refresh(force=True)
            return
        dialog = IndustryDemandDialog(
            self,
            selected_spot_id=self.selected_spot_id,
        )
        dialog.exec()
        self.refresh(force=True)

    def set_selected_car_load_state(self, status):
        if self.selected_car_id is None:
            return

        success, message = LocationService.set_industry_car_load_state(
            self.selected_car_id,
            status,
        )
        if not success:
            QMessageBox.warning(self, "Industry Work", message)
            return

        selected_car_id = self.selected_car_id
        self.refresh(force=True)
        selected_symbol = next(
            (
                symbol for symbol in self.car_symbols
                if symbol.car.id == selected_car_id
            ),
            None,
        )
        if selected_symbol is not None:
            self.show_car_details(selected_symbol.car)

    def find_car(self):
        search_text = " ".join(self.find_car_edit.text().split()).casefold()
        if not search_text:
            QMessageBox.information(
                self,
                "Find Car",
                "Enter reporting marks or a car number.",
            )
            return

        symbol = next(
            (
                item for item in self.car_symbols
                if search_text in (
                    f"{item.car.reporting_mark} {item.car.number}"
                ).casefold()
            ),
            None,
        )
        if symbol is None:
            QMessageBox.information(
                self,
                "Find Car",
                f"No car matching '{self.find_car_edit.text().strip()}' is on a displayed track.",
            )
            return

        tab_name = getattr(symbol, "diagram_tab_name", None)
        for index in range(self.diagram_tabs.count()):
            if self.diagram_tabs.tabText(index) == tab_name:
                self.diagram_tabs.setCurrentIndex(index)
                scroll_area = self.diagram_tabs.widget(index)
                scroll_area.ensureWidgetVisible(symbol)
                break
        self.show_car_details(symbol.car)

    @staticmethod
    def _track_position_text(car):
        spot_number = getattr(car, "diagram_spot_number", None)
        if spot_number is not None:
            return f"Spot {spot_number}"
        return str(car.operating_track_position or "Not assigned")

    def _update_move_buttons(self, car):
        spot_number = getattr(car, "diagram_spot_number", None)
        spot_count = getattr(car, "diagram_spot_count", None)
        if spot_number is not None and spot_count is not None:
            self.move_left_button.setEnabled(spot_number > 1)
            self.move_right_button.setEnabled(spot_number < spot_count)
            return

        track_symbols = [
            symbol for symbol in self.car_symbols
            if symbol.car.operating_track_id == car.operating_track_id
        ]
        selected_index = next(
            (
                index for index, symbol in enumerate(track_symbols)
                if symbol.car.id == car.id
            ),
            None,
        )
        self.move_left_button.setEnabled(
            selected_index is not None and selected_index > 0
        )
        self.move_right_button.setEnabled(
            selected_index is not None
            and selected_index < len(track_symbols) - 1
        )

    def move_selected_car(self, direction):
        if self.selected_car_id is None:
            return

        success, message = LocationService.move_car_on_track(
            self.selected_car_id,
            direction,
        )
        if not success:
            QMessageBox.warning(
                self,
                "Track Position",
                message,
            )
            return

        selected_car_id = self.selected_car_id
        self.refresh(force=True)
        selected_symbol = next(
            (
                symbol for symbol in self.car_symbols
                if symbol.car.id == selected_car_id
            ),
            None,
        )
        if selected_symbol is not None:
            self.show_car_details(selected_symbol.car)

    def reorder_car_on_track(self, car_id, insertion_index):
        success, message = LocationService.reorder_car_on_track(
            car_id,
            insertion_index,
        )
        if not success:
            QMessageBox.warning(
                self,
                "Track Position",
                message,
            )
            return

        self.selected_car_id = car_id
        self.refresh(force=True)
        selected_symbol = next(
            (
                symbol for symbol in self.car_symbols
                if symbol.car.id == car_id
            ),
            None,
        )
        if selected_symbol is not None:
            self.show_car_details(selected_symbol.car)

    def refresh(self, force=False):
        diagram_data = self._get_diagram_data()
        signature = self._signature(diagram_data)
        if not force and signature == self._diagram_signature:
            return

        self._diagram_signature = signature
        selected_tab = self.diagram_tabs.tabText(
            self.diagram_tabs.currentIndex()
        )
        self._clear_diagram()

        locations, town_groups = diagram_data
        track_count = 0
        car_count = 0
        general_layout = self._add_diagram_tab("General Tracks")
        for location, tracks in locations:
            for track, cars in tracks:
                self._build_track(
                    location.name,
                    track,
                    cars,
                    target_layout=general_layout,
                    tab_name="General Tracks",
                )
                track_count += 1
                car_count += len(cars)

        if not locations:
            general_layout.addWidget(QLabel(
                "No active yard, staging, or interchange tracks were found."
            ))
        general_layout.addStretch()

        for town, industries in town_groups:
            town_layout = self._add_diagram_tab(town)

            for industry, tracks in industries:
                for track, cars, capacity in tracks:
                    self._build_track(
                        industry.name,
                        track,
                        cars,
                        capacity=capacity,
                        row_track_id=track.operating_track_id,
                        target_layout=town_layout,
                        tab_name=town,
                    )
                    track_count += 1
                    car_count += len(cars)
            town_layout.addStretch()

        if track_count == 0:
            general_layout.insertWidget(0, QLabel(
                "No active general or industry tracks were found."
            ))

        for index in range(self.diagram_tabs.count()):
            if self.diagram_tabs.tabText(index) == selected_tab:
                self.diagram_tabs.setCurrentIndex(index)
                break
        self.status_label.setText(
            f"{track_count} tracks | {car_count} cars | Auto-refresh: 2 seconds"
        )

        if (
            self.selected_car_id is not None
            and not any(
                symbol.car.id == self.selected_car_id
                for symbol in self.car_symbols
            )
        ):
            self.selected_car_id = None
            self.details_label.setText(
                "Select a car to view its details."
            )
            self.move_left_button.setEnabled(False)
            self.move_right_button.setEnabled(False)
            self.mark_loaded_button.setEnabled(False)
            self.mark_empty_button.setEnabled(False)
            self.find_matching_car_button.setEnabled(False)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh(force=True)
        self.refresh_timer.start()

    def hideEvent(self, event):
        self.refresh_timer.stop()
        super().hideEvent(event)
