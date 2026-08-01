from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.industry_track import IndustryTrack


class IndustryTrackService:

    @staticmethod
    def get_all():
        with SessionLocal() as session:
            return (
                session.execute(
                    select(IndustryTrack)
                    .order_by(IndustryTrack.name)
                )
                .scalars()
                .all()
            )

    @staticmethod
    def get_by_id(track_id):
        with SessionLocal() as session:
            return session.get(IndustryTrack, track_id)

    @staticmethod
    def get_by_industry(industry_id):
        with SessionLocal() as session:
            return (
                session.execute(
                    select(IndustryTrack)
                    .where(
                        IndustryTrack.industry_id == industry_id
                    )
                    .order_by(IndustryTrack.name)
                )
                .scalars()
                .all()
            )

    @staticmethod
    def add(industry_id, name, spots):
        with SessionLocal() as session:
            track = IndustryTrack(
                industry_id=industry_id,
                name=name,
                spots=spots,
            )

            session.add(track)
            session.commit()
            session.refresh(track)

            return track

    @staticmethod
    def update(track_id, name=None, spots=None):
        with SessionLocal() as session:
            track = session.get(IndustryTrack, track_id)

            if not track:
                return None

            if name is not None:
                track.name = name

            if spots is not None:
                track.spots = spots

            session.commit()
            session.refresh(track)

            return track

    @staticmethod
    def delete(track_id):
        with SessionLocal() as session:
            track = session.get(IndustryTrack, track_id)

            if not track:
                return False

            session.delete(track)
            session.commit()

            return True