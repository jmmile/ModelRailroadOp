from sqlalchemy import select
from sqlalchemy.orm import selectinload

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.car import Car
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.train_route import TrainRoute
from modelrailroadops.models.waybill import Waybill


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
    def get_all():

        with SessionLocal() as session:

            return (
                session.execute(
                    select(Location)
                    .options(
                        selectinload(Location.tracks).selectinload(
                            LocationTrack.industry_tracks
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
