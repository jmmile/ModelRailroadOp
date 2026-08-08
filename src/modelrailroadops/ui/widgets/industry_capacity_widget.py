from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QFormLayout,
)

from modelrailroadops.services.industry_capacity_service import (
    IndustryCapacityService,
)



class IndustryCapacityWidget(QWidget):

    def __init__(
        self,
        parent=None
    ):

        super().__init__(parent)


        layout = QVBoxLayout(self)


        group = QGroupBox(
            "Industry Capacity"
        )


        form = QFormLayout()


        self.industry_label = QLabel("-")

        self.tracks_label = QLabel("-")

        self.total_label = QLabel("-")

        self.occupied_label = QLabel("-")

        self.available_label = QLabel("-")

        self.status_label = QLabel("-")



        form.addRow(
            "Industry",
            self.industry_label
        )

        form.addRow(
            "Tracks",
            self.tracks_label
        )

        form.addRow(
            "Total Spots",
            self.total_label
        )

        form.addRow(
            "Occupied",
            self.occupied_label
        )

        form.addRow(
            "Available",
            self.available_label
        )

        form.addRow(
            "Status",
            self.status_label
        )


        group.setLayout(
            form
        )


        layout.addWidget(
            group
        )


        layout.addStretch()



    def clear(self):

        self.industry_label.setText("-")

        self.tracks_label.setText("-")

        self.total_label.setText("-")

        self.occupied_label.setText("-")

        self.available_label.setText("-")

        self.status_label.setText("-")



    def load_industry(
        self,
        industry_id
    ):


        data = (
            IndustryCapacityService.get_capacity(
                industry_id
            )
        )


        if data is None:

            self.clear()

            return



        self.industry_label.setText(
            data["industry"]
        )


        self.tracks_label.setText(
            str(data["tracks"])
        )


        self.total_label.setText(
            str(data["total_spots"])
        )


        self.occupied_label.setText(
            str(data["occupied"])
        )


        self.available_label.setText(
            str(data["available"])
        )



        percent = data["percent_available"]



        if percent == 0:

            status = "🔴 FULL"

            color = "red"


        elif percent < 50:

            status = "🟡 LIMITED"

            color = "orange"


        else:

            status = "🟢 AVAILABLE"

            color = "green"



        self.status_label.setText(
            f"{status} ({percent}% Available)"
        )


        self.status_label.setStyleSheet(
            f"""
            color: {color};
            font-weight: bold;
            """
        )