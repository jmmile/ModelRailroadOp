import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import select, func

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car


with SessionLocal() as session:

    results = session.execute(
        select(
            Car.reporting_mark,
            Car.number,
            func.count(Car.id)
        )
        .group_by(
            Car.reporting_mark,
            Car.number
        )
        .having(
            func.count(Car.id) > 1
        )
    ).all()


    if not results:

        print("No duplicate cars found.")

    else:

        print("Duplicate cars:")
        
        for row in results:
            print(
                row[0],
                row[1],
                "count:",
                row[2]
            )