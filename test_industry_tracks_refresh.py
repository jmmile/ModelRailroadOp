
import sys
from pathlib import Path


# ---------------------------------------------------------
# Make src available
# ---------------------------------------------------------

sys.path.insert(
    0,
    str(Path(__file__).parent / "src")
)


# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------

from sqlalchemy import select

from modelrailroadops.database.database import (
    SessionLocal,
)

from modelrailroadops.models.industry import (
    Industry,
)

from modelrailroadops.models.industry_track import (
    IndustryTrack,
)

from modelrailroadops.services.industry_service import (
    IndustryService,
)

from modelrailroadops.ui.models.industry_track_table_model import (
    IndustryTrackTableModel,
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

print()
print("=" * 70)
print(" MODEL RAILROAD OPERATIONS")
print(" INDUSTRY TRACK REFRESH DIAGNOSTIC")
print("=" * 70)
print()


# ---------------------------------------------------------
# TEST 1
# Direct database query
# ---------------------------------------------------------

print("TEST 1: Direct database query")
print("-" * 70)

with SessionLocal() as session:

    industries = (
        session.execute(
            select(Industry)
            .order_by(
                Industry.name
            )
        )
        .scalars()
        .all()
    )

    print(
        f"Industries found directly in database: "
        f"{len(industries)}"
    )

    for industry in industries:

        print(
            f"  ID={industry.id} | "
            f"Name={industry.name!r}"
        )


print()


# ---------------------------------------------------------
# TEST 2
# Direct industry_tracks query
# ---------------------------------------------------------

print("TEST 2: Direct industry_tracks query")
print("-" * 70)

with SessionLocal() as session:

    tracks = (
        session.execute(
            select(IndustryTrack)
            .order_by(
                IndustryTrack.industry_id,
                IndustryTrack.name,
            )
        )
        .scalars()
        .all()
    )

    print(
        f"Industry tracks found directly: "
        f"{len(tracks)}"
    )

    for track in tracks:

        print(
            f"  ID={track.id} | "
            f"Industry ID={track.industry_id} | "
            f"Name={track.name!r}"
        )


print()


# ---------------------------------------------------------
# TEST 3
# IndustryService
# ---------------------------------------------------------

print("TEST 3: IndustryService.get_all()")
print("-" * 70)

try:

    service_industries = (
        IndustryService.get_all()
    )

    print(
        f"IndustryService returned: "
        f"{len(service_industries)}"
    )

    for industry in service_industries:

        print(
            f"  ID={industry.id} | "
            f"Name={industry.name!r} | "
            f"Tracks={len(industry.tracks)}"
        )

        for track in industry.tracks:

            print(
                f"      Track ID={track.id} | "
                f"Name={track.name!r}"
            )

except Exception as ex:

    print()
    print("ERROR IN IndustryService.get_all()")
    print(
        f"{type(ex).__name__}: {ex}"
    )


print()


# ---------------------------------------------------------
# TEST 4
# IndustryTrackTableModel
# ---------------------------------------------------------

print("TEST 4: IndustryTrackTableModel.refresh()")
print("-" * 70)

try:

    model = IndustryTrackTableModel()

    print(
        f"Model rows: "
        f"{model.rowCount()}"
    )

    print(
        f"Model columns: "
        f"{model.columnCount()}"
    )

    print()

    if not model.tracks:

        print(
            "MODEL CONTAINS NO ROWS."
        )

    else:

        for row_number, row in enumerate(
            model.tracks
        ):

            print(
                f"ROW {row_number}:"
            )

            print(
                f"  Industry: "
                f"{row['industry_name']!r}"
            )

            print(
                f"  Track: "
                f"{row['track_name']!r}"
            )

            print(
                f"  Spots: "
                f"{row['spot_total']}"
            )

            print(
                f"  Occupied: "
                f"{row['spot_occupied']}"
            )

            print(
                f"  Available: "
                f"{row['spot_available']}"
            )

            industry = row["industry"]

            if industry is not None:

                print(
                    f"  Industry ID: "
                    f"{industry.id}"
                )

            track = row["track"]

            if track is None:

                print(
                    "  Track object: None"
                )

            else:

                print(
                    f"  Track ID: "
                    f"{track.id}"
                )

            print()

except Exception as ex:

    print()
    print(
        "ERROR CREATING IndustryTrackTableModel"
    )

    print(
        f"{type(ex).__name__}: {ex}"
    )


# ---------------------------------------------------------
# TEST 5
# Verify model display data
# ---------------------------------------------------------

print("TEST 5: Model display data")
print("-" * 70)

try:

    model = IndustryTrackTableModel()

    for row in range(
        model.rowCount()
    ):

        values = []

        for column in range(
            model.columnCount()
        ):

            index = model.index(
                row,
                column
            )

            values.append(
                model.data(
                    index,
                    0
                )
            )

        print(
            f"Row {row}: {values}"
        )

except Exception as ex:

    print(
        f"{type(ex).__name__}: {ex}"
    )


# ---------------------------------------------------------
# Finished
# ---------------------------------------------------------

print()
print("=" * 70)
print(" DIAGNOSTIC COMPLETE")
print("=" * 70)
print()