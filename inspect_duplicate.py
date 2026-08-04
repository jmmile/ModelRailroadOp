from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.industry import Industry
from sqlalchemy import select
from sqlalchemy.orm import selectinload


with SessionLocal() as session:

    industries = session.execute(
        select(Industry)
        .where(Industry.name == "Wilhauser Lumber Company")
        .options(selectinload(Industry.tracks))
    ).scalars().all()

    for industry in industries:
        print("\nIndustry ID:", industry.id)
        print("Name:", industry.name)
        print("Railroad:", industry.railroad)
        print("Location:", industry.location)
        print("Notes:", industry.notes)

        print("Tracks:")
        for track in industry.tracks:
            print(
                f"  {track.name} - {track.spots} spots (Track ID {track.id})"
            )