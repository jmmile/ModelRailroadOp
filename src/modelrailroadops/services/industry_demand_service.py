from sqlalchemy import select
from sqlalchemy.orm import joinedload

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.spot import Spot
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.car_location_service import CarLocationService
from modelrailroadops.services.waybill_service import WaybillService


class IndustryDemandService:
    """Derive industry demand from open spots and their restrictions."""

    @staticmethod
    def get_open_demands():
        with SessionLocal() as session:
            reserved_spot_ids = set(session.execute(
                select(Waybill.destination_spot_id).where(
                    Waybill.destination_spot_id.is_not(None),
                    Waybill.status.in_(("ACTIVE", "IN_PROGRESS")),
                )
            ).scalars().all())
            busy_car_ids = set(session.execute(
                select(Waybill.car_id).where(
                    Waybill.status.in_(("ACTIVE", "IN_PROGRESS")),
                )
            ).scalars().all())
            spots = session.execute(
                select(Spot)
                .options(
                    joinedload(Spot.car),
                    joinedload(Spot.track).joinedload(IndustryTrack.industry),
                )
                .order_by(Spot.track_id, Spot.spot_number)
            ).unique().scalars().all()
            cars = session.execute(
                select(Car).order_by(Car.reporting_mark, Car.number)
            ).scalars().all()

            demands = []
            for spot in spots:
                if spot.car is not None or spot.id in reserved_spot_ids:
                    continue
                matches = []
                for car in cars:
                    if car.id in busy_car_ids:
                        continue
                    if (car.status or "").upper() not in ("EMPTY", "LOADED"):
                        continue
                    if not car.operating_location_id or not car.operating_track_id:
                        continue
                    valid, _message = CarLocationService.validate_car_for_spot(
                        car, spot
                    )
                    if valid:
                        matches.append({
                            "id": car.id,
                            "name": f"{car.reporting_mark} {car.number}",
                            "car_type": car.car_type or "Unknown",
                            "status": car.status or "Unknown",
                            "location": car.location or "Unassigned",
                        })
                industry = spot.track.industry
                requirements = []
                if spot.allowed_car_type:
                    requirements.append(spot.allowed_car_type)
                if spot.load_only:
                    requirements.append("Loaded")
                if spot.empty_only:
                    requirements.append("Empty")
                demands.append({
                    "spot_id": spot.id,
                    "town": industry.location or "Unassigned",
                    "industry": industry.name,
                    "track": spot.track.name,
                    "spot": spot.spot_number,
                    "requirements": ", ".join(requirements) or "Any car",
                    "matches": matches,
                })
            demands.sort(key=lambda row: (
                row["town"].casefold(),
                row["industry"].casefold(),
                row["track"].casefold(),
                row["spot"],
            ))
            return demands

    @staticmethod
    def create_waybill(spot_id, car_id, operations_session_id=None):
        with SessionLocal() as session:
            spot = session.get(Spot, spot_id)
            car = session.get(Car, car_id)
            if spot is None or car is None:
                return False, "The selected car or demand spot was not found."
            track = session.get(IndustryTrack, spot.track_id)
            industry = track.industry if track is not None else None
            if track is None or industry is None:
                return False, "The demand spot has no valid industry track."
            valid, message = CarLocationService.validate_car_for_spot(car, spot)
            if not valid:
                return False, message
            values = {
                "car_id": car.id,
                "operations_session_id": operations_session_id,
                "origin_location": car.location,
                "origin_location_id": car.operating_location_id,
                "origin_location_track_id": car.operating_track_id,
                "origin_spot_id": car.spot_id,
                "destination_industry_id": industry.id,
                "destination_track_id": track.id,
                "destination_spot_id": spot.id,
                "destination_location_id": industry.operating_location_id,
                "destination_location_track_id": track.operating_track_id,
                "load_state": car.status.upper(),
                "notes": "Generated from Industry Demand.",
            }
        return WaybillService.create(**values)
