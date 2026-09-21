"""Managed equipment pictures; file changes roll back if the DB save fails.

Locomotive defaults preserve the existing API; passenger pictures use a separate
collection and prefix through passenger_image_service.
"""

from contextlib import contextmanager
import os
from pathlib import Path
import tempfile
from threading import RLock

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QImage

from modelrailroadops import paths
from modelrailroadops.services.image_storage import LOCOMOTIVE_IMAGES, PASSENGER_IMAGES

_lock = RLock()
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def image_directory(collection=LOCOMOTIVE_IMAGES):
    if collection not in (LOCOMOTIVE_IMAGES, PASSENGER_IMAGES):
        raise ValueError("Unknown equipment picture collection.")
    return paths.DATA_DIRECTORY / collection


def image_key(reporting_mark, number, collection=LOCOMOTIVE_IMAGES):
    """Reversible escaping avoids punctuation/space filename collisions."""

    def component(value):
        return "".join(
            (
                chr(byte)
                if 65 <= byte <= 90 or 48 <= byte <= 57 or byte == 45
                else f"%{byte:02X}"
            )
            for byte in value.strip().upper().encode("utf-8")
        )

    # Prefix also avoids Windows reserved device filenames.
    prefix = "P" if collection == PASSENGER_IMAGES else "L"
    return f"{prefix}_{component(reporting_mark)}_{component(number)}"


def find_image(reporting_mark, number, collection=LOCOMOTIVE_IMAGES):
    root = image_directory(collection)
    if not root.exists():
        return None
    key = image_key(reporting_mark, number, collection).casefold()
    matches = [
        path
        for path in root.iterdir()
        if path.stem.casefold() == key and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if len(matches) > 1:
        raise ValueError(
            "Multiple pictures match this equipment. Resolve the duplicate files first."
        )
    if matches and (matches[0].is_symlink() or not matches[0].is_file()):
        raise ValueError(
            "The managed picture must be a regular file, not a link or folder."
        )
    return matches[0] if matches else None


def import_picture(filename):
    """Validate and normalize to PNG in memory; never modify the source photo."""
    path = Path(filename)
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Select a PNG, JPG, or JPEG picture.")
    image = QImage(str(path))
    if image.isNull():
        raise ValueError("This file cannot be read as a picture.")
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise ValueError("Unable to prepare this picture.")
    return bytes(buffer.data())


def _replace(path, contents):
    """Write completely before replacing a managed file."""
    descriptor, temporary = tempfile.mkstemp(prefix=".picture-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(contents)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def picture_change(
    old_identity, new_identity, picture=None, remove=False, collection=LOCOMOTIVE_IMAGES
):
    """Hold reversible file changes around a database transaction's commit.

    None preserves the picture; bytes replace it; remove=True removes it.
    Only files resolved inside our dedicated image directory are touched.
    """
    with _lock:
        root = image_directory(collection)
        if root.is_symlink() or root.is_junction():
            raise ValueError(
                "The equipment picture directory must not be a symbolic link."
            )
        old = find_image(*old_identity, collection=collection) if old_identity else None
        destination = find_image(*new_identity, collection=collection)
        if destination is not None and destination != old:
            raise ValueError(
                "A picture already exists for the new equipment identity. Nothing was overwritten."
            )
        if picture is not None and QImage.fromData(picture, "PNG").isNull():
            raise ValueError("The selected picture is invalid.")
        if (
            picture is None
            and not remove
            and (
                old is None
                or image_key(*old_identity, collection=collection)
                == image_key(*new_identity, collection=collection)
            )
        ):
            yield
            return

        target = root / (
            image_key(*new_identity, collection=collection)
            + (".png" if picture is not None else old.suffix if old else ".png")
        )
        contents = (
            None
            if remove
            else picture if picture is not None else old.read_bytes() if old else None
        )
        original = old.read_bytes() if old else None
        created = False
        old_removed = False
        try:
            if contents is not None:
                root.mkdir(parents=True, exist_ok=True)
                if old is not None and target == old:
                    _replace(target, contents)
                    created = True
                else:
                    # Exclusive creation also protects a destination appearing after discovery.
                    with target.open("xb") as stream:
                        created = True
                        stream.write(contents)
            if old is not None and (remove or target != old):
                old.unlink()
                old_removed = True
            yield
        except BaseException:
            if old is not None and (old_removed or (created and target == old)):
                _replace(old, original)
            if created and target != old:
                target.unlink(missing_ok=True)
            raise
