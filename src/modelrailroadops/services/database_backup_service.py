import sqlite3
import os
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from modelrailroadops.database import database
from modelrailroadops.services.image_storage import CAR_IMAGES, MANAGED_IMAGE_FOLDERS


class DatabaseBackupService:
    """Create and restore validated snapshots of the application database."""

    @staticmethod
    def create_layout_backup(destination):
        """Publish a complete archive only after its database and ZIP validate."""
        destination = Path(destination)
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
                staging = Path(temporary)
                snapshot = staging / "railroad.db"
                DatabaseBackupService._copy_database(database.DATABASE_FILE, snapshot)
                valid, message = DatabaseBackupService._validate_database(snapshot)
                if not valid:
                    return False, message
                archive = staging / "layout.zip"
                with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
                    output.write(snapshot, "railroad.db")
                    for folder in MANAGED_IMAGE_FOLDERS:
                        images = database.DATABASE_FILE.parent / folder
                        if images.is_symlink() or images.is_junction():
                            raise OSError(f"Image folder must not be a link: {images}")
                        # Explicit empty entries distinguish new snapshots from old backups.
                        output.writestr(folder + "/", b"")
                        if images.is_dir():
                            for picture in images.rglob("*"):
                                if picture.is_symlink() or picture.is_junction():
                                    raise OSError(f"Image path must not be a link: {picture}")
                                if picture.is_file():
                                    output.write(picture, folder + "/" + picture.relative_to(images).as_posix())
                with zipfile.ZipFile(archive) as check:
                    if check.testzip() is not None:
                        return False, "Backup archive verification failed."
                os.replace(archive, destination)
            return True, destination
        except (OSError, sqlite3.DatabaseError, zipfile.BadZipFile) as exc:
            return False, f"Layout backup failed: {exc}"

    @staticmethod
    def restore_layout_backup(source):
        """Stage and validate an archive before touching live data or images."""
        root = database.DATABASE_FILE.parent
        safety = (
            root
            / "backups"
            / (
                "railroad-before-restore-"
                + datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
                + ".zip"
            )
        )
        try:
            with tempfile.TemporaryDirectory(dir=root) as temporary:
                staging = Path(temporary)
                incoming = staging / "incoming"
                incoming.mkdir()
                # Old archives only knew car images. Preserve newer collections
                # when those folders are absent rather than silently deleting them.
                restore_folders = {CAR_IMAGES}
                (incoming / CAR_IMAGES).mkdir()
                with zipfile.ZipFile(source) as archive:
                    names = set()
                    for member in archive.infolist():
                        name = member.filename
                        target = (incoming / name).resolve()
                        if (
                            "\\" in name
                            or ":" in name
                            or any(part in (".", "..") for part in name.split("/"))
                            or target == incoming.resolve()
                            or incoming.resolve() not in target.parents
                            or (
                                name != "railroad.db"
                                and not any(name.startswith(folder + "/") for folder in MANAGED_IMAGE_FOLDERS)
                            )
                            or name.casefold() in names
                        ):
                            return (
                                False,
                                "The backup contains unexpected or unsafe file names.",
                            )
                        names.add(name.casefold())
                        folder = name.split("/", 1)[0]
                        if folder in MANAGED_IMAGE_FOLDERS:
                            restore_folders.add(folder)
                        if member.is_dir():
                            target.mkdir(parents=True, exist_ok=True)
                        else:
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with (
                                archive.open(member) as source_file,
                                target.open("wb") as output,
                            ):
                                shutil.copyfileobj(source_file, output)
                valid, message = DatabaseBackupService._validate_database(
                    incoming / "railroad.db"
                )
                if not valid:
                    return False, message
                saved, message = DatabaseBackupService.create_layout_backup(safety)
                if not saved:
                    return False, f"Restore cancelled; safety backup failed: {message}"
                previous_db = staging / "previous.db"
                DatabaseBackupService._copy_database(
                    database.DATABASE_FILE, previous_db
                )
                moved_old_images = []
                installed_images = []
                try:
                    database.engine.dispose()
                    DatabaseBackupService._copy_database(
                        incoming / "railroad.db", database.DATABASE_FILE
                    )
                    database.initialize_database()
                    for folder in MANAGED_IMAGE_FOLDERS:
                        if folder not in restore_folders:
                            continue
                        images = root / folder
                        if images.exists():
                            images.rename(staging / ("previous-" + folder))
                            moved_old_images.append(folder)
                        (incoming / folder).rename(images)
                        installed_images.append(folder)
                except Exception as exc:  # noqa: BLE001 - recover migration and filesystem failures
                    try:
                        database.engine.dispose()
                        DatabaseBackupService._copy_database(
                            previous_db, database.DATABASE_FILE
                        )
                        for folder in reversed(installed_images):
                            (root / folder).rename(staging / ("failed-" + folder))
                        for folder in reversed(moved_old_images):
                            (staging / ("previous-" + folder)).rename(root / folder)
                    except Exception as recovery_exc:  # noqa: BLE001
                        return (
                            False,
                            f"Restore failed: {exc}. Recovery failed: {recovery_exc}. Recover using {safety}.",
                        )
                    return False, f"Restore failed; previous layout restored: {exc}"
                return True, safety
        except (
            OSError,
            sqlite3.DatabaseError,
            zipfile.BadZipFile,
            RuntimeError,
        ) as exc:
            return False, f"Layout restore failed: {exc}"

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
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        return (
            database.DATABASE_FILE.parent
            / "backups"
            / f"railroad-backup-{timestamp}.zip"
        )

    @staticmethod
    def _validate_database(path):
        path = Path(path)

        if not path.is_file():
            return False, "The selected backup file does not exist."

        try:
            connection = sqlite3.connect(
                path.resolve().as_uri() + "?mode=ro",
                uri=True,
            )
            try:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()
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

        source_connection = sqlite3.connect(
            source.resolve().as_uri() + "?mode=ro", uri=True
        )
        try:
            destination_connection = sqlite3.connect(str(destination))
            try:
                source_connection.backup(destination_connection)
            finally:
                destination_connection.close()
        finally:
            source_connection.close()

    @staticmethod
    def create_backup(destination):
        destination = Path(destination)
        if destination.suffix.casefold() == ".zip":
            return DatabaseBackupService.create_layout_backup(destination)
        if destination.suffix.casefold() != ".db":
            destination = destination.with_suffix(".db")

        try:
            if destination.resolve() == database.DATABASE_FILE.resolve():
                return False, "Choose a file other than the active database."

            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
                snapshot = Path(temporary) / "snapshot.db"
                DatabaseBackupService._copy_database(database.DATABASE_FILE, snapshot)
                valid, message = DatabaseBackupService._validate_database(snapshot)
                if not valid:
                    return False, message
                os.replace(snapshot, destination)
        except (OSError, sqlite3.DatabaseError) as exc:
            return False, f"The backup could not be created: {exc}"

        return True, destination

    @staticmethod
    def restore_backup(source):
        source = Path(source)
        if source.suffix.casefold() == ".zip":
            return DatabaseBackupService.restore_layout_backup(source)
        valid, message = DatabaseBackupService._validate_database(source)
        if not valid:
            return False, message

        if source.resolve() == database.DATABASE_FILE.resolve():
            return False, "The selected file is already the active database."

        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        safety_backup = (
            database.DATABASE_FILE.parent
            / "backups"
            / f"railroad-before-restore-{timestamp}.db"
        )

        backed_up, message = DatabaseBackupService.create_backup(safety_backup)
        if not backed_up:
            return False, f"Restore cancelled; safety backup failed: {message}"
        try:
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
            except Exception as recovery_exc:  # noqa: BLE001
                return False, (
                    f"The database restore failed: {exc}. The automatic "
                    f"recovery also failed: {recovery_exc}. The safety "
                    f"backup remains at {safety_backup}."
                )
            return False, f"The database could not be restored: {exc}"

        return True, safety_backup
