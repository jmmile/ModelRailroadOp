"""Authenticated local web companion server."""

import hmac
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from modelrailroadops.database.database import DATABASE_FILE
from modelrailroadops.paths import data_directory_override
from modelrailroadops.services.operations_session_service import (
    OperationsSessionService,
)
from modelrailroadops.services.operations_session_train_service import (
    OperationsSessionTrainService,
)
from modelrailroadops.services.switch_list_move_service import (
    SwitchListMoveService,
)
from modelrailroadops.services.switch_list_service import (
    SwitchListService,
)
from modelrailroadops.services.waybill_service import (
    WaybillService,
)


WEB_DIRECTORY = Path(__file__).resolve().parent
STATIC_DIRECTORY = WEB_DIRECTORY / "static"
INDEX_FILE = STATIC_DIRECTORY / "index.html"

AUTH_COOKIE_NAME = "modelrailroadops_companion"
PAIRING_CODE = f"{secrets.randbelow(1_000_000):06d}"
AUTH_TOKEN = secrets.token_urlsafe(32)


app = FastAPI(
    title="Model Railroad Operations Companion",
    version="0.4.0",
)


class PairingRequest(BaseModel):
    """Pairing-code request sent by the companion browser."""

    code: str


def require_authentication(request: Request):
    """
    Require a valid companion authentication cookie.

    The authentication token exists only for the lifetime of the
    current server process. Restarting the server invalidates all
    previously paired browsers.
    """

    supplied_token = request.cookies.get(
        AUTH_COOKIE_NAME,
        "",
    )

    if not supplied_token:
        raise HTTPException(
            status_code=401,
            detail="This device is not paired.",
        )

    if not hmac.compare_digest(
        supplied_token,
        AUTH_TOKEN,
    ):
        raise HTTPException(
            status_code=401,
            detail="This device is not paired.",
        )


def require_same_origin(request: Request):
    """
    Require a write request to originate from this companion server.

    Authentication identifies the paired browser. The Origin check
    separately prevents another web site from causing that browser to
    submit a railroad-changing request with its authentication cookie.
    """

    supplied_origin = request.headers.get(
        "origin",
        "",
    ).rstrip("/")

    expected_origin = str(
        request.base_url
    ).rstrip("/")

    if (
        not supplied_origin
        or not hmac.compare_digest(
            supplied_origin,
            expected_origin,
        )
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "This write request did not originate from "
                "the companion application."
            ),
        )


def location_display(
    location,
    track,
    industry,
    industry_track,
    spot,
    fallback="",
):
    """
    Build an operator-friendly Waybill endpoint description.

    General operating Location/Track relationships are preferred.
    Legacy Industry/Track/Spot relationships remain supported.
    """

    parts = []

    if location is not None:
        if getattr(location, "name", None):
            parts.append(location.name)

        if (
            track is not None
            and getattr(track, "name", None)
        ):
            parts.append(track.name)

    elif industry is not None:
        if getattr(industry, "name", None):
            parts.append(industry.name)

        if (
            industry_track is not None
            and getattr(industry_track, "name", None)
        ):
            parts.append(industry_track.name)

    if spot is not None:
        spot_number = getattr(
            spot,
            "spot_number",
            None,
        )

        if spot_number is not None:
            parts.append(f"Spot {spot_number}")

    if parts:
        return " - ".join(
            str(part)
            for part in parts
        )

    return fallback or ""


@app.get("/health")
def health():
    """
    Report the companion server status.

    This endpoint intentionally remains available without pairing
    so local-network connectivity can be diagnosed.
    """

    return {
        "status": "ok",
        "application": "Model Railroad Operations Companion",
        "database": str(DATABASE_FILE),
    }


@app.get("/api/auth/status")
def authentication_status(request: Request):
    """
    Report whether the requesting browser is currently paired.

    No railroad information is returned by this endpoint.
    """

    supplied_token = request.cookies.get(
        AUTH_COOKIE_NAME,
        "",
    )

    authenticated = bool(
        supplied_token
        and hmac.compare_digest(
            supplied_token,
            AUTH_TOKEN,
        )
    )

    return {
        "authenticated": authenticated,
    }


@app.post("/api/pair")
def pair_device(
    pairing_request: PairingRequest,
    response: Response,
):
    """
    Pair a browser using the temporary six-digit pairing code.

    Successful pairing creates an HttpOnly authentication cookie.
    The cookie and its server-side token become invalid when the
    companion server is restarted.
    """

    supplied_code = pairing_request.code.strip()

    if not hmac.compare_digest(
        supplied_code,
        PAIRING_CODE,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect pairing code.",
        )

    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=AUTH_TOKEN,
        httponly=True,
        samesite="strict",
        secure=False,
        path="/",
    )

    return {
        "paired": True,
    }


@app.get("/api/sessions")
def get_sessions(request: Request):
    """
    Return Operations Sessions for an authenticated companion.

    This endpoint is read-only.
    """

    require_authentication(request)

    sessions = OperationsSessionService.get_all()

    return [
        {
            "id": operations_session.id,
            "name": operations_session.name or "",
            "session_date": (
                operations_session.session_date.isoformat()
                if operations_session.session_date is not None
                else None
            ),
            "status": operations_session.status or "",
            "notes": operations_session.notes or "",
        }
        for operations_session in sessions
    ]


@app.get("/api/sessions/{session_id}/trains")
def get_session_trains(
    session_id: int,
    request: Request,
):
    """
    Return trains assigned to an Operations Session.

    This endpoint is read-only and requires a paired browser.
    """

    require_authentication(request)

    assignments = (
        OperationsSessionTrainService.get_by_operations_session(
            session_id
        )
    )

    result = []

    for assignment in assignments:
        train = assignment.train

        if train is None:
            continue

        result.append(
            {
                "assignment_id": assignment.id,
                "train_id": train.id,
                "number": train.number or "",
                "name": train.name or "",
                "symbol": train.symbol or "",
                "train_type": train.train_type or "",
                "origin": train.origin or "",
                "destination": train.destination or "",
                "direction": train.direction or "",
                "active": bool(train.active),
            }
        )

    return result


@app.get(
    "/api/sessions/{session_id}/trains/{train_id}/moves"
)
def get_train_moves(
    session_id: int,
    train_id: int,
    request: Request,
):
    """
    Return ordered switch-list work for a train.

    This endpoint is read-only and requires a paired browser.
    """

    require_authentication(request)

    rows = SwitchListService.get_switch_list_rows(
        session_id,
        train_id,
    )

    result = []

    for row in rows:
        result.append(
            {
                "car_move_id": row.get("car_move_id"),
                "move_type": row.get("move_type") or "",
                "move_status": row.get("move_status") or "",
                "route_sequence": row.get("route_sequence"),
                "car_id": row.get("car_id"),
                "car_display": row.get("car_display") or "",
                "reporting_mark": (
                    row.get("reporting_mark") or ""
                ),
                "number": row.get("number") or "",
                "car_type": row.get("car_type") or "",
                "length": row.get("length"),
                "instruction_location": (
                    row.get("instruction_location") or ""
                ),
                "origin": (
                    row.get("origin_display") or ""
                ),
                "destination": (
                    row.get("destination_display") or ""
                ),
                "waybill_id": row.get("waybill_id"),
                "waybill_status": (
                    row.get("waybill_status") or ""
                ),
                "notes": row.get("notes") or "",
                "move_notes": row.get("move_notes") or "",
            }
        )

    return result


@app.get("/api/waybills/{waybill_id}")
def get_waybill(
    waybill_id: int,
    request: Request,
):
    """
    Return read-only operator details for one Waybill.

    The existing WaybillService performs the database lookup and
    eager-loads the related Car and location information.
    """

    require_authentication(request)

    waybill = WaybillService.get_by_id(
        waybill_id
    )

    if waybill is None:
        raise HTTPException(
            status_code=404,
            detail="Waybill not found.",
        )

    car = waybill.car

    car_display = ""

    if car is not None:
        car_display = (
            f"{car.reporting_mark or ''} "
            f"{car.number or ''}"
        ).strip()

    origin = location_display(
        waybill.origin_operating_location,
        waybill.origin_operating_track,
        waybill.origin_industry,
        waybill.origin_track,
        waybill.origin_spot,
        fallback=waybill.origin_location,
    )

    destination = location_display(
        waybill.destination_operating_location,
        waybill.destination_operating_track,
        waybill.destination_industry,
        waybill.destination_track,
        waybill.destination_spot,
    )

    return {
        "id": waybill.id,
        "car_id": waybill.car_id,
        "car_display": car_display,
        "car_type": (
            car.car_type
            if car is not None
            else ""
        ) or "",
        "load_state": waybill.load_state or "",
        "commodity": waybill.commodity or "",
        "cargo_weight_lbs": (
            waybill.cargo_weight_lbs
        ),
        "gross_weight_lbs": (
            waybill.gross_weight_lbs
        ),
        "tonnage": waybill.tonnage,
        "origin": origin,
        "destination": destination,
        "status": waybill.status or "",
        "notes": waybill.notes or "",
        "operations_session_id": (
            waybill.operations_session_id
        ),
        "created_at": (
            waybill.created_at.isoformat()
            if waybill.created_at is not None
            else None
        ),
        "completed_at": (
            waybill.completed_at.isoformat()
            if waybill.completed_at is not None
            else None
        ),
        "archived": bool(waybill.archived),
        "archived_at": (
            waybill.archived_at.isoformat()
            if waybill.archived_at is not None
            else None
        ),
    }


@app.post("/api/moves/{car_move_id}/complete")
def complete_car_move(
    car_move_id: int,
    request: Request,
):
    """
    Complete one switch-list instruction.

    This is a database-changing operation. The browser must be
    paired and the request must originate from this companion
    application.

    Railroad validation and transaction handling remain the
    responsibility of SwitchListMoveService.
    """

    require_authentication(request)
    require_same_origin(request)

    success, message = (
        SwitchListMoveService.complete_move(
            car_move_id
        )
    )

    if not success:
        raise HTTPException(
            status_code=409,
            detail=(
                message
                or "The Car Move could not be completed."
            ),
        )

    return {
        "completed": True,
        "car_move_id": car_move_id,
        "message": message,
    }


@app.get("/", response_class=HTMLResponse)
def companion_page():
    """
    Return the touch-friendly companion interface.

    The page itself is public so an unpaired browser can display
    the pairing screen. Railroad-data API calls require pairing.
    """

    return HTMLResponse(
        content=INDEX_FILE.read_text(
            encoding="utf-8"
        )
    )


def run():
    """
    Start the companion server for local-network development.

    The server listens on the local network so an iPad can connect.
    Railroad-data endpoints require the temporary pairing
    credential generated for this server run.
    """

    import uvicorn

    print()
    print("=" * 58)
    print("MODEL RAILROAD OPERATIONS COMPANION")
    print("=" * 58)
    print()
    print("Pairing code:")
    print()
    print(f"    {PAIRING_CODE}")
    print()
    print("Enter this code on the iPad companion page.")
    print("The code changes whenever this server is restarted.")
    print()
    if data_directory_override() is not None:
        print("*** DATABASE OVERRIDE ACTIVE ***")
        print()
        print(
            "The companion server is not using "
            "the normal data directory."
        )
        print()

    print(f"Database: {DATABASE_FILE}")
    print()
    print("=" * 58)    
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8675,
        reload=False,
    )


if __name__ == "__main__":
    run()