from sqlalchemy import select, func

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.industry import Industry


with SessionLocal() as session:

    duplicates = session.execute(
        select(
            Industry.name,
            func.count(Industry.id)
        )
        .group_by(Industry.name)
        .having(func.count(Industry.id) > 1)
    ).all()

    if not duplicates:
        print("No duplicate industries found")

    else:
        print("Duplicate industries found:")

        for name, count in duplicates:
            print(f"{name}: {count}")