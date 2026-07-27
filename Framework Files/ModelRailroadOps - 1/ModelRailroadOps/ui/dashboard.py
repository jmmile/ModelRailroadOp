from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel
class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        l=QVBoxLayout(self)
        l.addWidget(QLabel('Welcome to Model Railroad Operations Manager'))
