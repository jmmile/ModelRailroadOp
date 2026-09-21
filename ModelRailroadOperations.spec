from pathlib import Path
import PySide6
import sys
from PyInstaller.utils.hooks import collect_submodules

root = Path(SPECPATH)
sys.path.insert(0, str(root / "packaging"))
from release_audit import audit_inputs
a = Analysis(
    [str(root / "packaging" / "launcher.py")],
    pathex=[str(root / "src"), str(root / "packaging")],
    binaries=[],
    datas=[(str(root / "src/modelrailroadops/web/static/index.html"), "modelrailroadops/web/static"),
           (str(root / "src/modelrailroadops/resources/application.ico"), "modelrailroadops/resources")],
    hiddenimports=["sqlalchemy.dialects.sqlite", "modelrailroadops.web.server"] + collect_submodules("uvicorn"),
    excludes=["pytest", "ruff", "black", "alembic", "tkinter"],
    noarchive=False,
)
# Qt 6.11 ships a newer compatible MSVC runtime than Python 3.13.
# The process loads root DLLs first, so use Qt's versions consistently there.
qt_directory = Path(PySide6.__file__).parent
# Qt uses Windows' ICU API. A third-party ICU found on the build PATH has
# version-suffixed exports and must not shadow the Windows system DLL.
a.binaries = [entry for entry in a.binaries if Path(entry[0]).name.casefold() not in ("icuuc.dll", "icudt78.dll")]
for dll in ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll"):
    a.binaries = [entry for entry in a.binaries if entry[0].casefold() != dll]
    a.binaries.append((dll, str(qt_directory / dll), "BINARY"))
pyz = PYZ(a.pure)
audit_inputs(a.datas + a.binaries + a.pure + a.scripts, root)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name="Model Railroad Operations",
    icon=str(root / "src/modelrailroadops/resources/application.ico"),
    console=False, debug=False, strip=False, upx=False,
    version=str(root / "packaging" / "version_info.txt"),
)
companion = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name="Model Railroad Companion",
    icon=str(root / "src/modelrailroadops/resources/application.ico"),
    console=True, debug=False, strip=False, upx=False,
    version=str(root / "packaging" / "version_info.txt"),
)
coll = COLLECT(exe, companion, a.binaries, a.datas, strip=False, upx=False,
               name="Model Railroad Operations")
