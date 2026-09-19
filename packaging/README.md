# Windows build

Build on 64-bit Windows with Python 3.13 and the project virtual environment.
Install pinned tools with `.venv\Scripts\python.exe -m pip install -r requirements-build.txt`.
Run `powershell -File packaging\build.ps1` from the project. Pass `-Compiler`
if Inno Setup's ISCC.exe is installed elsewhere.

Outputs:

- `dist/Model Railroad Operations/Model Railroad Operations.exe`
- `dist/installer/ModelRailroadOperations-Setup-1.0.0.exe`

Keep the entire application folder together when testing the unpackaged EXE.
The installer contains supporting files and creates a Start Menu shortcut.
Desktop shortcut creation is optional. Installation requires no administrator
rights and does not include personal railroad data. It installs only for the
current Windows user. It does not delete `%LOCALAPPDATA%/ModelRailroadOperations`
when uninstalled. Close the application before installing updates.

## First use on desktop or laptop

1. Create a complete ZIP backup using the existing source application.
2. Run the setup program and launch Model Railroad Operations from Start.
3. The installed app initially opens an empty layout in its own data folder.
4. Choose File > Restore Database and select the ZIP to transfer the layout
   and car pictures. Verify the counts and images before operating.
5. When switching computers, close the old session, transfer a fresh ZIP,
   and restore it on the other computer. The copies do not synchronize.

The build is unsigned and uses the default executable icon. Physical printing,
laptop installation, and upgrade behavior need acceptance testing on the devices.

## Packaged verification

`--verify-build` runs only when `MODELRAILROADOPS_DATA_DIR` names an isolated
directory containing a `.build-verification` marker. It creates/updates a test
database, loads all tabs, renders screenshots, and tests ZIP backup/restore.
Never point it at a working layout. Its result is `verification.json` in the
test directory. Set `QT_QPA_PLATFORM=offscreen` for headless verification.
