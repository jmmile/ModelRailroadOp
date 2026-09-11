from sqlalchemy import select
from sqlalchemy.orm import selectinload

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.car import Car
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.spot import Spot
from modelrailroadops.models.train_route import TrainRoute
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.car_location_service import CarLocationService


class LocationService:
    LOCATION_TYPES = (
        "YARD",
        "STAGING",
        "INTERCHANGE",
        "STATION",
        "INDUSTRY",
        "OTHER",
    )

    TRACK_TYPES = (
        "ARRIVAL",
        "DEPARTURE",
        "CLASSIFICATION",
        "YARD",
        "STAGING",
        "INTERCHANGE",
        "INDUSTRY",
        "SIDING",
        "MAIN",
        "OTHER",
    )

    TRAFFIC_USES = (
        "INBOUND",
        "OUTBOUND",
        "BOTH",
    )

    @staticmethod
    def move_car_on_track(car_id, direction):
        """Move a car one position left or right on its current track."""

        if direction not in (-1, 1):
            return False, "Track position direction must be left or right."

        with SessionLocal() as session:
            car = session.get(Car, car_id)
            if car is None:
                return False, "Car not found."
            if car.industry_id is not None:
                if car.track_id is None or car.spot_id is None:
                    return False, "The car does not have an industry spot."

                spots = session.execute(
                    select(Spot)
                    .where(Spot.track_id == car.track_id)
                    .order_by(Spot.spot_number)
                ).scalars().all()
                current_index = next(
                    (
                        index for index, spot in enumerate(spots)
                        if spot.id == car.spot_id
                    ),
                    None,
                )
                if current_index is None:
                    return False, "The car's industry spot could not be found."

                target_index = current_index + direction
                if target_index < 0 or target_index >= len(spots):
                    end_name = "left" if direction < 0 else "right"
                    return False, f"The car is already at the {end_name} end."

                current_spot = spots[current_index]
                target_spot = spots[target_index]
                target_car = session.execute(
                    select(Car).where(Car.spot_id == target_spot.id)
                ).scalars().first()

                valid, message = CarLocationService.validate_car_for_spot(
                    car,
                    target_spot,
                )
                if not valid:
                    return False, message
                if target_car is not None:
                    valid, message = CarLocationService.validate_car_for_spot(
                        target_car,
                        current_spot,
                    )
                    if not valid:
                        return False, message

                track = session.get(IndustryTrack, car.track_id)
                industry = session.get(Industry, car.industry_id)
                if track is None or industry is None:
                    return False, "The car's industry track could not be found."

                car.spot_id = target_spot.id
                car.location = (
                    f"{industry.name} - {track.name} - "
                    f"Spot {target_spot.spot_number}"
                )
                if target_car is not None:
                    target_car.spot_id = current_spot.id
                    target_car.location = (
                        f"{industry.name} - {track.name} - "
                        f"Spot {current_spot.spot_number}"
                    )
                session.commit()
                return True, "Car industry spot updated."

            if car.operating_track_id is None:
                return False, "The car is not on a general railroad track."

            cars = session.execute(
                select(Car).where(
                    Car.operating_track_id == car.operating_track_id,
                    Car.industry_id.is_(None),
                )
            ).scalars().all()
            cars.sort(key=lambda item: (
                item.operating_track_position
                if item.operating_track_position is not None
                else 999999,
                item.id,
            ))

            current_index = next(
                (
                    index for index, item in enumerate(cars)
                    if item.id == car_id
                ),
                None,
            )
            if current_index is None:
                return False, "Car position could not be found."

            target_index = current_index + direction
            if target_index < 0 or target_index >= len(cars):
                end_name = "left" if direction < 0 else "right"
                return False, f"The car is already at the {end_name} end."

            for position, item in enumerate(cars, start=1):
                item.operating_track_position = position

            current_car = cars[current_index]
            target_car = cars[target_index]
            (
                current_car.operating_track_position,
                target_car.operating_track_position,
            ) = (
                target_car.operating_track_position,
                current_car.operating_track_position,
            )
            session.commit()

            return True, "Car track position updated."

    @staticmethod
    def reorder_car_on_track(car_id, insertion_index):
        """Place a car at a same-track insertion point or industry spot."""

        if not isinstance(insertion_index, int):
            return False, "The requested track position is invalid."

        with SessionLocal() as session:
            car = session.get(Car, car_id)
            if car is None:
                return False, "Car not found."
            if car.industry_id is not None:
                if car.track_id is None or car.spot_id is None:
                    return False, "The car does not have an industry spot."

                spots = session.execute(
                    select(Spot)
                    .where(Spot.track_id == car.track_id)
                    .order_by(Spot.spot_number)
                ).scalars().all()
                if not spots:
                    return False, "The industry track has no spots."

                target_index = max(
                    0,
                    min(insertion_index, len(spots) - 1),
                )
                target_spot = spots[target_index]
                if target_spot.id == car.spot_id:
                    return True, "Car is already in that industry spot."

                current_spot = session.get(Spot, car.spot_id)
                target_car = session.execute(
                    select(Car).where(Car.spot_id == target_spot.id)
                ).scalars().first()
                if current_spot is None:
                    return False, "The car's industry spot could not be found."

                valid, message = CarLocationService.validate_car_for_spot(
                    car,
                    target_spot,
                )
                if not valid:
                    return False, message
                if target_car is not None:
                    valid, message = CarLocationService.validate_car_for_spot(
                        target_car,
                        current_spot,
                    )
                    if not valid:
                        return False, message

                track = session.get(IndustryTrack, car.track_id)
                industry = session.get(Industry, car.industry_id)
                if track is None or industry is None:
                    return False, "The car's industry track could not be found."

                car.spot_id = target_spot.id
                car.location = (
                    f"{industry.name} - {track.name} - "
                    f"Spot {target_spot.spot_number}"
                )
                if target_car is not None:
                    target_car.spot_id = current_spot.id
                    target_car.location = (
                        f"{industry.name} - {track.name} - "
                        f"Spot {current_spot.spot_number}"
                    )
                session.commit()
                return True, "Car industry spot updated."

            if car.operating_track_id is None:
                return False, "The car is not on a general railroad track."

            cars = session.execute(
                select(Car).where(
                    Car.operating_track_id == car.operating_track_id,
                    Car.industry_id.is_(None),
                )
            ).scalars().all()
            cars.sort(key=lambda item: (
                item.operating_track_position
                if item.operating_track_position is not None
                else 999999,
                item.id,
            ))

            current_index = next(
                (
                    index for index, item in enumerate(cars)
                    if item.id == car_id
                ),
                None,
            )
            if current_index is None:
                return False, "Car position could not be found."

            requested_index = max(0, min(insertion_index, len(cars)))
            moving_car = cars.pop(current_index)
            if current_index < requested_index:
                requested_index -= 1
            requested_index = max(0, min(requested_index, len(cars)))
            cars.insert(requested_index, moving_car)

            for position, item in enumerate(cars, start=1):
                item.operating_track_position = position
            session.commit()

            return True, "Car track position updated."

    @staticmethod
    def get_all():

        with SessionLocal() as session:

            return (
                session.execute(
                    select(Location)
                    .options(
                        selectinload(Location.tracks).selectinload(
                            LocationTrack.industry_tracks
                        ),
                        selectinload(Location.tracks).selectinload(
                            LocationTrack.cars
                        ),
                        selectinload(Location.industries),
                    )
                    .order_by(Location.name)
                )
                .scalars()
                .all()
            )

    @staticmethod
    def create(
        name,
        location_type,
        notes=None,
        active=True,
    ):

        name = name.strip() if name else ""
        location_type = (
            location_type.strip().upper()
            if location_type
            else "OTHER"
        )

        if not name:
            return False, "Location name is required."

        if location_type not in LocationService.LOCATION_TYPES:
            return False, "Invalid location type."

        with SessionLocal() as session:

            existing = (
                session.execute(
                    select(Location).where(Location.name == name)
                )
                .scalars()
                .first()
            )

            if existing is not None:
                return False, f"Location '{name}' already exists."

            location = Location(
                name=name,
                location_type=location_type,
                notes=notes.strip() if notes else None,
                active=bool(active),
            )

            session.add(location)
            session.commit()
            session.refresh(location)

            return True, location

    @staticmethod
    def update(
        location_id,
        name,
        location_type,
        notes=None,
        active=True,
    ):

        name = name.strip() if name else ""
        location_type = (
            location_type.strip().upper()
            if location_type
            else "OTHER"
        )

        if not name:
            return False, "Location name is required."

        if location_type not in LocationService.LOCATION_TYPES:
            return False, "Invalid location type."

        with SessionLocal() as session:

            location = session.get(Location, location_id)

            if location is None:
                return False, "Location not found."

            if location.industries and (
                name != location.name
                or location_type != "INDUSTRY"
            ):
                return (
                    False,
                    "Industry locations must be renamed in the Industries tab.",
                )

            duplicate = (
                session.execute(
                    select(Location).where(
                        Location.name == name,
                        Location.id != location_id,
                    )
                )
                .scalars()
                .first()
            )

            if duplicate is not None:
                return False, f"Location '{name}' already exists."

            location.name = name
            location.location_type = location_type
            location.notes = notes.strip() if notes else None
            location.active = bool(active)

            session.commit()
            session.refresh(location)

            return True, location

    @staticmethod
    def set_active(
        location_id,
        active,
    ):

        with SessionLocal() as session:

            location = session.get(Location, location_id)

            if location is None:
                return False, "Location not found."

            location.active = bool(active)
            session.commit()

            return True, location

    @staticmethod
    def delete(
        location_id,
    ):

        with SessionLocal() as session:

            location = session.get(Location, location_id)

            if location is None:
                return False, "Location not found."

            industry = (
                session.execute(
                    select(Industry).where(
                        Industry.operating_location_id == location_id
                    )
                )
                .scalars()
                .first()
            )

            if industry is not None:
                return (
                    False,
                    "This location belongs to an Industry. "
                    "Delete or update it from the Industries tab.",
                )

            route_stop = (
                session.execute(
                    select(TrainRoute).where(
                        TrainRoute.location_id == location_id
                    )
                )
                .scalars()
                .first()
            )

            if route_stop is not None:
                return (
                    False,
                    "This location is used by one or more Train route stops. "
                    "Reassign or delete those route stops first.",
                )

            car = (
                session.execute(
                    select(Car).where(
                        Car.operating_location_id == location_id
                    )
                )
                .scalars()
                .first()
            )

            if car is not None:
                return (
                    False,
                    "This location contains one or more cars. "
                    "Move or clear those cars first.",
                )

            waybill = (
                session.execute(
                    select(Waybill).where(
                        (Waybill.origin_location_id == location_id)
                        | (Waybill.destination_location_id == location_id)
                    )
                )
                .scalars()
                .first()
            )

            if waybill is not None:
                return (
                    False,
                    "This location is used by one or more Waybills. "
                    "Reassign or delete those Waybills first.",
                )

            linked_industry_track = (
                session.execute(
                    select(IndustryTrack)
                    .join(
                        LocationTrack,
                        IndustryTrack.operating_track_id
                        == LocationTrack.id,
                    )
                    .where(
                        LocationTrack.location_id == location_id
                    )
                )
                .scalars()
                .first()
            )

            if linked_industry_track is not None:
                return (
                    False,
                    "This location contains an Industry track. "
                    "Update it from the Industry Tracks tab first.",
                )

            session.delete(location)

            try:
                session.commit()
            except Exception as exc:
                session.rollback()
                return False, str(exc)

            return True, "Location deleted."

    @staticmethod
    def create_track(
        location_id,
        name,
        track_type,
        traffic_use="BOTH",
        capacity=None,
        notes=None,
        active=True,
    ):

        return LocationService._save_track(
            None,
            location_id,
            name,
            track_type,
            traffic_use,
            capacity,
            notes,
            active,
        )

    @staticmethod
    def update_track(
        track_id,
        location_id,
        name,
        track_type,
        traffic_use="BOTH",
        capacity=None,
        notes=None,
        active=True,
    ):

        return LocationService._save_track(
            track_id,
            location_id,
            name,
            track_type,
            traffic_use,
            capacity,
            notes,
            active,
        )

    @staticmethod
    def _save_track(
        track_id,
        location_id,
        name,
        track_type,
        traffic_use,
        capacity,
        notes,
        active,
    ):

        name = name.strip() if name else ""
        track_type = (
            track_type.strip().upper()
            if track_type
            else "OTHER"
        )

        traffic_use = (
            traffic_use.strip().upper()
            if traffic_use
            else "BOTH"
        )

        if not name:
            return False, "Track name is required."

        if track_type not in LocationService.TRACK_TYPES:
            return False, "Invalid track type."

        if traffic_use not in LocationService.TRAFFIC_USES:
            return False, "Invalid traffic use."

        if capacity is not None and capacity < 0:
            return False, "Capacity cannot be negative."

        with SessionLocal() as session:

            location = session.get(Location, location_id)

            if location is None:
                return False, "Location not found."

            duplicate_query = select(LocationTrack).where(
                LocationTrack.location_id == location_id,
                LocationTrack.name == name,
            )

            if track_id is not None:
                duplicate_query = duplicate_query.where(
                    LocationTrack.id != track_id
                )

            duplicate = (
                session.execute(duplicate_query)
                .scalars()
                .first()
            )

            if duplicate is not None:
                return False, f"Track '{name}' already exists at this location."

            if track_id is None:
                track = LocationTrack(location_id=location_id)
                session.add(track)
            else:
                track = session.get(LocationTrack, track_id)
                if track is None:
                    return False, "Track not found."

            track.name = name
            track.track_type = track_type
            track.traffic_use = traffic_use
            track.capacity = capacity
            track.notes = notes.strip() if notes else None
            track.active = bool(active)

            session.commit()
            session.refresh(track)

            return True, track

    @staticmethod
    def delete_track(
        track_id,
    ):

        with SessionLocal() as session:

            track = session.get(LocationTrack, track_id)

            if track is None:
                return False, "Track not found."

            linked = (
                session.execute(
                    select(IndustryTrack).where(
                        IndustryTrack.operating_track_id == track_id
                    )
                )
                .scalars()
                .first()
            )

            if linked is not None:
                return (
                    False,
                    "Industry tracks must be deleted in the Industry Tracks tab.",
                )

            car = (
                session.execute(
                    select(Car).where(
                        Car.operating_track_id == track_id
                    )
                )
                .scalars()
                .first()
            )

            if car is not None:
                return (
                    False,
                    "This track contains one or more cars. "
                    "Move or clear those cars first.",
                )

            waybill = (
                session.execute(
                    select(Waybill).where(
                        (Waybill.origin_location_track_id == track_id)
                        | (Waybill.destination_location_track_id == track_id)
                    )
                )
                .scalars()
                .first()
            )

            if waybill is not None:
                return (
                    False,
                    "This track is used by one or more Waybills. "
                    "Reassign or delete those Waybills first.",
                )

            session.delete(track)
            session.commit()

            return True, "Track deleted."
