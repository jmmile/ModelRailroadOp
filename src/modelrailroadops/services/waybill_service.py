from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car
from modelrailroadops.models.industry import Industry
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.location import Location
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.spot import Spot
from modelrailroadops.models.waybill import Waybill


class WaybillService:
    """Create, manage, and complete Waybills."""

    @staticmethod
    def normalize_location_text(value):
        return "" if value is None else str(value).strip()

    @staticmethod
    def validate_load_details(
        car_id,
        load_state,
        cargo_weight_lbs,
        allow_unspecified=False,
    ):
        """Validate and normalize a Waybill's load and weight details."""

        normalized_state = (
            str(load_state).strip().upper()
            if load_state
            else None
        )

        if normalized_state is None:
            if allow_unspecified:
                return True, "", None, None
            return False, "Please select Loaded or Empty.", None, None

        if normalized_state not in {"LOADED", "EMPTY"}:
            return False, "Load state must be Loaded or Empty.", None, None

        if normalized_state == "EMPTY":
            return True, "", normalized_state, 0

        try:
            normalized_cargo_weight = int(cargo_weight_lbs)
        except (TypeError, ValueError):
            return (
                False,
                "Loaded cars require a whole-number cargo weight in pounds.",
                None,
                None,
            )

        if normalized_cargo_weight <= 0:
            return False, "Cargo weight must be greater than zero.", None, None

        with SessionLocal() as session:
            car = session.get(Car, car_id)

            if car is None:
                return False, "Car not found.", None, None

            if (
                car.load_limit_lbs is not None
                and normalized_cargo_weight > car.load_limit_lbs
            ):
                return (
                    False,
                    "Cargo weight cannot exceed the car's load limit of "
                    f"{car.load_limit_lbs:,} lb.",
                    None,
                    None,
                )

        return True, "", normalized_state, normalized_cargo_weight

    @staticmethod
    def _waybill_load_options():
        return (
            joinedload(Waybill.car),
            joinedload(Waybill.operations_session),
            joinedload(Waybill.origin_industry),
            joinedload(Waybill.origin_track),
            joinedload(Waybill.origin_spot),
            joinedload(Waybill.origin_operating_location),
            joinedload(Waybill.origin_operating_track),
            joinedload(Waybill.destination_industry),
            joinedload(Waybill.destination_track),
            joinedload(Waybill.destination_spot),
            joinedload(Waybill.destination_operating_location),
            joinedload(Waybill.destination_operating_track),
        )

    @staticmethod
    def validate_operations_session(operations_session_id):
        if operations_session_id is None:
            return True, ""
        with SessionLocal() as session:
            operations_session = session.get(
                OperationsSession, operations_session_id
            )
            if operations_session is None:
                return False, "Operations session not found."
            if operations_session.status == "COMPLETED":
                return False, (
                    "A completed operations session cannot be assigned "
                    "to a waybill."
                )
            if operations_session.status == "CANCELLED":
                return False, (
                    "A cancelled operations session cannot be assigned "
                    "to a waybill."
                )
        return True, ""

    @staticmethod
    def validate_location(industry_id, track_id, spot_id):
        with SessionLocal() as session:
            industry = session.get(Industry, industry_id)
            if industry is None:
                return False, "Industry not found."
            track = session.get(IndustryTrack, track_id)
            if track is None:
                return False, "Industry track not found."
            if track.industry_id != industry.id:
                return False, (
                    "The selected track does not belong to the selected "
                    "industry."
                )
            spot = session.get(Spot, spot_id)
            if spot is None:
                return False, "Spot not found."
            if spot.track_id != track.id:
                return False, (
                    "The selected spot does not belong to the selected "
                    "track."
                )
        return True, ""

    @staticmethod
    def validate_car_type_for_spot(car_id, spot_id):
        with SessionLocal() as session:
            car = session.get(Car, car_id)
            if car is None:
                return False, "Car not found."
            spot = session.get(Spot, spot_id)
            if spot is None:
                return False, "Spot not found."
            allowed_car_type = WaybillService.normalize_location_text(
                spot.allowed_car_type
            )
            if not allowed_car_type:
                return True, ""
            car_type = WaybillService.normalize_location_text(car.car_type)
            if not car_type:
                return False, (
                    f"Car {car.reporting_mark} {car.number} does not have a "
                    f"car type assigned and cannot be placed in spot "
                    f"{spot.spot_number}, which requires {allowed_car_type}."
                )
            if car_type.casefold() != allowed_car_type.casefold():
                return False, (
                    f"Car {car.reporting_mark} {car.number} is a {car_type}, "
                    f"but spot {spot.spot_number} requires "
                    f"{allowed_car_type}."
                )
        return True, ""

    @staticmethod
    def _resolve_general_endpoint(location_id, location_track_id, spot_id):
        """Validate a Location/Track endpoint and return legacy links."""

        if location_id is None:
            return False, "Location is required."
        if location_track_id is None:
            return False, "Track is required."

        with SessionLocal() as session:
            location = session.get(Location, location_id)
            track = session.get(LocationTrack, location_track_id)

            if location is None:
                return False, "Location not found."
            if track is None:
                return False, "Track not found."
            if track.location_id != location.id:
                return False, (
                    "The selected track does not belong to the selected "
                    "location."
                )
            if not location.active or not track.active:
                return False, "Location and track must be active."

            industry_track = session.execute(
                select(IndustryTrack).where(
                    IndustryTrack.operating_track_id == track.id
                )
            ).scalars().first()

            industry = None
            spot = None

            if industry_track is not None:
                industry = session.get(Industry, industry_track.industry_id)
                if industry is None:
                    return False, "Linked industry not found."
                if spot_id is None:
                    return False, (
                        "Industry destinations require a specific spot."
                    )
                spot = session.get(Spot, spot_id)
                if spot is None:
                    return False, "Spot not found."
                if spot.track_id != industry_track.id:
                    return False, (
                        "The selected spot does not belong to the selected "
                        "track."
                    )
            elif spot_id is not None:
                return False, "Yard and other general tracks do not use spots."

            return True, {
                "location_id": location.id,
                "location_track_id": track.id,
                "location_name": location.name,
                "industry_id": industry.id if industry is not None else None,
                "industry_track_id": (
                    industry_track.id if industry_track is not None else None
                ),
                "spot_id": spot.id if spot is not None else None,
            }

    @staticmethod
    def _general_ids_for_legacy(industry_id, track_id):
        with SessionLocal() as session:
            industry = session.get(Industry, industry_id)
            track = session.get(IndustryTrack, track_id)
            return (
                getattr(industry, "operating_location_id", None),
                getattr(track, "operating_track_id", None),
            )

    @staticmethod
    def validate_origin(
        origin_location,
        origin_industry_id=None,
        origin_track_id=None,
        origin_spot_id=None,
    ):
        if not WaybillService.normalize_location_text(origin_location):
            return False, "Origin location is required."
        if all(
            value is None
            for value in (
                origin_industry_id,
                origin_track_id,
                origin_spot_id,
            )
        ):
            return True, ""
        if any(
            value is None
            for value in (
                origin_industry_id,
                origin_track_id,
                origin_spot_id,
            )
        ):
            return False, (
                "If an origin uses an Industry, Track, and Spot, all three "
                "must be specified."
            )
        return WaybillService.validate_location(
            origin_industry_id,
            origin_track_id,
            origin_spot_id,
        )

    @staticmethod
    def validate_destination_spot_available(
        destination_spot_id,
        exclude_waybill_id=None,
    ):
        with SessionLocal() as session:
            if session.get(Spot, destination_spot_id) is None:
                return False, "Destination spot not found."
            statement = select(Waybill).where(
                Waybill.destination_spot_id == destination_spot_id,
                Waybill.status.in_(["ACTIVE", "IN_PROGRESS"]),
            )
            if exclude_waybill_id is not None:
                statement = statement.where(Waybill.id != exclude_waybill_id)
            if session.execute(statement).scalars().first() is not None:
                return False, (
                    "This destination spot is already reserved by another "
                    "active waybill."
                )
        return True, ""

    @staticmethod
    def _validate_waybill_values(
        car_id,
        operations_session_id,
        origin_location,
        destination_industry_id,
        destination_track_id,
        destination_spot_id,
        origin_location_id=None,
        origin_location_track_id=None,
        origin_spot_id=None,
        destination_location_id=None,
        destination_location_track_id=None,
        exclude_waybill_id=None,
    ):
        if car_id is None:
            return False, "Car is required."
        if not origin_location:
            return False, "Origin location is required."
        for validator, arguments in (
            (WaybillService.validate_operations_session, (operations_session_id,)),
        ):
            valid, message = validator(*arguments)
            if not valid:
                return False, message

        if origin_location_id is not None or origin_location_track_id is not None:
            valid, message = WaybillService._resolve_general_endpoint(
                origin_location_id,
                origin_location_track_id,
                origin_spot_id,
            )
        else:
            valid, message = WaybillService.validate_origin(origin_location)
        if not valid:
            return False, message

        if (
            destination_location_id is not None
            or destination_location_track_id is not None
        ):
            valid, message = WaybillService._resolve_general_endpoint(
                destination_location_id,
                destination_location_track_id,
                destination_spot_id,
            )
        else:
            if destination_industry_id is None:
                return False, "Destination location is required."
            if destination_track_id is None:
                return False, "Destination track is required."
            if destination_spot_id is None:
                return False, "Industry destinations require a spot."
            valid, message = WaybillService.validate_location(
                destination_industry_id,
                destination_track_id,
                destination_spot_id,
            )
        if not valid:
            return False, message

        if destination_spot_id is not None:
            for validator, arguments in (
                (
                    WaybillService.validate_car_type_for_spot,
                    (car_id, destination_spot_id),
                ),
                (
                    WaybillService.validate_destination_spot_available,
                    (destination_spot_id, exclude_waybill_id),
                ),
            ):
                valid, message = validator(*arguments)
                if not valid:
                    return False, message
        return True, ""

    @staticmethod
    def _load_waybill(session, waybill_id):
        return session.execute(
            select(Waybill)
            .options(*WaybillService._waybill_load_options())
            .where(Waybill.id == waybill_id)
        ).scalars().first()

    @staticmethod
    def create(
        car_id,
        operations_session_id,
        origin_location,
        destination_industry_id,
        destination_track_id,
        destination_spot_id,
        notes=None,
        origin_location_id=None,
        origin_location_track_id=None,
        origin_spot_id=None,
        destination_location_id=None,
        destination_location_track_id=None,
        load_state=None,
        commodity=None,
        cargo_weight_lbs=None,
    ):
        origin_location = WaybillService.normalize_location_text(origin_location)
        notes = str(notes).strip() if notes else None
        commodity = str(commodity).strip() if commodity else None
        (
            valid,
            message,
            load_state,
            cargo_weight_lbs,
        ) = WaybillService.validate_load_details(
            car_id,
            load_state,
            cargo_weight_lbs,
        )
        if not valid:
            return False, message
        valid, message = WaybillService._validate_waybill_values(
            car_id,
            operations_session_id,
            origin_location,
            destination_industry_id,
            destination_track_id,
            destination_spot_id,
            origin_location_id,
            origin_location_track_id,
            origin_spot_id,
            destination_location_id,
            destination_location_track_id,
        )
        if not valid:
            return False, message
        with SessionLocal() as session:
            car = session.get(Car, car_id)
            if car is None:
                return False, "Car not found."
            existing_waybill = session.execute(
                select(Waybill).where(
                    Waybill.car_id == car_id,
                    Waybill.status.in_(["ACTIVE", "IN_PROGRESS"]),
                )
            ).scalars().first()
            if existing_waybill is not None:
                return False, (
                    f"Car {car.reporting_mark} {car.number} already has an "
                    f"unfinished waybill (Waybill #{existing_waybill.id})."
                )

            if origin_location_id is not None:
                _, origin_values = WaybillService._resolve_general_endpoint(
                    origin_location_id,
                    origin_location_track_id,
                    origin_spot_id,
                )
                origin_location = origin_values["location_name"]
                origin_industry_id = origin_values["industry_id"]
                origin_track_id = origin_values["industry_track_id"]
                origin_spot_id = origin_values["spot_id"]
            else:
                origin_industry_id = None
                origin_track_id = None

            if destination_location_id is not None:
                _, destination_values = WaybillService._resolve_general_endpoint(
                    destination_location_id,
                    destination_location_track_id,
                    destination_spot_id,
                )
                destination_industry_id = destination_values["industry_id"]
                destination_track_id = destination_values["industry_track_id"]
                destination_spot_id = destination_values["spot_id"]
            else:
                (
                    destination_location_id,
                    destination_location_track_id,
                ) = WaybillService._general_ids_for_legacy(
                    destination_industry_id,
                    destination_track_id,
                )
            waybill = Waybill(
                car_id=car_id,
                operations_session_id=operations_session_id,
                origin_location=origin_location,
                origin_location_id=origin_location_id,
                origin_location_track_id=origin_location_track_id,
                origin_industry_id=origin_industry_id,
                origin_track_id=origin_track_id,
                origin_spot_id=origin_spot_id,
                destination_location_id=destination_location_id,
                destination_location_track_id=destination_location_track_id,
                destination_industry_id=destination_industry_id,
                destination_track_id=destination_track_id,
                destination_spot_id=destination_spot_id,
                load_state=load_state,
                commodity=commodity,
                cargo_weight_lbs=cargo_weight_lbs,
                status="ACTIVE",
                notes=notes,
            )
            session.add(waybill)
            session.commit()
            return True, WaybillService._load_waybill(session, waybill.id)

    @staticmethod
    def update(
        waybill_id,
        car_id,
        operations_session_id,
        origin_location,
        destination_industry_id,
        destination_track_id,
        destination_spot_id,
        notes=None,
        origin_location_id=None,
        origin_location_track_id=None,
        origin_spot_id=None,
        destination_location_id=None,
        destination_location_track_id=None,
        load_state=None,
        commodity=None,
        cargo_weight_lbs=None,
    ):
        origin_location = WaybillService.normalize_location_text(origin_location)
        notes = str(notes).strip() if notes else None
        commodity = str(commodity).strip() if commodity else None
        (
            valid,
            message,
            load_state,
            cargo_weight_lbs,
        ) = WaybillService.validate_load_details(
            car_id,
            load_state,
            cargo_weight_lbs,
            allow_unspecified=True,
        )
        if not valid:
            return False, message
        valid, message = WaybillService._validate_waybill_values(
            car_id,
            operations_session_id,
            origin_location,
            destination_industry_id,
            destination_track_id,
            destination_spot_id,
            origin_location_id,
            origin_location_track_id,
            origin_spot_id,
            destination_location_id,
            destination_location_track_id,
            exclude_waybill_id=waybill_id,
        )
        if not valid:
            return False, message
        with SessionLocal() as session:
            waybill = session.get(Waybill, waybill_id)
            if waybill is None:
                return False, "Waybill not found."
            if waybill.status == "COMPLETED":
                return False, "A completed waybill cannot be edited."
            if waybill.status == "CANCELLED":
                return False, "A cancelled waybill cannot be edited."
            car = session.get(Car, car_id)
            if car is None:
                return False, "Car not found."
            existing_waybill = session.execute(
                select(Waybill).where(
                    Waybill.car_id == car_id,
                    Waybill.status.in_(["ACTIVE", "IN_PROGRESS"]),
                    Waybill.id != waybill_id,
                )
            ).scalars().first()
            if existing_waybill is not None:
                return False, (
                    f"Car {car.reporting_mark} {car.number} already has "
                    f"another unfinished waybill "
                    f"(Waybill #{existing_waybill.id})."
                )

            if origin_location_id is not None:
                _, origin_values = WaybillService._resolve_general_endpoint(
                    origin_location_id,
                    origin_location_track_id,
                    origin_spot_id,
                )
                origin_location = origin_values["location_name"]
                origin_industry_id = origin_values["industry_id"]
                origin_track_id = origin_values["industry_track_id"]
                origin_spot_id = origin_values["spot_id"]
            else:
                origin_industry_id = None
                origin_track_id = None

            if destination_location_id is not None:
                _, destination_values = WaybillService._resolve_general_endpoint(
                    destination_location_id,
                    destination_location_track_id,
                    destination_spot_id,
                )
                destination_industry_id = destination_values["industry_id"]
                destination_track_id = destination_values["industry_track_id"]
                destination_spot_id = destination_values["spot_id"]
            else:
                (
                    destination_location_id,
                    destination_location_track_id,
                ) = WaybillService._general_ids_for_legacy(
                    destination_industry_id,
                    destination_track_id,
                )
            waybill.car_id = car_id
            waybill.operations_session_id = operations_session_id
            waybill.origin_location = origin_location
            waybill.origin_location_id = origin_location_id
            waybill.origin_location_track_id = origin_location_track_id
            waybill.origin_industry_id = origin_industry_id
            waybill.origin_track_id = origin_track_id
            waybill.origin_spot_id = origin_spot_id
            waybill.destination_location_id = destination_location_id
            waybill.destination_location_track_id = destination_location_track_id
            waybill.destination_industry_id = destination_industry_id
            waybill.destination_track_id = destination_track_id
            waybill.destination_spot_id = destination_spot_id
            waybill.load_state = load_state
            waybill.commodity = commodity
            waybill.cargo_weight_lbs = cargo_weight_lbs
            waybill.notes = notes
            session.commit()
            return True, WaybillService._load_waybill(session, waybill.id)

    @staticmethod
    def get_all():
        with SessionLocal() as session:
            return session.execute(
                select(Waybill)
                .options(*WaybillService._waybill_load_options())
                .order_by(Waybill.created_at.desc(), Waybill.id.desc())
            ).scalars().all()

    @staticmethod
    def get_by_archive_view(view="OPEN"):
        normalized_view = str(view or "OPEN").strip().upper()

        if normalized_view not in {
            "OPEN",
            "COMPLETED",
            "ARCHIVED",
            "ALL",
        }:
            normalized_view = "OPEN"

        with SessionLocal() as session:
            statement = (
                select(Waybill)
                .options(*WaybillService._waybill_load_options())
                .order_by(
                    Waybill.created_at.desc(),
                    Waybill.id.desc(),
                )
            )

            if normalized_view == "OPEN":
                statement = statement.where(
                    Waybill.status.in_(["ACTIVE", "IN_PROGRESS"]),
                    Waybill.archived.is_(False),
                )

            elif normalized_view == "COMPLETED":
                statement = statement.where(
                    Waybill.status == "COMPLETED",
                    Waybill.archived.is_(False),
                )

            elif normalized_view == "ARCHIVED":
                statement = statement.where(
                    Waybill.archived.is_(True),
                )

            return session.execute(
                statement
            ).scalars().all()

    @staticmethod
    def get_by_id(waybill_id):
        with SessionLocal() as session:
            return WaybillService._load_waybill(session, waybill_id)

    @staticmethod
    def get_for_car(car_id):
        with SessionLocal() as session:
            return session.execute(
                select(Waybill)
                .options(*WaybillService._waybill_load_options())
                .where(Waybill.car_id == car_id)
                .order_by(Waybill.created_at.desc(), Waybill.id.desc())
            ).scalars().all()

    @staticmethod
    def get_active_for_car(car_id):
        with SessionLocal() as session:
            return session.execute(
                select(Waybill)
                .options(*WaybillService._waybill_load_options())
                .where(
                    Waybill.car_id == car_id,
                    Waybill.status.in_(["ACTIVE", "IN_PROGRESS"]),
                )
                .order_by(Waybill.created_at.desc(), Waybill.id.desc())
            ).scalars().all()

    @staticmethod
    def _destination_error(waybill, session):
        car = session.get(Car, waybill.car_id)
        if car is None:
            return "The car assigned to this waybill was not found."

        if waybill.destination_spot_id is not None:
            if car.spot_id != waybill.destination_spot_id:
                return (
                    f"Car {car.reporting_mark} {car.number} has not reached "
                    "the waybill destination."
                )
            return ""

        if (
            waybill.destination_location_id is None
            or waybill.destination_location_track_id is None
        ):
            return "The waybill does not have a complete destination."

        if (
            car.operating_location_id != waybill.destination_location_id
            or car.operating_track_id
            != waybill.destination_location_track_id
        ):
            return (
                f"Car {car.reporting_mark} {car.number} has not reached "
                "the waybill destination."
            )
        return ""

    @staticmethod
    def validate_completion(waybill_id, db_session=None):
        """Return whether an unfinished Waybill can be completed.

        ``db_session`` lets OperationsSessionService validate several
        Waybills in the transaction that will complete them.
        """
        if db_session is not None:
            waybill = db_session.get(Waybill, waybill_id)
            if waybill is None:
                return False, "Waybill not found."
            if waybill.status not in ("ACTIVE", "IN_PROGRESS"):
                return False, "Only an active or in-progress waybill can be completed."
            error = WaybillService._destination_error(waybill, db_session)
            return (False, error) if error else (True, "")
        with SessionLocal() as session:
            return WaybillService.validate_completion(waybill_id, session)

    @staticmethod
    def is_at_destination(waybill_id):
        with SessionLocal() as session:
            waybill = session.get(Waybill, waybill_id)
            if waybill is None:
                return False, "Waybill not found."
            error = WaybillService._destination_error(waybill, session)
            return (False, error) if error else (True, "")

    @staticmethod
    def complete(waybill_id, db_session=None):
        """Complete a Waybill after confirming its car is at its destination.

        When a caller supplies ``db_session``, this method does not commit.
        That permits an Operations Session and all of its Waybills to be
        completed atomically.
        """
        if db_session is not None:
            valid, message = WaybillService.validate_completion(
                waybill_id, db_session
            )
            if not valid:
                return False, message
            waybill = db_session.get(Waybill, waybill_id)
            waybill.status = "COMPLETED"
            waybill.completed_at = datetime.utcnow()
            return True, waybill
        with SessionLocal() as session:
            success, result = WaybillService.complete(waybill_id, session)
            if not success:
                return False, result
            session.commit()
            return True, WaybillService._load_waybill(session, waybill_id)

    @staticmethod
    def archive(waybill_id):
        with SessionLocal() as session:
            waybill = session.get(Waybill, waybill_id)

            if waybill is None:
                return False, "Waybill not found."

            if waybill.status != "COMPLETED":
                return False, (
                    "Only a completed waybill can be archived."
                )

            if waybill.archived:
                return False, "Waybill is already archived."

            waybill.archived = True
            waybill.archived_at = datetime.utcnow()

            session.commit()

            return True, WaybillService._load_waybill(
                session,
                waybill.id,
            )

    @staticmethod
    def restore_from_archive(waybill_id):
        with SessionLocal() as session:
            waybill = session.get(Waybill, waybill_id)

            if waybill is None:
                return False, "Waybill not found."

            if not waybill.archived:
                return False, "Waybill is not archived."

            waybill.archived = False
            waybill.archived_at = None

            session.commit()

            return True, WaybillService._load_waybill(
                session,
                waybill.id,
            )

    @staticmethod
    def cancel(waybill_id):
        with SessionLocal() as session:
            waybill = session.get(Waybill, waybill_id)
            if waybill is None:
                return False, "Waybill not found."
            if waybill.status == "COMPLETED":
                return False, "A completed waybill cannot be cancelled."
            if waybill.status == "CANCELLED":
                return False, "Waybill is already cancelled."
            waybill.status = "CANCELLED"
            session.commit()
            return True, WaybillService._load_waybill(session, waybill.id)

    @staticmethod
    def set_in_progress(waybill_id):
        with SessionLocal() as session:
            waybill = session.get(Waybill, waybill_id)
            if waybill is None:
                return False, "Waybill not found."
            if waybill.status == "COMPLETED":
                return False, (
                    "A completed waybill cannot be changed to in progress."
                )
            if waybill.status == "CANCELLED":
                return False, (
                    "A cancelled waybill cannot be changed to in progress."
                )
            waybill.status = "IN_PROGRESS"
            session.commit()
            return True, WaybillService._load_waybill(session, waybill.id)

    @staticmethod
    def delete(waybill_id):
        with SessionLocal() as session:
            waybill = session.get(Waybill, waybill_id)
            if waybill is None:
                return False
            session.delete(waybill)
            session.commit()
            return True
