# Desktop companion startup

## Behavior

The desktop starts its companion automatically by default. Dashboard → iPad / Web Companion provides Start, Stop, a saved automatic-start checkbox, running status, LAN address candidates, and the current pairing code. The checkbox affects the next launch; use Stop to stop the current server.

The server runs in a background thread without a console. Closing the desktop waits for its own server to finish shutting down. A separately launched companion is never terminated: if port 8675 is occupied or unavailable, the dashboard reports this and allows a retry. It does not retrieve another server's pairing code or assume that server uses the same database.

Each successful start generates new pairing credentials; browsers must pair again after a restart. Settings are stored in desktop-settings.ini within the active application data directory, not in the database. No schema changes. Backup restore is blocked while the desktop-owned server is running; separately launched companions must be closed manually before restore.

## Files changed for this feature

- src/modelrailroadops/services/companion_controller.py (new): exclusive port ownership, background Uvicorn lifecycle, status and pairing information.
- src/modelrailroadops/ui/widgets/companion_panel.py (new): dashboard controls and saved preference.
- src/modelrailroadops/ui/widgets/dashboard_widget.py: embeds the panel.
- src/modelrailroadops/ui/main_window.py: graceful close and restore guard.
- src/modelrailroadops/__main__.py: invokes automatic start during normal desktop launch.
- tests/test_companion_controller.py (new): real local HTTP lifecycle, duplicate start, occupied port, restart credentials, immediate stop, preference persistence, UI state, startup failure.
- tests/test_database_override_warning.py: simulated startup window updated; asserts automatic-start invocation.
- packaging/release_audit.py: requires the new modules in both packaged executables.
- packaging/verify_build.py: verifies packaged background startup and shutdown using a temporary database and ephemeral port.
- packaging/README.md: updated desktop and standalone companion instructions.
- COMPANION_STARTUP_TEST_REPORT.md: this report.

## Manual acceptance checklist

Automated suite: **208 passed, 2 warnings in 24.77 seconds**. Warnings are the existing Starlette/HTTPX and AnyIO deprecations. An initial diagnostic run was interrupted to update the existing startup-window test double for the new startup call; the subsequent complete suite passed.

- [ ] Close existing desktop and companion programs. Install the rebuilt installer, then open Model Railroad Operations.
- [ ] Dashboard shows Running and a six-digit pairing code without opening a companion console.
- [ ] On an iPad on the same private network, enter one of the displayed http:// addresses in Safari. Pair with the displayed code. Confirm the expected layout/session data appears.
- [ ] If Windows asks, allow private-network access only. Do not forward port 8675 on your router. Multiple addresses may appear with VPNs or multiple network adapters; select the home-network address.
- [ ] Click Stop. Dashboard reaches Stopped; iPad requests no longer reach this server. Cached page content may remain visible.
- [ ] Click Start. Dashboard reaches Running. Reload the iPad page and pair again with the current code.
- [ ] Uncheck automatic startup, close and reopen the desktop. Dashboard stays Stopped. Click Start to confirm manual operation still works.
- [ ] Recheck automatic startup, close and reopen. Companion starts again.
- [ ] Close desktop while Running. Reopen it and confirm the port is available and it starts successfully.
- [ ] Close desktop. Launch the separate Model Railroad Companion shortcut, then launch desktop. Dashboard reports the unavailable port. The separate companion continues working and supplies its own pairing code in its console.
- [ ] Close the separate companion console and click Start on Dashboard. Desktop companion starts successfully.
- [ ] While desktop companion is Running, select Restore Database. A Stop Companion First message appears before any restore selection or database changes.
- [ ] Verify the dashboard remains usable at your normal window size and display scaling.

## Release build results

- Complete test-first release build passed: 208 tests, no failures, errors, or skips.
- PyInstaller resource/privacy audits passed. Packaged runtime passed all 16 tabs, picture editors/codecs, authenticated HTTP pairing/session requests, desktop-owned companion startup/shutdown, and all-picture backup/restore.
- Inno Setup installer compilation passed.
- Installer: `C:\Users\jgmil\Documents\ModelRailroadOps\release\ModelRailroadOperations-Setup-1.0.0.exe`
- Size: **53,019,810 bytes**.
- SHA-256: `cce65c2d7efe1169b656370a40d401393b8a5feedffb11f8c77260a57ffee01f`
- Adjacent `.exe.sha256` and `release-manifest.json` contain checksum/provenance information. Logs: `build/release-logs`.
- This installer includes the earlier locomotive/passenger selected-row picture previews as well as the new companion controls. It has been built, not installed on the user's computer.

## Remaining manual checks

Firewall permissions, iPad connectivity, installation on another PC, and visual layout require the physical checks above. The installer is unsigned. The server uses the existing HTTP/private-LAN pairing design, not public-internet hosting. LAN address candidates are calculated at startup; stop/start after changing network adapters. A companion started outside the desktop remains independently managed.

No production database or picture collections were modified. No commit or push was performed.
