
import sys
from pathlib import Path


# ---------------------------------------------------------
# Add src folder to Python path
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_FOLDER = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(SRC_FOLDER),
)


# ---------------------------------------------------------
# Qt
# ---------------------------------------------------------

from PySide6.QtWidgets import QApplication


# ---------------------------------------------------------
# Database
# ---------------------------------------------------------

from modelrailroadops.database.database import (
    SessionLocal,
)

from modelrailroadops.models.industry import Industry


# ---------------------------------------------------------
# Model
# ---------------------------------------------------------

from modelrailroadops.ui.models.industry_track_table_model import (
    IndustryTrackTableModel,
)


# ---------------------------------------------------------
# Widget
# ---------------------------------------------------------

from modelrailroadops.ui.widgets.industry_tracks_widget import (
    IndustryTracksWidget,
)


def print_database_state():
    """
    Test 1:
    Verify that the database contains industries with
    and without tracks.
    """

    print()
    print("=" * 70)
    print("TEST 1 - DATABASE")
    print("=" * 70)

    with SessionLocal() as session:

        industries = (
            session.query(Industry)
            .order_by(Industry.id)
            .all()
        )

        print(
            f"Database industries: {len(industries)}"
        )

        found_zero_track = False

        for industry in industries:

            track_count = len(
                industry.tracks
            )

            print(
                f"ID={industry.id} | "
                f"Name='{industry.name}' | "
                f"Tracks={track_count}"
            )

            if track_count == 0:

                found_zero_track = True

                print(
                    "   >>> ZERO-TRACK INDUSTRY FOUND"
                )

        if found_zero_track:

            print()
            print(
                "PASS: Database contains at least "
                "one industry with zero tracks."
            )

        else:

            print()
            print(
                "FAIL: Database contains no "
                "zero-track industries."
            )


def test_table_model():
    """
    Test 2:
    Verify that IndustryTrackTableModel includes
    industries with zero tracks.
    """

    print()
    print("=" * 70)
    print("TEST 2 - INDUSTRY TRACK TABLE MODEL")
    print("=" * 70)

    model = IndustryTrackTableModel()

    print(
        f"Model row count: {model.rowCount()}"
    )

    found_zero_track_row = False

    for row_number, row in enumerate(
        model.tracks
    ):

        industry_name = row.get(
            "industry_name"
        )

        track_name = row.get(
            "track_name"
        )

        track_id = row.get(
            "track_id"
        )

        print(
            f"ROW {row_number}: "
            f"Industry='{industry_name}' | "
            f"Track='{track_name}' | "
            f"Track ID={track_id}"
        )

        if (
            track_id is None
            and industry_name
        ):

            found_zero_track_row = True

            print(
                "   >>> ZERO-TRACK ROW FOUND"
            )

    print()

    if found_zero_track_row:

        print(
            "PASS: Model contains a zero-track row."
        )

    else:

        print(
            "FAIL: Model does NOT contain a "
            "zero-track row."
        )

    return model


def test_qt_widget(model):
    """
    Test 3:
    Create the actual IndustryTracksWidget and
    inspect the QTableView.
    """

    print()
    print("=" * 70)
    print("TEST 3 - INDUSTRY TRACKS WIDGET")
    print("=" * 70)

    widget = IndustryTracksWidget()

    print(
        "Widget created."
    )

    print(
        f"Widget model object: {widget.model}"
    )

    print(
        f"Table model object: {widget.table.model()}"
    )

    print(
        "Same model object:",
        widget.table.model() is widget.model,
    )

    print(
        f"Widget model rows: "
        f"{widget.model.rowCount()}"
    )

    print(
        f"Table model rows: "
        f"{widget.table.model().rowCount()}"
    )

    print()

    found_zero_track_row = False

    for row_number in range(
        widget.table.model().rowCount()
    ):

        industry_item = (
            widget.table.model().index(
                row_number,
                0,
            )
        )

        track_item = (
            widget.table.model().index(
                row_number,
                1,
            )
        )

        industry_name = (
            widget.table.model().data(
                industry_item
            )
        )

        track_name = (
            widget.table.model().data(
                track_item
            )
        )

        print(
            f"TABLE ROW {row_number}: "
            f"Industry='{industry_name}' | "
            f"Track='{track_name}'"
        )

        if (
            industry_name
            and not track_name
        ):

            found_zero_track_row = True

            print(
                "   >>> ZERO-TRACK TABLE ROW FOUND"
            )

    print()

    if found_zero_track_row:

        print(
            "PASS: QTableView contains a "
            "zero-track industry."
        )

    else:

        print(
            "FAIL: QTableView does NOT contain "
            "a zero-track industry."
        )

    return widget


def test_widget_refresh(widget):
    """
    Test 4:
    Explicitly call refresh() and verify that the
    zero-track industry survives the refresh.
    """

    print()
    print("=" * 70)
    print("TEST 4 - WIDGET REFRESH")
    print("=" * 70)

    print(
        "Calling widget.refresh()..."
    )

    widget.refresh()

    model = widget.table.model()

    print(
        f"Rows after refresh: "
        f"{model.rowCount()}"
    )

    found_zero_track_row = False

    for row_number in range(
        model.rowCount()
    ):

        industry_name = model.data(
            model.index(
                row_number,
                0,
            )
        )

        track_name = model.data(
            model.index(
                row_number,
                1,
            )
        )

        print(
            f"ROW {row_number}: "
            f"Industry='{industry_name}' | "
            f"Track='{track_name}'"
        )

        if (
            industry_name
            and not track_name
        ):

            found_zero_track_row = True

    print()

    if found_zero_track_row:

        print(
            "PASS: Zero-track industry survives "
            "widget.refresh()."
        )

    else:

        print(
            "FAIL: Zero-track industry disappears "
            "during widget.refresh()."
        )


def main():

    print()
    print("=" * 70)
    print("MODEL RAILROAD OPS")
    print("ZERO-TRACK INDUSTRY DIAGNOSTIC")
    print("=" * 70)

    # -----------------------------------------------------
    # Test database
    # -----------------------------------------------------

    print_database_state()

    # -----------------------------------------------------
    # Test model
    # -----------------------------------------------------

    model = test_table_model()

    # -----------------------------------------------------
    # Qt application
    # -----------------------------------------------------

    app = QApplication.instance()

    if app is None:

        app = QApplication(
            sys.argv
        )

    # -----------------------------------------------------
    # Test widget
    # -----------------------------------------------------

    widget = test_qt_widget(
        model
    )

    # -----------------------------------------------------
    # Test refresh
    # -----------------------------------------------------

    test_widget_refresh(
        widget
    )

    # -----------------------------------------------------
    # Final result
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print()

    print(
        "If Tests 1 and 2 PASS but Test 3 FAIL,"
    )

    print(
        "the problem is inside IndustryTracksWidget."
    )

    print()

    print(
        "If Test 3 PASS but the application does not "
        "show the industry,"
    )

    print(
        "the problem is in MainWindow/tab refresh "
        "or another part of the application."
    )

    print()

    print(
        "If Test 4 FAIL, the problem is occurring "
        "during widget.refresh()."
    )

    print()


if __name__ == "__main__":

    main()
