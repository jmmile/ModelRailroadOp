
import sys
from pathlib import Path


#
# Add src folder to Python path
#

sys.path.insert(
    0,
    str(Path(__file__).parent / "src")
)


from sqlalchemy import select

from modelrailroadops.database.database import (
    SessionLocal,
)

from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot


def check_car_locations():

    print()
    print("=" * 70)
    print(" Model Railroad Operations")
    print(" Car Location Check")
    print("=" * 70)
    print()

    problems = []

    with SessionLocal() as session:

        cars = (
            session.execute(
                select(Car).order_by(
                    Car.reporting_mark,
                    Car.number,
                )
            )
            .scalars()
            .all()
        )

        print(
            f"Checking {len(cars)} cars..."
        )

        print()

        for car in cars:

            #
            # -------------------------------------------------
            # CASE 1
            # Completely unassigned car.
            # -------------------------------------------------
            #

            if (
                car.industry_id is None
                and car.track_id is None
                and car.spot_id is None
            ):

                current_location = (
                    car.location or ""
                ).strip()

                if (
                    current_location
                    and current_location.lower()
                    != "unassigned"
                ):

                    problems.append(
                        {
                            "car": (
                                f"{car.reporting_mark} "
                                f"{car.number}"
                            ),
                            "type": "Old Location",
                            "location": current_location,
                            "industry": "",
                            "track": "",
                            "spot": "",
                            "expected": "Unassigned",
                        }
                    )

                continue

            #
            # -------------------------------------------------
            # CASE 2
            # Car has a spot assignment.
            # -------------------------------------------------
            #

            if car.spot_id is not None:

                spot = session.get(
                    Spot,
                    car.spot_id,
                )

                track = None
                industry = None

                if spot is not None:

                    track = session.get(
                        IndustryTrack,
                        spot.track_id,
                    )

                if track is not None:

                    industry = session.get(
                        Industry,
                        track.industry_id,
                    )

                #
                # Invalid structured assignment.
                #

                if (
                    spot is None
                    or track is None
                    or industry is None
                ):

                    problems.append(
                        {
                            "car": (
                                f"{car.reporting_mark} "
                                f"{car.number}"
                            ),
                            "type": "Invalid Assignment",
                            "location": (
                                car.location or ""
                            ),
                            "industry": (
                                str(car.industry_id)
                                if car.industry_id
                                is not None
                                else ""
                            ),
                            "track": (
                                str(car.track_id)
                                if car.track_id
                                is not None
                                else ""
                            ),
                            "spot": (
                                str(car.spot_id)
                                if car.spot_id
                                is not None
                                else ""
                            ),
                            "expected": (
                                "Valid Industry / Track / Spot"
                            ),
                        }
                    )

                    continue

                #
                # Expected location text.
                #

                expected_location = (
                    f"{industry.name} - "
                    f"{track.name} - "
                    f"Spot "
                    f"{spot.spot_number}"
                )

                current_location = (
                    car.location or ""
                ).strip()

                #
                # Location text does not match
                # structured assignment.
                #

                if (
                    current_location
                    != expected_location
                ):

                    problems.append(
                        {
                            "car": (
                                f"{car.reporting_mark} "
                                f"{car.number}"
                            ),
                            "type": "Location Mismatch",
                            "location": current_location,
                            "industry": industry.name,
                            "track": track.name,
                            "spot": str(
                                spot.spot_number
                            ),
                            "expected": expected_location,
                        }
                    )

                continue

            #
            # -------------------------------------------------
            # CASE 3
            # Industry and/or track exists but there
            # is no spot.
            # -------------------------------------------------
            #

            industry = None
            track = None

            if car.industry_id is not None:

                industry = session.get(
                    Industry,
                    car.industry_id,
                )

            if car.track_id is not None:

                track = session.get(
                    IndustryTrack,
                    car.track_id,
                )

            #
            # Build expected location.
            #

            if (
                industry is not None
                and track is not None
            ):

                expected_location = (
                    f"{industry.name} - "
                    f"{track.name}"
                )

            elif industry is not None:

                expected_location = (
                    industry.name
                )

            elif track is not None:

                expected_location = (
                    track.name
                )

            else:

                expected_location = (
                    "Unassigned"
                )

            current_location = (
                car.location or ""
            ).strip()

            if (
                current_location
                != expected_location
            ):

                problems.append(
                    {
                        "car": (
                            f"{car.reporting_mark} "
                            f"{car.number}"
                        ),
                        "type": "Location Mismatch",
                        "location": current_location,
                        "industry": (
                            industry.name
                            if industry is not None
                            else ""
                        ),
                        "track": (
                            track.name
                            if track is not None
                            else ""
                        ),
                        "spot": "",
                        "expected": expected_location,
                    }
                )

    #
    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------
    #

    print("=" * 70)
    print(" Results")
    print("=" * 70)
    print()

    if not problems:

        print(
            "No location problems were found."
        )

        print()

        return

    print(
        f"Found {len(problems)} car(s) "
        f"with location problems."
    )

    print()

    #
    # Print every problem.
    #

    for number, problem in enumerate(
        problems,
        start=1
    ):

        print("=" * 70)
        print(
            f" PROBLEM {number} OF {len(problems)}"
        )
        print("=" * 70)

        print()

        print(
            f"Car:       {problem['car']}"
        )

        print(
            f"Problem:   {problem['type']}"
        )

        print(
            f"Location:  "
            f"{problem['location'] or '(blank)'}"
        )

        print(
            f"Industry:  "
            f"{problem['industry'] or '(none)'}"
        )

        print(
            f"Track:     "
            f"{problem['track'] or '(none)'}"
        )

        print(
            f"Spot:      "
            f"{problem['spot'] or '(none)'}"
        )

        print(
            f"Expected:  "
            f"{problem['expected']}"
        )

        print()

    print("=" * 70)
    print(
        "IMPORTANT: No database changes were made."
    )
    print(
        "This script is read-only."
    )
    print("=" * 70)
    print()


if __name__ == "__main__":

    check_car_locations()
