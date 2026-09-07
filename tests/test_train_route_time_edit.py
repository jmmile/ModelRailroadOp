from PySide6.QtCore import Qt, QTime
from PySide6.QtTest import QTest

from modelrailroadops.ui.dialogs.add_train_route_dialog import RouteStopTimeEdit


def test_typing_replaces_clicked_route_stop_time(qapp):
    time_edit = RouteStopTimeEdit()
    time_edit.setDisplayFormat("h:mm AP")
    time_edit.setTime(QTime(10, 45))
    time_edit.show()

    QTest.mouseClick(time_edit.lineEdit(), Qt.LeftButton)
    QTest.keyClick(time_edit.lineEdit(), Qt.Key_9)

    assert time_edit.time() == QTime(9, 45)
