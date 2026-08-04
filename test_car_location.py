import sys
from pathlib import Path

# Add src folder to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.services.car_location_service import (
    CarLocationService
)

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car


def show_car(car_id):

    location = CarLocationService.get_car_location(car_id)

    print()
    print("=" * 40)

    if location:
        print(f"Car: {location['car']}")
        print(f"Industry: {location['industry']}")
        print(f"Track: {location['track']}")
        print(f"Spot: {location['spot']}")
    else:
        print("Car not found")

    print("=" * 40)


def main():

    # Show available cars
    session = SessionLocal()

    print("Available cars:")

    cars = session.query(Car).all()

    for car in cars:
        print(
            f"{car.id}: "
            f"{car.reporting_mark} {car.number}"
        )

    session.close()


    #
    # Test 1: Assign car to a spot
    #
    print()
    print("Assigning car to spot...")

    result = CarLocationService.assign_car_to_spot(
        car_id=2,
        spot_id=1,
    )

    if result:
        print("Assignment successful!")
    else:
        print("Assignment failed!")

    show_car(2)


    #
    # Test 2: Prevent duplicate spot assignment
    #
    print()
    print("Testing duplicate spot assignment...")

    result = CarLocationService.assign_car_to_spot(
        car_id=3,
        spot_id=1,
    )

    if result:
        print(
            "ERROR: Duplicate assignment allowed!"
        )
    else:
        print(
            "SUCCESS: Spot already occupied. "
            "Assignment blocked."
        )


    #
    # Test 3: Move car
    #
    print()
    print("Testing car move...")

    result = CarLocationService.move_car(
        car_id=2,
        new_spot_id=2,
    )

    if result:
        print("Move successful!")
    else:
        print("Move failed!")

    show_car(2)


    #
    # Test 4: Move into occupied spot
    #
    print()
    print("Testing move into occupied spot...")

    result = CarLocationService.move_car(
        car_id=3,
        new_spot_id=2,
    )

    if result:
        print(
            "ERROR: Move into occupied spot allowed!"
        )
    else:
        print(
            "SUCCESS: Move blocked. "
            "Destination spot occupied."
        )


    #
    # Cleanup
    #
    print()
    print("Cleaning up test location...")

    result = CarLocationService.clear_car_location(
        car_id=2
    )

    if result:
        print("Cleanup successful!")
    else:
        print("Cleanup failed!")

    show_car(2)


if __name__ == "__main__":
    main()