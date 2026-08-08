from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
)

from modelrailroadops.ui.styles import TABLE_SELECTION_STYLE


def configure_table(table):

    table.setStyleSheet(
        TABLE_SELECTION_STYLE
    )

    table.setSelectionBehavior(
        QAbstractItemView.SelectRows
    )

    table.setSelectionMode(
        QAbstractItemView.SingleSelection
    )

    table.setAlternatingRowColors(
        True
    )

    table.setEditTriggers(
        QAbstractItemView.NoEditTriggers
    )

    table.horizontalHeader().setSectionResizeMode(
        QHeaderView.ResizeToContents
    )

    table.verticalHeader().setVisible(
        False
    )