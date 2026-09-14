import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from modelrailroadops.database import database


class DatabaseBackupService:
    """Create and restore validated snapshots of the application database."""

    @staticmethod
    def automatic_backup(session):
        """Snapshot committed data before activation, using the caller's database."""
        source = Path(session.get_bind().url.database).resolve()
        folder = source.parent / "backups" / "automatic"
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        destination = folder / f"railroad-auto-{timestamp}.db"
        try:
            DatabaseBackupService._copy_database(source, destination)
            valid, message = DatabaseBackupService._validate_database(destination)
            if not valid:
                return False, message
            # Only prune this feature's files inside its dedicated directory.
            backups = sorted(folder.glob("railroad-auto-*.db"), reverse=True)
            for old_backup in backups[10:]:
                if old_backup.resolve().parent == folder.resolve():
                    old_backup.unlink()
        except (OSError, sqlite3.DatabaseError) as exc:
            return False, f"Automatic backup failed: {exc}"
        return True, destination

    @staticmethod
    def default_backup_path():
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        return (
            database.DATABASE_FILE.parent
            / "backups"
            / f"railroad-backup-{timestamp}.db"
        )

    @staticmethod
    def _validate_database(path):
        path = Path(path)

        if not path.is_file():
            return False, "The selected backup file does not exist."

        try:
            connection = sqlite3.connect(
                f"file:{path.resolve().as_posix()}?mode=ro",
                uri=True,
            )
            try:
                integrity = connection.execute(
                    "PRAGMA integrity_check"
                ).fetchone()
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    ).fetchall()
                }
            finally:
                connection.close()
        except sqlite3.DatabaseError as exc:
            return False, f"The selected file is not a valid database: {exc}"

        if not integrity or integrity[0] != "ok":
            return False, "The selected database failed its integrity check."

        required_tables = {"cars", "industries", "locations", "waybills"}
        if not required_tables.issubset(tables):
            return False, (
                "The selected file is not a Model Railroad Operations backup."
            )

        return True, ""

    @staticmethod
    def _copy_database(source, destination):
        source = Path(source)
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        source_connection = sqlite3.connect(str(source))
        destination_connection = sqlite3.connect(str(destination))
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
            source_connection.close()

    @staticmethod
    def create_backup(destination):
        destination = Path(destination)
        if destination.suffix.casefold() != ".db":
            destination = destination.with_suffix(".db")

        try:
            if destination.resolve() == database.DATABASE_FILE.resolve():
                return False, "Choose a file other than the active database."

            DatabaseBackupService._copy_database(
                database.DATABASE_FILE,
                destination,
            )
            valid, message = DatabaseBackupService._validate_database(
                destination
            )
            if not valid:
                destination.unlink(missing_ok=True)
                return False, message
        except (OSError, sqlite3.DatabaseError) as exc:
            return False, f"The backup could not be created: {exc}"

        return True, destination

    @staticmethod
    def restore_backup(source):
        source = Path(source)
        valid, message = DatabaseBackupService._validate_database(source)
        if not valid:
            return False, message

        if source.resolve() == database.DATABASE_FILE.resolve():
            return False, "The selected file is already the active database."

        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        safety_backup = (
            database.DATABASE_FILE.parent
            / "backups"
            / f"railroad-before-restore-{timestamp}.db"
        )

        try:
            DatabaseBackupService._copy_database(
                database.DATABASE_FILE,
                safety_backup,
            )
            database.engine.dispose()
            DatabaseBackupService._copy_database(
                source,
                database.DATABASE_FILE,
            )
            database.initialize_database()
        except Exception as exc:  # noqa: BLE001 - migrations may raise broadly
            try:
                database.engine.dispose()
                DatabaseBackupService._copy_database(
                    safety_backup,
                    database.DATABASE_FILE,
                )
                database.initialize_database()
            except Exception as recovery_exc:  # noqa: BLE001
                return False, (
                    f"The database restore failed: {exc}. The automatic "
                    f"recovery also failed: {recovery_exc}. The safety "
                    f"backup remains at {safety_backup}."
                )
            return False, f"The database could not be restored: {exc}"

        return True, safety_backup
