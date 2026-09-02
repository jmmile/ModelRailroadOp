import sys
from pathlib import Path

# Add src folder to Python path.
sys.path.insert(
    0,
    str(Path(__file__).parent / "src"),
)

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car


def clean_car_locations():
    """
    Find cars that have no structured Industry/Track/Spot
    assignment but still contain an old legacy location.

    These cars are reset to:

        location = "Unassigned"

    The structured location fields are not changed.
    """

    session = SessionLocal()

    try:
        cars = (
            session.query(Car)
            .filter(
                Car.industry_id.is_(None),
                Car.track_id.is_(None),
                Car.spot_id.is_(None),
                Car.location.is_not(None),
                Car.location != "Unassigned",
            )
            .order_by(
                Car.id,
            )
            .all()
        )

        if not cars:
            print("No inconsistent car locations were found.")
            return

        print("=" * 60)
        print("CAR LOCATION CLEANUP")
        print("=" * 60)
        print()

        print(
            f"Found {len(cars)} car(s) with stale "
            "legacy locations:"
        )
        print()

        for car in cars:
            print(
                f"  Car ID {car.id}: "
                f"{car.reporting_mark} {car.number}"
            )
            print(
                f"    Current location: "
                f"{car.location}"
            )
            print(
                "    Structured location: "
                "Industry=None, Track=None, Spot=None"
            )
            print(
                "    New location: Unassigned"
            )
            print()

        print(
            "These cars will have ONLY their "
            "location field changed."
        )
        print()

        response = input(
            "Proceed with cleanup? (Y/N): "
        ).strip().casefold()

        if response != "y":
            print()
            print("Cleanup cancelled.")
            return

        for car in cars:
            car.location = "Unassigned"

        session.commit()

        print()
        print("=" * 60)
        print("CLEANUP COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print()
        print(
            f"Updated {len(cars)} car(s)."
        )
        print()
        print(
            "Only the legacy location field "
            "was changed."
        )
        print(
            "Industry, Track, and Spot assignments "
            "were not changed."
        )

    except Exception as exc:
        session.rollback()

        print()
        print("=" * 60)
        print("ERROR: NO CHANGES WERE SAVED")
        print("=" * 60)
        print()
        print(exc)

    finally:
        session.close()


if __name__ == "__main__":
    clean_car_locations()