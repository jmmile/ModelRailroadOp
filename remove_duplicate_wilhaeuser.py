from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack


with SessionLocal() as session:

    # Remove duplicate tracks
    duplicate_tracks = (
        session.query(IndustryTrack)
        .filter(
            IndustryTrack.industry_id == 2
        )
        .all()
    )

    for track in duplicate_tracks:
        print(
            f"Deleting duplicate track: {track.name} "
            f"(ID {track.id})"
        )
        session.delete(track)

    # Remove duplicate industry
    duplicate_industry = session.get(
        Industry,
        2
    )

    if duplicate_industry:
        print(
            f"Deleting duplicate industry: "
            f"{duplicate_industry.name} "
            f"(ID {duplicate_industry.id})"
        )
        session.delete(duplicate_industry)

    session.commit()

print("Duplicate cleanup complete")