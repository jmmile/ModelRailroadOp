"""Test-first Windows release orchestration invoked by build.ps1."""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

from release_audit import audit_bundle, digest

APP = "Model Railroad Operations"
INSTALLER = "ModelRailroadOperations-Setup-1.0.0.exe"


def clean_owned(project, relative):
    """Only these exact artifact directories may ever be recursively removed."""
    allowed = {"build/release", "dist/Model Railroad Operations", "release"}
    if relative not in allowed:
        raise ValueError(f"Refusing cleanup target: {relative}")
    project = project.resolve()
    target = project / relative
    if target.resolve() != target.absolute() or not target.resolve().is_relative_to(
        project
    ):
        raise ValueError(f"Cleanup path escapes project: {target}")
    for parent in [target, *target.parents]:
        if parent == project:
            break
        if parent.is_symlink() or parent.is_junction():
            raise ValueError(f"Linked cleanup path: {parent}")
    if target.exists():
        for entry in target.rglob("*"):
            if entry.is_symlink() or entry.is_junction():
                raise ValueError(f"Linked artifact: {entry}")
        shutil.rmtree(target)


def run(command, project, environment, log, timeout=1800):
    print(f"Running {log.name} ...", flush=True)
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            command,
            cwd=project,
            env=environment,
            stdout=output,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    if result.returncode:
        raise RuntimeError(f"{log.name} failed ({result.returncode}). See {log}")


def preflight(compiler):
    if sys.platform != "win32" or sys.version_info[:2] != (3, 13):
        raise RuntimeError("Build requires 64-bit Windows Python 3.13.")
    if sys.maxsize <= 2**32:
        raise RuntimeError("Build requires 64-bit Python.")
    for package in [
        "PyInstaller",
        "PySide6",
        "SQLAlchemy",
        "fastapi",
        "uvicorn",
        "httpx",
        "pytest",
    ]:
        importlib.metadata.version(package)
    if not shutil.which("node"):
        raise RuntimeError(
            "Node.js is required so companion polling tests are not skipped."
        )
    candidates = (
        [compiler]
        if compiler
        else [
            shutil.which("ISCC.exe"),
            r"C:\Program Files\Inno Setup 7\ISCC.exe",
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        ]
    )
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise RuntimeError(
        "Inno Setup compiler not found; pass -Compiler with its full path."
    )


def build(project, compiler):
    compiler = preflight(compiler)
    logs = project / "build/release-logs"
    logs.mkdir(parents=True, exist_ok=True)
    started = time.time()
    environment = os.environ.copy()
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["PYTHONIOENCODING"] = "utf-8"
    with tempfile.TemporaryDirectory(prefix="mro-release-") as temporary:
        isolated = Path(temporary)
        environment["MODELRAILROADOPS_DATA_DIR"] = str(isolated / "tests")
        junit = logs / "pytest.xml"
        run(
            [sys.executable, "-m", "pytest", "-q", f"--junitxml={junit}"],
            project,
            environment,
            logs / "pytest.log",
        )
        suites = list(ET.parse(junit).getroot().iter("testsuite"))
        counts = {
            key: sum(int(s.get(key, 0)) for s in suites)
            for key in ["tests", "failures", "errors", "skipped"]
        }
        if not counts["tests"] or any(
            counts[key] for key in ["failures", "errors", "skipped"]
        ):
            raise RuntimeError(
                f"Release requires a fully passing, unskipped suite: {counts}"
            )
        # Prevent unrelated developer tools (e.g. Poppler/Git) from supplying DLLs.
        windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        environment["PATH"] = os.pathsep.join(str(path) for path in [
            Path(sys.base_prefix) / "DLLs", Path(sys.base_prefix),
            windows / "System32", windows,
        ])
        for relative in ["build/release", "dist/Model Railroad Operations", "release"]:
            clean_owned(project, relative)
        work = project / "build/release"
        work.mkdir(parents=True)
        run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--clean",
                "--noconfirm",
                "--workpath",
                str(work),
                "--distpath",
                str(project / "dist"),
                "ModelRailroadOperations.spec",
            ],
            project,
            environment,
            logs / "pyinstaller.log",
        )
        bundle = project / "dist" / APP
        manifest = audit_bundle(bundle, project)
        verify_root = isolated / "verification"
        verify_root.mkdir()
        (verify_root / ".build-verification").touch()
        environment["MODELRAILROADOPS_DATA_DIR"] = str(verify_root)
        # The frozen runtime must work without Python or development tools on PATH.
        environment["PATH"] = os.pathsep.join([str(windows / "System32"), str(windows)])
        try:
            run(
                [str(bundle / (APP + ".exe")), "--verify-build"],
                project,
                environment,
                logs / "verification.log",
                timeout=180,
            )
        finally:
            # Retain failure diagnostics before TemporaryDirectory removes fixtures.
            if (verify_root / "verification.json").is_file():
                shutil.copy2(verify_root / "verification.json", logs / "verification.json")
        verification = json.loads((verify_root / "verification.json").read_text())
        if verification.get("result") != "passed":
            raise RuntimeError(f"Bundled verification failed: {verification}")
        (logs / "verification.json").write_text(json.dumps(verification, indent=2))
        if audit_bundle(bundle, project) != manifest:
            raise RuntimeError("Bundled verification modified the distribution.")
        staging = work / "installer"
        staging.mkdir()
        run(
            [
                compiler,
                f"/DReleaseOutput={staging}",
                f"/DBundleSource={bundle}",
                str(project / "packaging/installer.iss"),
            ],
            project,
            environment,
            logs / "inno.log",
        )
        installer = staging / INSTALLER
        if not installer.is_file() or installer.stat().st_size < 1_000_000:
            raise RuntimeError("Installer missing or unexpectedly small.")
        release = project / "release"
        release.mkdir()
        final = release / INSTALLER
        shutil.copy2(installer, final)
        checksum = digest(final)
        (release / (INSTALLER + ".sha256")).write_text(
            f"{checksum}  {INSTALLER}\n", encoding="ascii"
        )
        report = {
            "result": "passed",
            "tests": counts,
            "verification": verification,
            "installer": str(final),
            "bytes": final.stat().st_size,
            "sha256": checksum,
            "elapsed_seconds": round(time.time() - started, 2),
            "bundle_files": manifest,
            "dependencies": {
                d.metadata["Name"]: d.version
                for d in importlib.metadata.distributions()
            },
        }
        (release / "release-manifest.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    k: report[k]
                    for k in ["result", "tests", "installer", "bytes", "sha256"]
                },
                indent=2,
            ),
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", default="")
    arguments = parser.parse_args()
    try:
        build(Path(__file__).resolve().parents[1], arguments.compiler)
    except Exception as error:
        print(f"RELEASE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
