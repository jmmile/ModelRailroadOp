"""Read-only packet data assembled from the existing operating instructions."""
from sqlalchemy import select

from modelrailroadops.models.operations_session_train import OperationsSessionTrain
from modelrailroadops.models.train import Train
from modelrailroadops.services import operations_session_service as sessions
from modelrailroadops.services.switch_list_service import SwitchListService
from modelrailroadops.services.train_route_service import TrainRouteService


class CrewPacketService:
    @staticmethod
    def get_packet(session_id):
        summary = sessions.OperationsSessionService.end_summary(session_id)
        rows = SwitchListService.get_switch_list_rows(session_id)
        trains = []
        with sessions.SessionLocal() as db:
            assignments = db.scalars(select(OperationsSessionTrain).where(
                OperationsSessionTrain.operations_session_id == session_id
            )).all()
            by_train = {assignment.train_id: assignment for assignment in assignments}
            train_ids = set(by_train) | {row["train_id"] for row in rows}
            for tid in sorted(train_ids):
                train = db.get(Train, tid)
                assignment = by_train.get(tid)
                locomotives = []
                passenger_cars = []
                if assignment:
                    for item in sorted(assignment.locomotives, key=lambda item: item.sequence):
                        loco = item.locomotive
                        locomotives.append((item.sequence, f"{loco.reporting_mark} {loco.number}", loco.model))
                    for item in sorted(assignment.passenger_cars, key=lambda item: item.sequence):
                        car = item.passenger_car
                        passenger_cars.append((item.sequence, f"{car.reporting_mark} {car.number}", car.equipment_type))
                routes = TrainRouteService.get_by_train(tid)
                route_rows = [(route.sequence,
                               route.operating_location.name if route.operating_location else route.location,
                               route.operating_track.name if route.operating_track else "-",
                               route.arrival_time.strftime("%H:%M") if route.arrival_time else "-",
                               route.departure_time.strftime("%H:%M") if route.departure_time else "-")
                              for route in routes]
                trains.append({"id": tid, "name": f"{train.symbol} - {train.name}",
                               "assigned": assignment is not None,
                               "locomotives": locomotives, "passenger_cars": passenger_cars,
                               "route": route_rows,
                               "moves": [row for row in rows if row["train_id"] == tid]})
        trains.sort(key=lambda train: train["name"].casefold())
        return {"summary": summary, "trains": trains}
