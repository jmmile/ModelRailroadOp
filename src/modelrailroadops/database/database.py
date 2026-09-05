from pathlib import Path

from sqlalchemy import (
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import (
    sessionmaker,
)

import modelrailroadops.models

from modelrailroadops.database.base import Base


#
# Database location
#

PROJECT_ROOT = (
    Path(__file__).resolve().parents[3]
)

DATABASE_FILE = (
    PROJECT_ROOT
    / "data"
    / "railroad.db"
)

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
)


def _upgrade_waybill_location_schema():
    """Add general Location/Track endpoints without losing Waybills.

    SQLite cannot remove the NOT NULL requirement from the three legacy
    destination columns in place.  A transactional table copy is therefore
    used when the old schema is detected.  Existing IDs remain unchanged, so
    CarMove and Operations Session references continue to point at the same
    Waybills.
    """

    current_inspector = inspect(engine)

    if not current_inspector.has_table("waybills"):
        return

    column_details = {
        column["name"]: column
        for column in current_inspector.get_columns("waybills")
    }
    general_columns = {
        "origin_location_id",
        "origin_location_track_id",
        "destination_location_id",
        "destination_location_track_id",
    }
    legacy_destination_columns = (
        "destination_industry_id",
        "destination_track_id",
        "destination_spot_id",
    )

    needs_rebuild = (
        not general_columns.issubset(column_details)
        or any(
            not column_details[name]["nullable"]
            for name in legacy_destination_columns
            if name in column_details
        )
    )

    if needs_rebuild:
        source_columns = set(column_details)

        def source(name, fallback="NULL"):
            return name if name in source_columns else fallback

        raw_connection = engine.raw_connection()

        try:
            cursor = raw_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("BEGIN")
            cursor.execute("DROP TABLE IF EXISTS waybills_location_upgrade")
            cursor.execute(
                """
                CREATE TABLE waybills_location_upgrade (
                    id INTEGER NOT NULL,
                    car_id INTEGER NOT NULL,
                    operations_session_id INTEGER,
                    origin_location VARCHAR(100) NOT NULL,
                    origin_location_id INTEGER,
                    origin_location_track_id INTEGER,
                    origin_industry_id INTEGER,
                    origin_track_id INTEGER,
                    origin_spot_id INTEGER,
                    destination_location_id INTEGER,
                    destination_location_track_id INTEGER,
                    destination_industry_id INTEGER,
                    destination_track_id INTEGER,
                    destination_spot_id INTEGER,
                    load_state VARCHAR(20),
                    commodity VARCHAR(100),
                    cargo_weight_lbs INTEGER,
                    status VARCHAR(30) NOT NULL,
                    notes VARCHAR(500),
                    created_at DATETIME NOT NULL,
                    completed_at DATETIME,
                    PRIMARY KEY (id),
                    FOREIGN KEY(car_id) REFERENCES cars(id),
                    FOREIGN KEY(operations_session_id)
                        REFERENCES operations_sessions(id),
                    FOREIGN KEY(origin_location_id) REFERENCES locations(id),
                    FOREIGN KEY(origin_location_track_id)
                        REFERENCES location_tracks(id),
                    FOREIGN KEY(origin_industry_id) REFERENCES industries(id),
                    FOREIGN KEY(origin_track_id) REFERENCES industry_tracks(id),
                    FOREIGN KEY(origin_spot_id) REFERENCES spots(id),
                    FOREIGN KEY(destination_location_id)
                        REFERENCES locations(id),
                    FOREIGN KEY(destination_location_track_id)
                        REFERENCES location_tracks(id),
                    FOREIGN KEY(destination_industry_id)
                        REFERENCES industries(id),
                    FOREIGN KEY(destination_track_id)
                        REFERENCES industry_tracks(id),
                    FOREIGN KEY(destination_spot_id) REFERENCES spots(id)
                )
                """
            )
            cursor.execute(
                f"""
                INSERT INTO waybills_location_upgrade (
                    id,
                    car_id,
                    operations_session_id,
                    origin_location,
                    origin_location_id,
                    origin_location_track_id,
                    origin_industry_id,
                    origin_track_id,
                    origin_spot_id,
                    destination_location_id,
                    destination_location_track_id,
                    destination_industry_id,
                    destination_track_id,
                    destination_spot_id,
                    load_state,
                    commodity,
                    cargo_weight_lbs,
                    status,
                    notes,
                    created_at,
                    completed_at
                )
                SELECT
                    {source('id')},
                    {source('car_id')},
                    {source('operations_session_id')},
                    {source('origin_location', "''")},
                    {source('origin_location_id')},
                    {source('origin_location_track_id')},
                    {source('origin_industry_id')},
                    {source('origin_track_id')},
                    {source('origin_spot_id')},
                    {source('destination_location_id')},
                    {source('destination_location_track_id')},
                    {source('destination_industry_id')},
                    {source('destination_track_id')},
                    {source('destination_spot_id')},
                    {source('load_state')},
                    {source('commodity')},
                    {source('cargo_weight_lbs')},
                    {source('status', "'ACTIVE'")},
                    {source('notes')},
                    {source('created_at', 'CURRENT_TIMESTAMP')},
                    {source('completed_at')}
                FROM waybills
                """
            )
            cursor.execute("DROP TABLE waybills")
            cursor.execute(
                "ALTER TABLE waybills_location_upgrade RENAME TO waybills"
            )
            raw_connection.commit()
            cursor.execute("PRAGMA foreign_keys = ON")
        except Exception:
            raw_connection.rollback()
            try:
                raw_connection.cursor().execute("PRAGMA foreign_keys = ON")
            except Exception:
                pass
            raise
        finally:
            raw_connection.close()

    # Populate general endpoint IDs for all legacy Industry Waybills and for
    # named origins that already match a Location. This is safe to rerun.
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE waybills
                SET origin_location_id = COALESCE(
                    origin_location_id,
                    (
                        SELECT industries.operating_location_id
                        FROM industries
                        WHERE industries.id = waybills.origin_industry_id
                    ),
                    (
                        SELECT locations.id
                        FROM locations
                        WHERE locations.name = waybills.origin_location
                    )
                ),
                origin_location_track_id = COALESCE(
                    origin_location_track_id,
                    (
                        SELECT industry_tracks.operating_track_id
                        FROM industry_tracks
                        WHERE industry_tracks.id = waybills.origin_track_id
                    )
                ),
                destination_location_id = COALESCE(
                    destination_location_id,
                    (
                        SELECT industries.operating_location_id
                        FROM industries
                        WHERE industries.id = waybills.destination_industry_id
                    )
                ),
                destination_location_track_id = COALESCE(
                    destination_location_track_id,
                    (
                        SELECT industry_tracks.operating_track_id
                        FROM industry_tracks
                        WHERE industry_tracks.id = waybills.destination_track_id
                    )
                )
                """
            )
        )


def _upgrade_waybill_load_schema():
    """Add nullable load details without changing existing Waybills."""

    current_inspector = inspect(engine)

    if not current_inspector.has_table("waybills"):
        return

    columns = {
        column["name"]
        for column in current_inspector.get_columns("waybills")
    }

    additions = {
        "load_state": "VARCHAR(20)",
        "commodity": "VARCHAR(100)",
        "cargo_weight_lbs": "INTEGER",
    }

    with engine.begin() as connection:
        for column_name, column_type in additions.items():
            if column_name not in columns:
                connection.execute(
                    text(
                        f"ALTER TABLE waybills "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )



def _upgrade_waybill_archive_schema():
    """Add Waybill archive fields without changing existing Waybills."""

    current_inspector = inspect(engine)

    if not current_inspector.has_table("waybills"):
        return

    columns = {
        column["name"]
        for column in current_inspector.get_columns("waybills")
    }

    with engine.begin() as connection:
        if "archived" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE waybills "
                    "ADD COLUMN archived BOOLEAN NOT NULL DEFAULT 0"
                )
            )

        if "archived_at" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE waybills "
                    "ADD COLUMN archived_at DATETIME"
                )
            )

def initialize_database():
    """
    Create all database tables and apply required migrations.

    Existing data is preserved.  SQLAlchemy's create_all()
    creates missing tables but does not add columns to existing
    SQLite tables, so each schema addition is checked explicitly.
    """

    #
    # Create tables that do not already exist.
    #

    Base.metadata.create_all(
        bind=engine,
    )

    inspector = inspect(
        engine,
    )

    #
    # Update the Train definition without rebuilding the table.
    # SQLite 3.25+ supports an in-place column rename, which
    # preserves Train IDs and all foreign-key references to them.
    #

    if inspector.has_table(
        "trains"
    ):

        columns = {
            column["name"]
            for column in inspector.get_columns(
                "trains"
            )
        }

        with engine.begin() as connection:

            if "symbol" in columns and "number" not in columns:

                connection.execute(
                    text(
                        """
                        ALTER TABLE trains
                        RENAME COLUMN symbol TO number
                        """
                    )
                )

                columns.remove("symbol")
                columns.add("number")

            train_columns = {
                "train_type": "VARCHAR(50)",
                "priority": "INTEGER",
                "operating_days": "VARCHAR(100)",
                "scheduled_departure": "TIME",
                "scheduled_arrival": "TIME",
            }

            for column_name, column_type in train_columns.items():

                if column_name not in columns:

                    connection.execute(
                        text(
                            f"ALTER TABLE trains "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )

    #
    # Link the existing Industry system to general operational
    # Locations and LocationTracks. Existing Industry IDs and
    # IndustryTrack IDs remain unchanged.
    #

    if inspector.has_table(
        "industries"
    ):

        industry_columns = {
            column["name"]
            for column in inspector.get_columns(
                "industries"
            )
        }

        with engine.begin() as connection:

            if "operating_location_id" not in industry_columns:

                connection.execute(
                    text(
                        """
                        ALTER TABLE industries
                        ADD COLUMN operating_location_id INTEGER
                        REFERENCES locations(id)
                        """
                    )
                )

            connection.execute(
                text(
                    """
                    INSERT OR IGNORE INTO locations (
                        name,
                        location_type,
                        active
                    )
                    SELECT name, 'INDUSTRY', 1
                    FROM industries
                    WHERE TRIM(name) != ''
                    """
                )
            )

            connection.execute(
                text(
                    """
                    UPDATE industries
                    SET operating_location_id = (
                        SELECT locations.id
                        FROM locations
                        WHERE locations.name = industries.name
                    )
                    """
                )
            )

    if inspector.has_table(
        "industry_tracks"
    ):

        track_columns = {
            column["name"]
            for column in inspector.get_columns(
                "industry_tracks"
            )
        }

        with engine.begin() as connection:

            if "operating_track_id" not in track_columns:

                connection.execute(
                    text(
                        """
                        ALTER TABLE industry_tracks
                        ADD COLUMN operating_track_id INTEGER
                        REFERENCES location_tracks(id)
                        """
                    )
                )

            connection.execute(
                text(
                    """
                    INSERT OR IGNORE INTO location_tracks (
                        location_id,
                        name,
                        track_type,
                        active
                    )
                    SELECT
                        industries.operating_location_id,
                        industry_tracks.name,
                        'INDUSTRY',
                        1
                    FROM industry_tracks
                    JOIN industries
                        ON industries.id = industry_tracks.industry_id
                    WHERE industries.operating_location_id IS NOT NULL
                    """
                )
            )

            connection.execute(
                text(
                    """
                    UPDATE industry_tracks
                    SET operating_track_id = (
                        SELECT location_tracks.id
                        FROM location_tracks
                        JOIN industries
                            ON industries.operating_location_id
                            = location_tracks.location_id
                        WHERE industries.id = industry_tracks.industry_id
                        AND location_tracks.name = industry_tracks.name
                    )
                    """
                )
            )

    if inspector.has_table(
        "location_tracks"
    ):

        location_track_columns = {
            column["name"]
            for column in inspector.get_columns(
                "location_tracks"
            )
        }

        if "traffic_use" not in location_track_columns:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE location_tracks
                        ADD COLUMN traffic_use VARCHAR(20)
                        NOT NULL DEFAULT 'BOTH'
                        """
                    )
                )

    #
    # Add industry_id to train_routes when required.
    #

    if inspector.has_table(
        "train_routes"
    ):

        columns = {
            column["name"]
            for column in inspector.get_columns(
                "train_routes"
            )
        }

        if "industry_id" not in columns:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE train_routes
                        ADD COLUMN industry_id INTEGER
                        REFERENCES industries(id)
                        """
                    )
                )

        if "location_id" not in columns:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE train_routes
                        ADD COLUMN location_id INTEGER
                        REFERENCES locations(id)
                        """
                    )
                )

        if "location_track_id" not in columns:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE train_routes
                        ADD COLUMN location_track_id INTEGER
                        REFERENCES location_tracks(id)
                        """
                    )
                )

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    INSERT OR IGNORE INTO locations (
                        name,
                        location_type,
                        active
                    )
                    SELECT DISTINCT
                        location,
                        CASE
                            WHEN LOWER(location) LIKE '%staging%'
                                THEN 'STAGING'
                            WHEN LOWER(location) LIKE '%interchange%'
                                THEN 'INTERCHANGE'
                            WHEN LOWER(location) LIKE '%yard%'
                                THEN 'YARD'
                            ELSE 'OTHER'
                        END,
                        1
                    FROM train_routes
                    WHERE TRIM(location) != ''
                    """
                )
            )

            connection.execute(
                text(
                    """
                    UPDATE train_routes
                    SET location_id = COALESCE(
                        (
                            SELECT industries.operating_location_id
                            FROM industries
                            WHERE industries.id = train_routes.industry_id
                        ),
                        (
                            SELECT locations.id
                            FROM locations
                            WHERE locations.name = train_routes.location
                        )
                    )
                    """
                )
            )

        #
        # Origin and destination are derived from the first and
        # last ordered route stops. This also corrects existing
        # Train records and clears endpoints for empty routes.
        #

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    UPDATE trains
                    SET origin = (
                        SELECT location
                        FROM train_routes
                        WHERE train_routes.train_id = trains.id
                        ORDER BY sequence, id
                        LIMIT 1
                    ),
                    destination = (
                        SELECT location
                        FROM train_routes
                        WHERE train_routes.train_id = trains.id
                        ORDER BY sequence DESC, id DESC
                        LIMIT 1
                    )
                    """
                )
            )

    #
    # Add execution fields introduced on the CarMove model.
    # Existing moves are PENDING because no completion state was
    # stored before this migration.
    #

    if inspector.has_table(
        "car_moves"
    ):

        columns = {
            column["name"]
            for column in inspector.get_columns(
                "car_moves"
            )
        }

        with engine.begin() as connection:

            if "status" not in columns:

                connection.execute(
                    text(
                        """
                        ALTER TABLE car_moves
                        ADD COLUMN status VARCHAR(20)
                        NOT NULL DEFAULT 'PENDING'
                        """
                    )
                )

            if "completed_at" not in columns:

                connection.execute(
                    text(
                        """
                        ALTER TABLE car_moves
                        ADD COLUMN completed_at DATETIME
                        """
                    )
                )

    #
    # Link existing structured Industry car positions to the
    # general Location and LocationTrack system.
    #

    if inspector.has_table(
        "cars"
    ):

        car_column_details = {
            column["name"]: column
            for column in inspector.get_columns(
                "cars"
            )
        }
        car_columns = set(car_column_details)

        with engine.begin() as connection:

            if "empty_weight_lbs" not in car_columns and "weight" in car_columns:
                connection.execute(
                    text(
                        """
                        ALTER TABLE cars
                        ADD COLUMN empty_weight_lbs INTEGER
                        """
                    )
                )

                connection.execute(
                    text(
                        """
                        UPDATE cars
                        SET empty_weight_lbs = CAST(ROUND(weight * 2000) AS INTEGER)
                        WHERE weight IS NOT NULL
                        """
                    )
                )

                connection.execute(
                    text(
                        """
                        ALTER TABLE cars
                        DROP COLUMN weight
                        """
                    )
                )

                car_columns.remove("weight")
                car_columns.add("empty_weight_lbs")

            if "empty_weight_lbs" not in car_columns:
                connection.execute(
                    text(
                        """
                        ALTER TABLE cars
                        ADD COLUMN empty_weight_lbs INTEGER
                        """
                    )
                )

                car_columns.add("empty_weight_lbs")

            empty_weight_type = str(
                car_column_details.get("empty_weight_lbs", {}).get("type", "")
            ).upper()

            if (
                "empty_weight_lbs" in car_column_details
                and "INT" not in empty_weight_type
            ):
                connection.execute(
                    text(
                        """
                        ALTER TABLE cars
                        RENAME COLUMN empty_weight_lbs
                        TO empty_weight_lbs_legacy
                        """
                    )
                )

                connection.execute(
                    text(
                        """
                        ALTER TABLE cars
                        ADD COLUMN empty_weight_lbs INTEGER
                        """
                    )
                )

                connection.execute(
                    text(
                        """
                        UPDATE cars
                        SET empty_weight_lbs = CAST(
                            ROUND(empty_weight_lbs_legacy) AS INTEGER
                        )
                        WHERE empty_weight_lbs_legacy IS NOT NULL
                        """
                    )
                )

                connection.execute(
                    text(
                        """
                        ALTER TABLE cars
                        DROP COLUMN empty_weight_lbs_legacy
                        """
                    )
                )

            if "load_limit_lbs" not in car_columns:
                connection.execute(
                    text(
                        """
                        ALTER TABLE cars
                        ADD COLUMN load_limit_lbs INTEGER
                        """
                    )
                )

            if "operating_location_id" not in car_columns:
                connection.execute(
                    text(
                        """
                        ALTER TABLE cars
                        ADD COLUMN operating_location_id INTEGER
                        REFERENCES locations(id)
                        """
                    )
                )

            if "operating_track_id" not in car_columns:
                connection.execute(
                    text(
                        """
                        ALTER TABLE cars
                        ADD COLUMN operating_track_id INTEGER
                        REFERENCES location_tracks(id)
                        """
                    )
                )

            connection.execute(
                text(
                    """
                    UPDATE cars
                    SET operating_location_id = (
                        SELECT industries.operating_location_id
                        FROM industries
                        WHERE industries.id = cars.industry_id
                    )
                    WHERE industry_id IS NOT NULL
                    """
                )
            )

            connection.execute(
                text(
                    """
                    UPDATE cars
                    SET operating_track_id = (
                        SELECT industry_tracks.operating_track_id
                        FROM industry_tracks
                        WHERE industry_tracks.id = cars.track_id
                    )
                    WHERE track_id IS NOT NULL
                    """
                )
            )

    # Waybills can now begin or end on any operational LocationTrack,
    # including yard, staging, and interchange tracks.
    _upgrade_waybill_location_schema()
    _upgrade_waybill_load_schema()
    _upgrade_waybill_archive_schema()
