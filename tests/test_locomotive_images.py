"""Picture storage and Qt editor tests use only isolated files and databases."""

import pytest
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QFileDialog, QMessageBox
from sqlalchemy import event

from modelrailroadops import paths
from modelrailroadops.services import locomotive_image_service as images
from modelrailroadops.services import locomotive_service
from modelrailroadops.services.locomotive_service import LocomotiveService
from modelrailroadops.ui.dialogs.add_locomotive_dialog import AddLocomotiveDialog


@pytest.fixture
def storage(tmp_path, monkeypatch, test_database):
    monkeypatch.setattr(paths, "DATA_DIRECTORY", tmp_path / "runtime")
    monkeypatch.setattr(locomotive_service, "SessionLocal", test_database.SessionLocal)
    return tmp_path


def photo(root, name="source.jpg", color="red"):
    path = root / name
    image = QImage(320, 100, QImage.Format.Format_RGB32)
    image.fill(QColor(color))
    assert image.save(str(path))
    return path


def add_with_picture(root):
    source = photo(root)
    return LocomotiveService.add("UP", "1996", picture=images.import_picture(source))


@pytest.mark.parametrize("extension", ["png", "jpg", "jpeg", "JPG"])
def test_import_formats_and_preview_data(storage, extension):
    source = photo(storage, "source." + extension)
    original = source.read_bytes()
    payload = images.import_picture(source)
    locomotive = LocomotiveService.add("UP", "1996", picture=payload)
    managed = images.find_image(locomotive.reporting_mark, locomotive.number)
    assert managed == paths.DATA_DIRECTORY / "Locomotive_Images" / "L_UP_1996.png"
    assert managed.read_bytes() == payload
    assert not QImage(str(managed)).isNull()
    assert source.read_bytes() == original


def test_no_image_does_not_create_directory(storage):
    locomotive = LocomotiveService.add("GN", "A1", horsepower=1500)
    assert locomotive.horsepower == 1500
    assert images.find_image("GN", "A1") is None
    assert not images.image_directory().exists()
    assert LocomotiveService.update(locomotive.id, "GN", "A2").number == "A2"


def test_safe_distinct_filename_keys():
    identities = [
        ("A B", "1"),
        ("A_B", "1"),
        ("A/B", "1"),
        ("A%B", "1"),
        ("CON", "N:1"),
        ("A", "B_1"),
    ]
    keys = [images.image_key(*identity) for identity in identities]
    assert len(set(keys)) == len(keys)
    assert all(not any(c in key for c in '/\\:*?"<>| ') for key in keys)
    assert images.image_key(" up ", "a1") == images.image_key("UP", "A1")


@pytest.mark.parametrize("extension", [".png", ".jpg", ".jpeg", ".JPG"])
def test_discover_supported_extensions(storage, extension):
    images.image_directory().mkdir(parents=True)
    path = images.image_directory() / ("L_UP_1996" + extension)
    photo(path.parent, path.name)
    assert images.find_image("up", "1996") == path


def test_replace_rename_remove_and_preserve_source(storage):
    locomotive = add_with_picture(storage)
    source = photo(storage, "replacement.png", "blue")
    payload = images.import_picture(source)
    LocomotiveService.update(locomotive.id, "UP", "1996", picture=payload)
    assert images.find_image("UP", "1996").read_bytes() == payload
    LocomotiveService.update(locomotive.id, "GN", "A 1")
    assert images.find_image("UP", "1996") is None
    assert images.find_image("GN", "A 1").read_bytes() == payload
    LocomotiveService.update(locomotive.id, "GN", "A 1", remove_picture=True)
    assert images.find_image("GN", "A 1") is None
    assert source.exists()


def test_collision_preserves_image_and_database(storage):
    locomotive = add_with_picture(storage)
    old = images.find_image("UP", "1996").read_bytes()
    collision = photo(images.image_directory(), "L_GN_1.jpg", "blue")
    original_collision = collision.read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        LocomotiveService.update(locomotive.id, "GN", "1")
    assert LocomotiveService.get_by_id(locomotive.id).reporting_mark == "UP"
    assert images.find_image("UP", "1996").read_bytes() == old
    assert collision.read_bytes() == original_collision


def test_case_collision_with_other_locomotive(storage):
    locomotive = add_with_picture(storage)
    with pytest.raises(ValueError, match="same picture identity"):
        LocomotiveService.add("up", "1996")
    assert LocomotiveService.get_by_id(locomotive.id).number == "1996"


def test_duplicate_and_ambiguous_images_are_preserved(storage):
    add_with_picture(storage)
    assert LocomotiveService.add("UP", "1996") is None
    photo(images.image_directory(), "L_UP_1996.jpg")
    with pytest.raises(ValueError, match="Multiple pictures"):
        images.find_image("UP", "1996")
    assert len(list(images.image_directory().iterdir())) == 2


@pytest.mark.parametrize("action", ["replace", "rename", "remove", "add"])
def test_commit_failure_restores_files_and_database(storage, test_database, action):
    locomotive = add_with_picture(storage)
    before = {p.name: p.read_bytes() for p in images.image_directory().iterdir()}

    def fail_commit(session):
        raise RuntimeError("Simulated database failure")

    session_class = test_database.SessionLocal.class_
    event.listen(session_class, "before_commit", fail_commit)
    try:
        with pytest.raises(RuntimeError, match="Simulated"):
            if action == "add":
                LocomotiveService.add(
                    "GN", "2", picture=images.import_picture(photo(storage))
                )
            else:
                LocomotiveService.update(
                    locomotive.id,
                    "GN" if action == "rename" else "UP",
                    "1996",
                    picture=(
                        images.import_picture(photo(storage, "blue.png", "blue"))
                        if action == "replace"
                        else None
                    ),
                    remove_picture=action == "remove",
                )
    finally:
        event.remove(session_class, "before_commit", fail_commit)
    assert {
        p.name: p.read_bytes() for p in images.image_directory().iterdir()
    } == before
    assert LocomotiveService.get_by_id(locomotive.id).reporting_mark == "UP"
    assert len(LocomotiveService.get_all()) == 1


def test_invalid_picture(storage):
    broken = storage / "broken.jpg"
    broken.write_bytes(b"not an image")
    with pytest.raises(ValueError, match="cannot be read"):
        images.import_picture(broken)
    with pytest.raises(ValueError, match="invalid"):
        LocomotiveService.add("UP", "1", picture=b"invalid")
    assert LocomotiveService.get_all() == []


def test_file_write_failure_rolls_back_database(storage, monkeypatch):
    locomotive = add_with_picture(storage)
    original = images.find_image("UP", "1996").read_bytes()

    def fail_replace(*args):
        raise OSError("Simulated disk failure")

    monkeypatch.setattr(images, "_replace", fail_replace)
    with pytest.raises(OSError, match="disk failure"):
        LocomotiveService.update(
            locomotive.id,
            "UP",
            "1996",
            picture=images.import_picture(photo(storage, "new.png", "blue")),
        )
    assert images.find_image("UP", "1996").read_bytes() == original
    assert LocomotiveService.get_by_id(locomotive.id).number == "1996"


def test_runtime_override_and_packaged_path(storage, monkeypatch):
    monkeypatch.setenv("MODELRAILROADOPS_DATA_DIR", str(storage / "override"))
    monkeypatch.setattr(paths, "DATA_DIRECTORY", paths.data_directory())
    assert images.image_directory() == storage / "override" / "Locomotive_Images"
    monkeypatch.delenv("MODELRAILROADOPS_DATA_DIR")
    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(storage / "local"))
    monkeypatch.setattr(paths, "DATA_DIRECTORY", paths.data_directory())
    assert (
        images.image_directory()
        == storage / "local" / "ModelRailroadOperations" / "Locomotive_Images"
    )


def choose(dialog, filename, monkeypatch):
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", lambda *args: (str(filename), "")
    )
    dialog.choose_picture()


def test_add_cancel_leaves_no_image_or_row(storage, qapp, monkeypatch):
    dialog = AddLocomotiveDialog()
    choose(dialog, photo(storage), monkeypatch)
    assert not dialog.picture_preview.pixmap().isNull()
    dialog.reject()
    assert not images.image_directory().exists()
    assert LocomotiveService.get_all() == []


@pytest.mark.parametrize("action", ["replace", "remove", "rename"])
def test_edit_cancel_preserves_existing(storage, qapp, monkeypatch, action):
    locomotive = add_with_picture(storage)
    old = images.find_image("UP", "1996").read_bytes()
    dialog = AddLocomotiveDialog(locomotive=locomotive)
    if action == "replace":
        choose(dialog, photo(storage, "blue.png", "blue"), monkeypatch)
    elif action == "remove":
        dialog.clear_picture()
    else:
        dialog.number.setText("2")
    dialog.reject()
    assert images.find_image("UP", "1996").read_bytes() == old
    assert LocomotiveService.get_by_id(locomotive.id).number == "1996"


def test_editor_save_reopen_and_remove(storage, qapp, monkeypatch):
    dialog = AddLocomotiveDialog()
    assert dialog.picture_preview.text() == "No Image Available"
    assert not dialog.remove_picture_button.isEnabled()
    dialog.reporting_mark.setText("UP")
    dialog.number.setText("1996")
    dialog.horsepower.setText("3000")
    choose(dialog, photo(storage), monkeypatch)
    dialog.save()
    assert dialog.result() == dialog.DialogCode.Accepted
    locomotive = LocomotiveService.get_all()[0]
    assert locomotive.horsepower == 3000
    reopened = AddLocomotiveDialog(locomotive=locomotive)
    preview = reopened.picture_preview.pixmap()
    assert preview.width() <= 400 and preview.height() <= 150
    assert abs(preview.width() / preview.height() - 3.2) < 0.05
    reopened.clear_picture()
    reopened.save()
    final = AddLocomotiveDialog(locomotive=LocomotiveService.get_by_id(locomotive.id))
    assert final.picture_preview.text() == "No Image Available"


def test_editor_collision_error_keeps_dialog_open(storage, qapp, monkeypatch):
    locomotive = add_with_picture(storage)
    photo(images.image_directory(), "L_GN_2.png")
    messages = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: messages.append(args[2]))
    dialog = AddLocomotiveDialog(locomotive=locomotive)
    dialog.reporting_mark.setText("GN")
    dialog.number.setText("2")
    dialog.save()
    assert messages and "already exists" in messages[0]
    assert dialog.result() != dialog.DialogCode.Accepted


def test_car_image_convention_unchanged(storage, monkeypatch):
    from modelrailroadops.ui.waybills import waybill_form

    monkeypatch.setattr(waybill_form, "DATA_DIRECTORY", paths.DATA_DIRECTORY)
    assert (
        waybill_form.WaybillFormRenderer.image_directory()
        == paths.DATA_DIRECTORY / "Car_Images"
    )
