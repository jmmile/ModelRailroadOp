"""Fail-closed resource/provenance checks; never import the application or its DB."""

import hashlib
import os
from pathlib import Path
import sys
import zipfile

FORBIDDEN_SUFFIXES = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".csv",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".pdf",
    ".docx",
    ".xlsx",
    ".bak",
    ".log",
}
FORBIDDEN_FOLDERS = {
    "data",
    "backups",
    "car_images",
    "locomotive_images",
    "passenger_images",
    "web_test",
    "tests",
    "test_data",
    "test-data",
    ".git",
}
WEB_PAGE = "modelrailroadops/web/static/index.html"
APP_ICON = "modelrailroadops/resources/application.ico"
REQUIRED_MODULES = {
    "modelrailroadops.services.companion_controller",
    "modelrailroadops.ui.widgets.companion_panel",
    "modelrailroadops.web.server",
    "fastapi",
    "uvicorn",
    "pydantic",
    "modelrailroadops.services.locomotive_image_service",
    "modelrailroadops.services.passenger_image_service",
    "modelrailroadops.services.image_storage",
    "modelrailroadops.services.database_backup_service",
    "modelrailroadops.ui.dialogs.add_locomotive_dialog",
    "modelrailroadops.ui.dialogs.add_passenger_car_dialog",
}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check_name(name):
    path = Path(name.replace("\\", "/"))
    parts = {part.casefold() for part in path.parts}
    if path.is_absolute() or ".." in parts or parts & FORBIDDEN_FOLDERS:
        raise ValueError(f"Forbidden packaged path: {name}")
    if path.suffix.casefold() in FORBIDDEN_SUFFIXES or ".db-" in path.name.lower():
        raise ValueError(f"Forbidden packaged data: {name}")


def audit_inputs(entries, project):
    """Reject local personal inputs even if renamed to a benign destination."""
    project = Path(project).resolve()
    for destination, source, kind in entries:
        # A module called asyncio.log is Python code, not a personal log file.
        check_name(destination.replace(".", "/") if kind.startswith("PYMODULE") else destination)
        if not source or source == "-":
            continue
        path = Path(source).resolve()
        if not path.is_relative_to(project):
            trusted = [Path(sys.base_prefix).resolve()]
            if os.environ.get("WINDIR"):
                trusted.append(Path(os.environ["WINDIR"]).resolve())
            if not any(path.is_relative_to(folder) for folder in trusted):
                raise ValueError(f"Unapproved external input: {path}")
            continue  # Python installation or Windows system runtime.
        relative = path.relative_to(project)
        if relative.parts[0] == ".venv":
            continue  # Installed dependencies, still subject to destination audit.
        permitted = (
            relative.as_posix() == "src/" + WEB_PAGE
            or (relative.as_posix() == "src/" + APP_ICON and destination.replace("\\", "/") == APP_ICON)
            or (relative.as_posix() == "build/release/ModelRailroadOperations/base_library.zip"
                and destination == "base_library.zip")
            or (
                relative.as_posix().startswith("src/modelrailroadops/")
                and path.suffix == ".py"
            )
            or relative.as_posix()
            in {"packaging/launcher.py", "packaging/verify_build.py"}
        )
        if not permitted:
            raise ValueError(f"Unapproved project input: {relative}")


def audit_bundle(bundle, project):
    from PyInstaller.archive.readers import CArchiveReader

    bundle, project = Path(bundle), Path(project)
    files = []
    for path in sorted(bundle.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise ValueError(f"Linked bundle path: {path}")
        relative = path.relative_to(bundle).as_posix()
        check_name(relative)
        if path.is_file():
            if path.suffix.lower() == ".zip":
                if relative != "_internal/base_library.zip":
                    raise ValueError(f"Unexpected archive: {relative}")
                with zipfile.ZipFile(path) as archive:
                    for name in archive.namelist():
                        check_name(name)
                        if not name.endswith(".pyc"):
                            raise ValueError(f"Unexpected library payload: {name}")
            files.append(
                {"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)}
            )
    required = [
        "Model Railroad Operations.exe",
        "Model Railroad Companion.exe",
        "_internal/python313.dll",
        "_internal/" + WEB_PAGE,
        "_internal/" + APP_ICON,
        "_internal/PySide6/plugins/platforms/qwindows.dll",
    ]
    for name in required:
        if not (bundle / name).is_file():
            raise ValueError(f"Missing required runtime resource: {name}")
    if digest(bundle / "_internal" / WEB_PAGE) != digest(project / "src" / WEB_PAGE):
        raise ValueError("Bundled companion page does not match current source")
    if digest(bundle / "_internal" / APP_ICON) != digest(project / "src" / APP_ICON):
        raise ValueError("Bundled icon does not match current source")
    for executable in required[:2]:
        archive = CArchiveReader(str(bundle / executable))
        modules = set(archive.open_embedded_archive("PYZ.pyz").toc)
        if missing := REQUIRED_MODULES - modules:
            raise ValueError(f"Missing modules in {executable}: {sorted(missing)}")
        for name in archive.toc:
            check_name(name)
    return files
