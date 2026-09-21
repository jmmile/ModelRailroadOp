# One-command Windows release build

Build on 64-bit Windows with Python 3.13 and the project virtual environment.
Install build/runtime tools with `.venv\Scripts\python.exe -m pip install -r requirements-build.txt -r requirements.txt`.
The build computer also needs Node.js (for the companion JavaScript tests) and
Inno Setup 7 or 6. The receiving computer needs none of these tools or Python.

Run from the project:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\build.ps1
```

Pass `-Compiler 'C:\path\to\ISCC.exe'` when Inno Setup is installed elsewhere.
The script can also be invoked by absolute path from another directory.

The command performs these gates, stopping on any failure:

1. Check build prerequisites.
2. Run the complete pytest suite with a temporary data-directory override;
   require nonzero test count, zero failures/errors, and zero skipped tests.
3. Clean only the validated `build/release`, `dist/Model Railroad Operations`,
   and `release` artifact directories. Do not put personal files there.
4. Build current desktop and companion executables with PyInstaller.
   The build DLL search path is limited to the Python installation and Windows;
   unrelated tools on the developer's PATH cannot supply runtime DLLs.
5. Audit bundle inputs and output: explicit project-resource allowlist,
   forbidden personal-data paths/extensions, embedded modules, Python/Qt
   runtime, companion HTML source hash, and standard-library ZIP contents.
6. Run the bundled `--verify-build` in a fresh marker-protected temporary
   directory. Exercise tabs, image codecs and editors, authenticated companion
   HTTP on an ephemeral loopback port, and all-picture ZIP backup/restore.
   Verification runs with only Windows directories on PATH, not Python/dev tools.
7. Re-audit the distribution to ensure verification did not modify it.
8. Compile Inno Setup in staging, then publish the installer, SHA-256 file,
   and dependency/file-hash manifest only after successful verification/build.

Logs and pytest XML: `build/release-logs/`. Generated test data/screenshots
stay in disposable temporary directories, not the installer.

Outputs:

- `dist/Model Railroad Operations/Model Railroad Operations.exe`
- `dist/Model Railroad Operations/Model Railroad Companion.exe`
- `release/ModelRailroadOperations-Setup-1.0.0.exe`
- `release/ModelRailroadOperations-Setup-1.0.0.exe.sha256`
- `release/release-manifest.json`

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
   and all managed pictures. Verify the counts and images before operating.
5. When switching computers, close the old session, transfer a fresh ZIP,
   and restore it on the other computer. The copies do not synchronize.

The build is unsigned and uses the approved concept C locomotive icon. Physical printing,
laptop installation without Python, SmartScreen behavior, and upgrades need
acceptance testing on the devices. The target is x64-compatible Windows 10
(build 17763+) or Windows 11. Copy the installer, not just the desktop EXE.

The desktop starts its companion automatically on port 8675. Dashboard →
iPad / Web Companion shows its status, pairing code, and network addresses,
plus Start/Stop controls and a saved automatic-start preference. Closing the
desktop stops the server it started. Stop it before restoring a backup.

Alternatively, launch **Model Railroad Companion** from the Start Menu to run
independently. Keep its console open while using the iPad; it supplies its own
pairing code. An occupied port prevents a duplicate desktop server; the desktop
does not stop an independent server. Both use the same per-user data directory.
Allow Windows Firewall access only for the intended private local network;
do not port-forward it. Close both programs before installing an update, and
close any independent companion before restoring a layout.

Verify the transferred installer with:

```powershell
Get-FileHash .\ModelRailroadOperations-Setup-1.0.0.exe -Algorithm SHA256
```

Compare to the adjacent `.sha256` file. Hashes detect changed/corrupt files;
they are not a code signature or proof of publisher identity.

## Packaged verification

`--verify-build` runs only when `MODELRAILROADOPS_DATA_DIR` names an isolated
directory containing only a `.build-verification` marker. A populated directory
is rejected even if it has that marker. It creates a test database, loads all
tabs, exercises the web server and picture editors, renders a screenshot,
and tests ZIP backup/restore. Never point it at a working layout.
Its result is `verification.json` in the
test directory. Set `QT_QPA_PLATFORM=offscreen` for headless verification.

## Privacy and release limits

Only Python source under the application package and the explicit companion
HTML page are approved project inputs. No user database, ZIP backup, photograph,
CSV, test-data directory, or report is an approved application resource.
Third-party runtime dependencies are collected by PyInstaller, not by copying
the project or data tree. Runtime images are user data and are imported/restored
after installation. No build step opens the production database.

The audit is a deterministic allowlist/path/extension/archive check, not a
forensic personal-information classifier for arbitrarily modified source or
third-party libraries. Build only from reviewed code and trusted dependencies.
Version 1.0.0 remains the existing version; update the spec version resource,
installer version/name, and release filename constant together for a new version.
