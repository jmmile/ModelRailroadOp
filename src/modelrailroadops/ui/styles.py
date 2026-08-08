TABLE_SELECTION_STYLE = """
QTableView {
    selection-background-color: #1e4f91;
    selection-color: white;
    alternate-background-color: #f5f5f5;
}

QTableView::item:selected {
    background-color: #1e4f91;
    color: white;
}

QTableView::item:selected:active {
    background-color: #1e4f91;
    color: white;
}

QTableView::item:selected:!active {
    background-color: #1e4f91;
    color: white;
}

QTableView::item:hover {
    background-color: #d8e8ff;
}
"""