from sqlalchemy import func, select

from modelrailroadops.database.database import SessionLocal
from modelrailroadops.models.car import Car
from modelrailroadops.models.car_move import CarMove
from modelrailroadops.models.industry_track import IndustryTrack
from modelrailroadops.models.location_track import LocationTrack
from modelrailroadops.models.operations_session import OperationsSession
from modelrailroadops.models.operations_session_train import OperationsSessionTrain
from modelrailroadops.models.spot import Spot
from modelrailroadops.models.train import Train
from modelrailroadops.models.waybill import Waybill
from modelrailroadops.services.car_location_service import CarLocationService
from modelrailroadops.services.industry_demand_service import IndustryDemandService


class DashboardService:
    """Build a read-only operational summary for the opening dashboard."""

    @staticmethod
    def get_summary():
        demands = IndustryDemandService.get_open_demands()

        with SessionLocal() as session:
            cars = session.execute(select(Car)).scalars().all()
            total_cars = len(cars)
            loaded = sum((car.status or "").upper() == "LOADED" for car in cars)
            empty = sum((car.status or "").upper() == "EMPTY" for car in cars)
            available = sum((car.status or "").upper() == "AVAILABLE" for car in cars)
            on_train = sum((car.location or "").startswith("On Train:") for car in cars)
            unassigned = sum(
                car.industry_id is None
                and car.operating_location_id is None
                and not (car.location or "").startswith("On Train:")
                for car in cars
            )

            active_session = (
                session.execute(
                    select(OperationsSession)
                    .where(OperationsSession.status == "ACTIVE")
                    .order_by(
                        OperationsSession.session_date.desc(),
                        OperationsSession.id.desc(),
                    )
                )
                .scalars()
                .first()
            )

            current_operations = {
                "session_id": None,
                "name": "No active operating session",
                "date": "",
                "trains": "None",
                "completed_moves": 0,
                "total_moves": 0,
                "progress": 0,
            }

            if active_session is not None:
                train_rows = (
                    session.execute(
                        select(Train)
                        .join(
                            OperationsSessionTrain,
                            OperationsSessionTrain.train_id == Train.id,
                        )
                        .where(
                            OperationsSessionTrain.operations_session_id
                            == active_session.id
                        )
                        .order_by(Train.number, Train.name)
                    )
                    .scalars()
                    .all()
                )
                move_statuses = (
                    session.execute(
                        select(CarMove.status).where(
                            CarMove.operations_session_id == active_session.id
                        )
                    )
                    .scalars()
                    .all()
                )
                completed_moves = sum(status == "COMPLETED" for status in move_statuses)
                total_moves = len(move_statuses)
                progress = (
                    round(completed_moves * 100 / total_moves) if total_moves else 0
                )
                current_operations = {
                    "session_id": active_session.id,
                    "name": active_session.name,
                    "date": active_session.session_date.isoformat(),
                    "trains": ", ".join(
                        f"{train.symbol} - {train.name}" for train in train_rows
                    )
                    or "No trains assigned",
                    "completed_moves": completed_moves,
                    "total_moves": total_moves,
                    "progress": progress,
                }

            active_waybills = session.scalar(
                select(func.count())
                .select_from(Waybill)
                .where(Waybill.status.in_(("ACTIVE", "IN_PROGRESS")))
            )
            pending_moves = session.scalar(
                select(func.count())
                .select_from(CarMove)
                .where(CarMove.status == "PENDING")
            )
            awaiting_pickup = session.scalar(
                select(func.count())
                .select_from(CarMove)
                .where(
                    CarMove.status == "PENDING",
                    CarMove.move_type == "PICKUP",
                )
            )

            incompatible_spots = 0
            for car in cars:
                if car.spot_id is None:
                    continue
                spot = session.get(Spot, car.spot_id)
                valid, _message = CarLocationService.validate_car_for_spot(
                    car,
                    spot,
                )
                if not valid:
                    incompatible_spots += 1

            over_capacity_tracks = 0
            capacity_details = []
            tracks = session.execute(select(LocationTrack)).scalars().all()
            for track in tracks:
                occupied = session.scalar(
                    select(func.count())
                    .select_from(Car)
                    .where(Car.operating_track_id == track.id)
                )
                capacity = track.capacity
                industry_track_ids = select(IndustryTrack.id).where(
                    IndustryTrack.operating_track_id == track.id
                )
                if session.scalar(select(IndustryTrack.id).where(
                    IndustryTrack.operating_track_id == track.id
                ).limit(1)) is not None:
                    # Industry capacity is physical spots, not a manually entered limit.
                    capacity = session.scalar(
                        select(func.count()).select_from(Spot).where(
                            Spot.track_id.in_(industry_track_ids)
                        )
                    )
                if capacity is not None and occupied > capacity:
                    over_capacity_tracks += 1
                state = "Available"
                if capacity is None:
                    state = "Capacity not set"
                elif occupied > capacity:
                    state = "Over capacity"
                elif occupied == capacity:
                    state = "Full"
                elif capacity > 0 and occupied / capacity >= 0.8:
                    state = "Near capacity"
                capacity_details.append(
                    {
                        "location": track.location.name,
                        "track": track.name,
                        "occupied": occupied,
                        "capacity": capacity,
                        "available": max(0, capacity - occupied)
                        if capacity is not None
                        else None,
                        "status": state
                        if track.active and track.location.active
                        else f"Inactive — {state}",
                    }
                )
            capacity_details.sort(key=lambda row: (row["location"], row["track"]))

            completed_with_pending = session.scalar(
                select(func.count(func.distinct(OperationsSession.id)))
                .select_from(OperationsSession)
                .join(
                    CarMove,
                    CarMove.operations_session_id == OperationsSession.id,
                )
                .where(
                    OperationsSession.status == "COMPLETED",
                    CarMove.status == "PENDING",
                )
            )

        attention = [
            {
                "label": "Unassigned cars",
                "count": unassigned,
                "destination": "Car Roster",
            },
            {
                "label": "Cars at incompatible spots",
                "count": incompatible_spots,
                "destination": "Car Spotting",
            },
            {
                "label": "Tracks over capacity",
                "count": over_capacity_tracks,
                "destination": "Locations",
            },
            {
                "label": "Completed sessions with pending moves",
                "count": completed_with_pending,
                "destination": "Operations Sessions",
            },
        ]

        return {
            "capacity_details": capacity_details,
            "current_operations": current_operations,
            "fleet": {
                "total": total_cars,
                "loaded": loaded,
                "empty": empty,
                "available": available,
                "on_train": on_train,
                "unassigned": unassigned,
            },
            "work_waiting": {
                "industry_demands": len(demands),
                "active_waybills": active_waybills or 0,
                "pending_moves": pending_moves or 0,
                "awaiting_pickup": awaiting_pickup or 0,
            },
            "attention": attention,
            "attention_total": sum(item["count"] for item in attention),
        }
