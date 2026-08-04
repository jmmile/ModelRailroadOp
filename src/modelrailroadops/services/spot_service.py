from sqlalchemy import select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.spot import Spot


class SpotService:

    @staticmethod
    def get_by_track(track_id):

        with SessionLocal() as session:

            return (
                session.execute(
                    select(Spot)
                    .where(
                        Spot.track_id == track_id
                    )
                    .order_by(
                        Spot.spot_number
                    )
                )
                .scalars()
                .all()
            )


    @staticmethod
    def add(
        track_id,
        spot_number,
        max_length=None,
        allowed_car_type=None,
    ):

        with SessionLocal() as session:

            spot = Spot(
                track_id=track_id,
                spot_number=spot_number,
                max_length=max_length,
                allowed_car_type=allowed_car_type,
            )

            session.add(spot)
            session.commit()
            session.refresh(spot)

            return spot


    @staticmethod
    def delete(spot_id):

        with SessionLocal() as session:

            spot = session.get(
                Spot,
                spot_id
            )

            if not spot:
                return False

            session.delete(spot)
            session.commit()

            return True