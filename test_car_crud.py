import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.services.car_service import CarService


print("Adding test car...")

car = CarService.add(
    "UP",
    "19999",
    "Union Pacific",
    "Gondola",
    "Active",
    "Portland Yard"
)

if car:
    print(f"Added: {car.reporting_mark} {car.number}")
else:
    print("Duplicate car not added.")


print("\nCurrent cars:")

cars = CarService.get_all()

for car in cars:
    print(
        car.reporting_mark,
        car.number,
        car.car_type,
        car.location
    )

print(f"\nTotal cars: {len(cars)}")