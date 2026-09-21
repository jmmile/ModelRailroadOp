# Windows One-Command Release Build — Implementation and Acceptance Report

## Status

**Complete: the one-command release build passed, the installer and checksum were generated, and the final full pytest run passed.** No commits or pushes were made. The production database and picture collections were not modified. Installation on a clean second computer remains a manual acceptance test.

## Release command

From `C:\Users\jgmil\Documents\ModelRailroadOps`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\build.ps1
```

An alternate Inno Setup path can be supplied with `-Compiler 'C:\path\ISCC.exe'`.
The build computer needs Windows x64, Python 3.13 in the project `.venv`, the
requirements-build.txt and requirements.txt dependencies, Node.js for the
JavaScript regression test, and Inno Setup. The receiving computer does **not**
need Python, Node.js, development tools, or Inno Setup.

## Implemented pipeline

1. Check required build tools before starting.
2. Run the complete pytest suite with a disposable data-directory override;
   require tests to be present and no failures, errors, or skipped tests.
3. Clean only explicitly allowed, resolved artifact directories, rejecting
   symlinks/junctions: `build/release`, `dist/Model Railroad Operations`, and
   `release`. Project roots, source, and user data are not cleanup targets.
4. Build both executables with PyInstaller using an explicit companion HTML
   resource and web-server hidden imports. Retain the existing Qt/MSVC runtime
   compatibility handling. Restrict DLL discovery to the Python installation
   and Windows, removing unrelated developer tools from the search path.
5. Audit source provenance and bundle paths: only approved application source,
   the explicit HTML resource, generated standard-library archive, and trusted
   interpreter/dependency/system inputs are allowed. Reject personal-data
   folders, database/photo/CSV/log/document extensions, and unexpected archives.
6. Inspect both executables' embedded Python archives for the required web and
   picture-management modules. Verify the bundled Python DLL, Windows Qt plugin,
   and companion HTML hash against the current source. Inspect every entry of
   the standard-library ZIP and record bundle file hashes.
7. Run the actual bundled desktop executable with `--verify-build` against a
   new temporary directory containing only the verification marker. A populated
   directory is rejected even if someone adds that marker. Only Windows
   directories remain on PATH during bundled verification.
8. Exercise all desktop tabs, generated JPEG/PNG pictures, both picture editors,
   authenticated companion HTTP on a loopback-only ephemeral port, pairing and
   session retrieval, and ZIP backup/restore of all three picture collections.
9. Re-audit the distribution and require unchanged file hashes after verification.
10. Run Inno Setup into staging. Publish the successful installer under `release`,
    generate its `.sha256` file, and write `release-manifest.json` with test,
    verification, dependency, and file-hash results.

All commands are checked for failure and have timeouts. Installer publication
is not reached after a failing test/build/audit/runtime-verification/compiler
step. Detailed command logs and pytest XML are retained in `build/release-logs`.
Bundled-verifier JSON is also retained on verification failure when available.

If preflight/tests fail, the previous successful release is left intact. Once
the test gate passes, the current release output is cleaned before rebuilding.
Always check the command's success and manifest rather than assuming an old
installer represents a new successful run.

## Packaging and runtime changes

- The companion's `web/static/index.html` is now explicitly bundled.
- FastAPI, Starlette, Pydantic, and Uvicorn runtime versions are declared.
- The desktop executable remains windowed.
- `Model Railroad Companion.exe` is a separate console executable using the
  same bundled application code. Its Start Menu shortcut launches the local
  server on port 8675 and displays the pairing code. Keep that console open
  while using the companion; close it to stop the server.
- Both applications use the existing per-user data-directory architecture.
  Installation does not contain a prepopulated railroad database or photographs.
  On another computer, restore a layout ZIP separately after installation.
- The installer remains per-user, does not require administrator rights, targets
  x64-compatible Windows 10 build 17763+ / Windows 11, and preserves the user data
  folder on uninstall. The release version remains the existing `1.0.0`.

## Files changed for this packaging task

- `packaging/build.ps1` — one-command checked entry point.
- `ModelRailroadOperations.spec` — explicit web resources/imports, audit hook,
  desktop and companion executables.
- `packaging/launcher.py` — packaged desktop/companion dispatch.
- `packaging/verify_build.py` — empty-directory guard plus web, picture, and
  all-collection backup verification.
- `packaging/installer.iss` — staging/output overrides and companion shortcut.
- `packaging/README.md` — build, transfer, operating, and verification instructions.
- `requirements-runtime.txt` — web runtime dependencies.
- `requirements.txt` — required web/test dependencies.
- `.gitignore` — exclude generated release artifacts.
- `tests/test_web_companion_authentication.py` — remove three live-database
  dependencies and use temporary seeded records instead.

Added:

- `packaging/release_build.py` — checked orchestration and artifact publication.
- `packaging/release_audit.py` — input provenance, privacy, and bundle resource audit.
- `tests/test_release_build.py` — release-gate, cleanup, provenance, verifier,
  skipped-test, failure-injection, and checksum-publication regression tests.
- `packaging/RELEASE_BUILD_REPORT.md` — this report.

Earlier uncommitted picture-management changes were preserved and are included
in the built application. Nothing was committed or pushed.

## Development findings

The first test-first build correctly stopped before packaging: three existing
web authentication tests accessed the default database, including a hard-coded
Waybill 26. Those tests now use isolated test fixtures and a seeded waybill ID.
The production database was not used to make the isolated build pass.

The new deny-by-default input audit also initially rejected PyInstaller's own
generated `base_library.zip` and the Python module name `asyncio.log`. The former
now has a precise generated-path allowance and its archive contents are checked;
the latter is validated as a module name, not misclassified as a log-file path.
Regression tests distinguish module entries from data entries and reject
unapproved external files.

The provenance audit also caught an OpenSSL DLL picked up from an unrelated
Poppler tool directory on the developer's PATH. Packaging now uses a controlled
DLL search path so this unrelated runtime cannot enter the installer.

## Final results

### Build and test results

| Gate | Result |
| --- | --- |
| Full pytest inside the successful release build | **194 passed, 2 warnings in 21.78s**; zero failures/errors/skips |
| Clean PyInstaller build | Passed; desktop and companion executables built |
| Input provenance and personal-data checks | Passed; no prohibited data payload found |
| Resource/Python archive audit | Passed; **207 bundled files** hashed |
| Bundled executable verification | Passed with only Windows directories on PATH |
| Desktop tabs | All **16 tabs** loaded in the bundled runtime |
| Pictures | Locomotive/passenger previews, JPEG import, PNG storage passed |
| Web companion | Bundled HTML, actual loopback HTTP, unauthenticated rejection, pairing, authenticated session retrieval passed |
| Backup/restore | All three generated picture collections round-tripped successfully |
| Post-verification distribution audit | Passed; no bundled files changed during verification |
| Inno Setup | Successful compile in **32.687 seconds** |
| Complete successful pipeline | **130.05 seconds** |
| Independent installer SHA-256 check | Matches the generated checksum file |
| Final post-build complete pytest suite | **194 passed, 2 warnings in 21.33s** |
| Whitespace validation | `git diff --check` passed |

Final full-suite command (with a fresh disposable `MODELRAILROADOPS_DATA_DIR`):

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=build/release-logs/final-pytest.xml
```

### Finished artifacts

Installer:

```text
C:\Users\jgmil\Documents\ModelRailroadOps\release\ModelRailroadOperations-Setup-1.0.0.exe
```

Size: **52,997,015 bytes** (approximately **53.0 MB / 50.54 MiB**).

SHA-256, independently confirmed with PowerShell `Get-FileHash`:

```text
b053efc0fedef99f759571a9b15f601eede7c44eb8a24f2c75962b98451dd166
```

Adjacent files:

- `release/ModelRailroadOperations-Setup-1.0.0.exe.sha256`
- `release/release-manifest.json` — dependency versions, installer metadata,
  automated verification, and all 207 bundle file hashes.

Evidence/logs:

- `build/release-logs/pytest.log` and `pytest.xml`
- `build/release-logs/pyinstaller.log`
- `build/release-logs/verification.json` and `verification.log`
- `build/release-logs/inno.log`
- `build/release-logs/final-pytest.xml`

The bundled verification began with an empty database (zero freight cars and
zero waybills) and generated only synthetic verification pictures/records in its
temporary directory. No real-layout Waybill preview was exercised in this empty
fixture; that check remains part of the manual test with a restored test layout.

### Warnings and limitations

- Both full pytest runs reported the existing Starlette HTTPX TestClient
  deprecation and AnyIO `BlockingPortal` alias deprecation.
- PyInstaller reported optional hidden imports unavailable: `tzdata`,
  `pysqlite2`, `MySQLdb`, and `psycopg2`. This application uses bundled Python
  SQLite, not those optional database drivers; SQLite was exercised by the
  packaged verification. IANA timezone database support was not added or tested.
- Git emitted Windows LF/CRLF advisories; no whitespace errors were found.
- The executable/installer is unsigned. No clean-machine install, upgrade,
  uninstall, physical printing, or physical iPad test was claimed as automated.
- This build uses the existing 1.0.0 version identifiers. Future version changes
  must keep the version resource, Inno version/filename, and release filename
  constant consistent, as documented in `packaging/README.md`.

## Remaining manual acceptance tests

Perform installation tests on a second Windows computer or clean Windows VM
without Python. Do not use your production layout for destructive restore tests.

- [ ] Copy the installer and its `.sha256` file to the second computer.
- [ ] Run `Get-FileHash .\ModelRailroadOperations-Setup-1.0.0.exe -Algorithm SHA256`
  and compare it with the checksum file. PASS: exact hash match.
- [ ] Run the installer as a normal user. PASS: installation completes without
  requiring a Python installation or administrator credentials.
- [ ] Confirm Start Menu shortcuts for Model Railroad Operations and Model
  Railroad Companion; confirm the optional desktop shortcut if selected.
- [ ] Launch the desktop application. PASS: it opens an empty layout with no
  developer/user records or photographs from the build computer.
- [ ] Open all tabs; check text, sizing, icons, and dialogs on the target display.
- [ ] Add a disposable locomotive with a JPG picture and passenger car with a PNG
  picture. Save/reopen, change, cancel, rename, and remove as described in the
  combined picture-management report. PASS: both editors work without Python.
- [ ] Restore a test layout ZIP containing freight, locomotive, and passenger
  pictures. PASS: records and all picture collections appear correctly.
- [ ] Create a new ZIP and restore it in an isolated test layout. PASS: safety
  backup is created and the database/pictures round-trip correctly.
- [ ] Launch the companion Start Menu shortcut. PASS: its console shows a pairing
  code and the correct per-user database path, and port 8675 is available.
- [ ] Allow firewall access only on the intended private network if prompted.
  Pair an iPad/browser and verify sessions, trains, Waybill details, and two-device
  pickup/set-out synchronization. Do not expose the server to the Internet.
- [ ] Close the companion console. PASS: the server stops cleanly; restarting it
  provides a new pairing code without losing layout data.
- [ ] Check physical printing / Print Preview and JPEG support on the target.
- [ ] With a backup available, close both applications and test installing over
  the previous version. PASS: upgrade succeeds and runtime data is preserved.
- [ ] Test uninstall on the disposable target. PASS: application files/shortcuts
  are removed, while the per-user layout data remains available.

The installer is unsigned; Windows SmartScreen/antivirus may display warnings.
The checksum detects transfer corruption, not publisher identity. The automated
audit is an allowlist/provenance/resource check, not a forensic personal-content
classifier for arbitrary source-code changes or compromised dependencies.

Manual acceptance result: **NOT RUN / PASS / FAIL / PARTIAL**

Tester / Windows version / date / notes:
