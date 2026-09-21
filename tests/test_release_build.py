"""Release gates and packaging safety checks without invoking a real build."""

import importlib.util
from pathlib import Path
import sys

import pytest


@pytest.fixture
def release(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "packaging"
    monkeypatch.syspath_prepend(str(folder))
    import release_build

    return release_build


@pytest.mark.parametrize(
    "name",
    [
        "data/railroad.db",
        "renamed.csv",
        "photo.JPG",
        "Car_Images/x",
        "test-data/file.txt",
        "backups/a.zip",
        "../outside",
        "layout.db-wal",
    ],
)
def test_reject_personal_payload(release, name):
    from release_audit import check_name

    with pytest.raises(ValueError):
        check_name(name)


def test_input_provenance_rejects_renamed_personal_file(release, tmp_path):
    from release_audit import audit_inputs

    with pytest.raises(ValueError, match="Unapproved"):
        audit_inputs(
            [("harmless.txt", str(tmp_path / "data/private.txt"), "DATA")], tmp_path
        )
    audit_inputs(
        [
            (
                "modelrailroadops/web/static/index.html",
                str(tmp_path / "src/modelrailroadops/web/static/index.html"),
                "DATA",
            )
        ],
        tmp_path,
    )


def test_module_name_is_not_a_data_extension(release, tmp_path):
    from release_audit import audit_inputs
    audit_inputs([("asyncio.log", str(tmp_path / ".venv/Lib/asyncio/log.py"), "PYMODULE")], tmp_path)
    with pytest.raises(ValueError):
        audit_inputs([("asyncio.log", str(tmp_path / ".venv/Lib/asyncio/log.py"), "DATA")], tmp_path)


def test_arbitrary_external_data_is_rejected(release, tmp_path):
    from release_audit import audit_inputs
    project = tmp_path / "project"
    project.mkdir()
    with pytest.raises(ValueError, match="external"):
        audit_inputs([("harmless.txt", str(tmp_path / "private.txt"), "DATA")], project)


@pytest.mark.parametrize(
    "target", [".", "..", "data", "src", "build", "dist", "release/../data"]
)
def test_cleanup_refuses_non_artifact_paths(release, tmp_path, target):
    with pytest.raises(ValueError):
        release.clean_owned(tmp_path, target)


def test_cleanup_preserves_user_data(release, tmp_path):
    (tmp_path / "data").mkdir()
    protected = tmp_path / "data/railroad.db"
    protected.write_bytes(b"private")
    (tmp_path / "build/release").mkdir(parents=True)
    (tmp_path / "build/release/old.txt").touch()
    release.clean_owned(tmp_path, "build/release")
    assert protected.read_bytes() == b"private"
    assert not (tmp_path / "build/release").exists()


def test_test_failure_aborts_before_cleanup_or_build(release, tmp_path, monkeypatch):
    monkeypatch.setattr(release, "preflight", lambda compiler: "compiler")
    calls = []

    def failed(command, *args, **kwargs):
        calls.append(command)
        raise RuntimeError("pytest failed")

    monkeypatch.setattr(release, "run", failed)
    monkeypatch.setattr(
        release,
        "clean_owned",
        lambda *args: pytest.fail("Cleanup reached after failed tests"),
    )
    with pytest.raises(RuntimeError, match="pytest failed"):
        release.build(tmp_path, "")
    assert len(calls) == 1 and "pytest" in calls[0]


def test_skipped_tests_abort_release(release, tmp_path, monkeypatch):
    monkeypatch.setattr(release, "preflight", lambda compiler: "compiler")

    def skipped(command, *args, **kwargs):
        xml = next(
            part.split("=", 1)[1] for part in command if part.startswith("--junitxml=")
        )
        Path(xml).write_text(
            '<testsuites><testsuite tests="2" failures="0" errors="0" skipped="1"/></testsuites>'
        )

    monkeypatch.setattr(release, "run", skipped)
    monkeypatch.setattr(
        release,
        "clean_owned",
        lambda *args: pytest.fail("Cleanup reached with skipped tests"),
    )
    with pytest.raises(RuntimeError, match="unskipped"):
        release.build(tmp_path, "")


def test_verifier_refuses_existing_layout(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "packaging/verify_build.py"
    spec = importlib.util.spec_from_file_location("isolated_verify_build", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("MODELRAILROADOPS_DATA_DIR", str(tmp_path))
    (tmp_path / ".build-verification").touch()
    database = tmp_path / "railroad.db"
    database.write_bytes(b"never touch")
    assert module.verify() == 2
    assert database.read_bytes() == b"never touch"


@pytest.mark.parametrize("failure", ["pyinstaller.log", "verification.log", "inno.log", None])
def test_pipeline_gates_and_successful_publication(release, tmp_path, monkeypatch, failure):
    import json
    monkeypatch.setenv("PATH", "UNTRUSTED_SEARCH_DIRECTORY")
    monkeypatch.setattr(release, "preflight", lambda compiler: "compiler")
    monkeypatch.setattr(release, "audit_bundle", lambda *args: [])
    calls = []
    def fake_run(command, project, environment, log, **kwargs):
        calls.append(log.name)
        if log.name != "pytest.log":
            assert "UNTRUSTED_SEARCH_DIRECTORY" not in environment["PATH"]
        if log.name == failure:
            raise RuntimeError("Injected failure")
        if log.name == "pytest.log":
            xml = next(part.split("=", 1)[1] for part in command if part.startswith("--junitxml="))
            Path(xml).write_text('<testsuites><testsuite tests="2" failures="0" errors="0" skipped="0"/></testsuites>')
        elif log.name == "verification.log":
            (Path(environment["MODELRAILROADOPS_DATA_DIR"]) / "verification.json").write_text(json.dumps({"result": "passed"}))
        elif log.name == "inno.log":
            staging = next(part.split("=", 1)[1] for part in command if part.startswith("/DReleaseOutput="))
            (Path(staging) / release.INSTALLER).write_bytes(b"synthetic-installer" * 100000)
    monkeypatch.setattr(release, "run", fake_run)
    if failure:
        with pytest.raises(RuntimeError, match="Injected"):
            release.build(tmp_path, "")
        assert not (tmp_path / "release").exists()
        assert calls[-1] == failure
    else:
        release.build(tmp_path, "")
        manifest = json.loads((tmp_path / "release/release-manifest.json").read_text())
        assert manifest["sha256"] == release.digest(tmp_path / "release" / release.INSTALLER)
        assert (tmp_path / "release" / (release.INSTALLER + ".sha256")).is_file()
