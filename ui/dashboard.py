from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QVBoxLayout
from database import get_count


class Dashboard(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("<h1>Model Railroad Operations Manager</h1>")
        layout.addWidget(title)

        self.cars = QLabel()
        self.industries = QLabel()
        self.locomotives = QLabel()
        self.trains = QLabel()

        layout.addWidget(self.cars)
        layout.addWidget(self.industries)
        layout.addWidget(self.locomotives)
        layout.addWidget(self.trains)

        self.setLayout(layout)

        self.refresh()

    def refresh(self):

        self.cars.setText(
            f"Cars: {get_count('cars')}"
        )

        self.industries.setText(
            f"Industries: {get_count('industries')}"
        )

        self.locomotives.setText(
            f"Locomotives: {get_count('locomotives')}"
        )

        self.trains.setText(
            f"Trains: {get_count('trains')}"
        )