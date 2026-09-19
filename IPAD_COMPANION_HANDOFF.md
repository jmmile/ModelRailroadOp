# Model Railroad Operations — iPad companion handoff

Prepared September 16, 2026. This is a development plan, not an implemented browser application.

## User and goal

The application is for the owner's Windows desktop and laptop. An iPad will be carried around the model railroad layout. Build a touch-friendly browser companion in Safari, with the Windows computer awake and hosting the railroad data on the same home Wi-Fi. No native iOS application, public hosting, or App Store distribution is required.

The user is conserving coding-agent credits and wants to continue planning and implementation in regular ChatGPT, applying code in Visual Studio Code when direct filesystem tools are unavailable. Provide small, complete, reviewable changes and exact commands. Ask for current source files before modifying code you cannot inspect. Do not claim local edits, tests, or Git operations occurred without evidence.

## Current desktop application

- Python 3.13, PySide6 6.11.1, SQLAlchemy 2.0.51, SQLite.
- Project: `C:\Users\jgmil\Documents\ModelRailroadOps`.
- GitHub: https://github.com/jmmile/ModelRailroadOp
- Latest verified commit: `a17182e` on `main`, pushed previously: dashboard, backups, undo, and industry pickup shortcut.
- Cleanup and EXE packaging changes remain UNCOMMITTED as of this handoff. GitHub does not contain that latest work. Preserve it; do not reset or replace the checkout with GitHub's older version.
- User confirmed the Windows installer worked and their layout backup restored successfully. Physical printing and full laptop acceptance testing have not been confirmed.
- 91 source tests passed. Packaged tests passed all 16 tabs, waybill preview, image loading, ZIP backup/restore, and empty-layout startup. The isolated layout contained 24 cars, 24 waybills, and 25 PNG images at test time; these are not guaranteed current live totals.
- No browser server, browser interface, pairing, or mobile API has been implemented.

Features include freight roster, industries/spots, general locations/tracks, Car Spotting, waybills, operating sessions, switch lists, movement history, passenger operations, dashboard, and backup/restore. Industry capacity uses defined spots; general-track capacity uses its configured car limit. Double-clicking an industry-spot car opens a prefilled pickup waybill or its existing active assignment. General tracks retain their existing waybill workflow.

## Data locations: critical distinction

`src/modelrailroadops/paths.py` defines:

- Source runs: project `data` folder.
- Installed EXE: `%LOCALAPPDATA%\ModelRailroadOperations`.
- `MODELRAILROADOPS_DATA_DIR`: explicit override for either mode, read at import time.

The installed application and source checkout can contain DIFFERENT layouts. A development server must explicitly select the intended data directory before importing database modules. Test against a disposable copy first. The production companion should use the installed application's data directory; do not accidentally open the project's older database.

Manual ZIP backups contain `railroad.db` and `Car_Images/`. Older `.db` backups remain supported. Automatic pre-session backups contain the database only and retain ten files. Restore safety backups are retained. Keep live databases, backups, private images, and personal CSVs out of Git and build packages.

## Verified source entry points

All paths below are relative to the project root.

- `src/modelrailroadops/services/switch_list_service.py`: `SwitchListService.get_generated_moves(operations_session_id, train_id=None)`, `get_switch_list_rows(...)`, and `get_on_train_rows(...)`. Inspect exact row method arguments and fields before use. Generated moves may disappear from a non-completed session's results when their waybill completes; account for this in mobile progress/history.
- `src/modelrailroadops/services/switch_list_move_service.py`: `SwitchListMoveService.can_complete_move(...)`, `complete_move(car_move_id)`, and `return_car_to_pickup(...)`. Inspect full validation and transaction boundaries.
- `complete_move(car_move_id)` returns `(success, message)` and performs movement updates in one transaction. PICKUP starts a PLANNED session, changes its waybill to IN_PROGRESS, moves the car aboard its train, and records history. SETOUT requires pickup, validates the destination, relocates the car, and completes the waybill when appropriate.
- `src/modelrailroadops/services/operations_session_train_service.py`: `get_by_operations_session(...)` retrieves session train assignments.
- `src/modelrailroadops/services/waybill_service.py`: `get_by_id(waybill_id)`, `get_active_for_car(car_id)`, and other business operations.
- `src/modelrailroadops/database/database.py`: shared engine, SessionLocal, schema initialization. Compatibility engine/session modules re-export shared objects.
- `src/modelrailroadops/ui/switch_list/switch_list_widget.py`: current desktop switch-list behavior.
- `src/modelrailroadops/models/`: OperationsSession, OperationsSessionTrain, CarMove, Waybill, Car, Train, Spot, and location models.
- `tests/conftest.py`: isolated SQLite fixture and offscreen Qt fixture.
- `tests/test_operations_session_lifecycle.py`, `tests/test_switch_list_completed_session.py`, `tests/test_waybill_rules.py`: important existing business-rule coverage.

Keep Qt widget/rendering imports out of server request handlers. Browser waybills should be HTML views of service data, not desktop dialogs. Reuse existing business services rather than independently writing car, move, waybill, and session status changes in the web layer.

## Proposed first release

One complete operator workflow:

1. Pair the iPad with the Windows host.
2. Select an operating session, then an assigned train.
3. See ordered pickup/setout instructions in large touch-friendly cards.
4. Open a car's waybill details: reporting marks, number, type, load status, origin, destination, and notes.
5. Confirm pickup or setout; display service validation errors clearly.
6. Refresh progress and cars aboard the train after success.

Initially omit roster editing, layout configuration, new waybill generation, passenger operations, offline edits, internet access, and background synchronization between computers. A disconnected iPad should show its connection state and disable movement completion, not queue commands for later.

## Proposed architecture — not yet chosen or installed

Use a small Python HTTP service (FastAPI/Uvicorn is a candidate) with plain HTML/CSS/JavaScript served from the same origin. Avoid a large frontend build system for this first version. Verify chosen framework documentation and compatible versions when implementation starts.

Browser -> authenticated local API -> existing business services -> same SQLite layout.

Begin read-only on localhost and an isolated layout. After tests pass, add controlled writes and explicitly enable private-network access. Later add a Windows Start/Stop Companion control showing connection address and pairing information. Do not start a network listener silently with the desktop application.

Proposed endpoints:

- `POST /api/pair`: exchange a short-lived pairing code for a session.
- `GET /api/sessions`: selectable operating sessions.
- `GET /api/sessions/{id}/trains`: assigned trains.
- `GET /api/sessions/{id}/trains/{train_id}/moves`: ordered instructions/progress.
- `GET /api/waybills/{id}`: plain data for browser rendering.
- `POST /api/moves/{id}/complete`: validated movement completion.

These are proposals, not existing APIs. Verify session/train/move relationships server-side. GET requests must never mutate operations. Use explicit data objects, not serialized ORM internals.

## Correctness and connection requirements

- Both screens must use the same database and existing destination restrictions.
- Desktop and mobile can act concurrently. Review SQLite write transactions and service behavior before claiming duplicate requests are safe. Disabling a button is insufficient. Repeated taps/retries must never add duplicate movement history or repeat state transitions.
- Re-read the move state inside its transaction; reject stale/wrong-session actions. Design idempotency and conflict handling with tests before enabling writes.
- Pause/stop companion access while restoring a database. Dispose connections and resume only after a successful restore/recovery. Backup/restore and web writes must not overlap unsafely.
- Start with explicit pairing, bounded session lifetime, code retry limits, and no unauthenticated reads or writes. No public port forwarding. Use same-origin request checks/CSRF protection; do not enable wildcard CORS.
- Plain local HTTP does not encrypt pairing or session traffic. Choose and document a trusted-home-network approach versus HTTPS before deployment; do not describe a pairing code as encryption. Cookie settings must match that choice.
- PC must stay awake; both devices need network reachability. Guest Wi-Fi isolation or Windows firewall rules may prevent connection. Restrict any required firewall rule to the private network and chosen port with user authorization.
- Poll modestly while the page is visible; stop polling in the background. Escape all railroad/user text when rendering HTML.

## Incremental implementation order

1. Preserve/commit current desktop cleanup and packaging only when the user authorizes it; exclude generated binaries/data. Capture a fresh ZIP backup.
2. Inspect current service/model files, then create the server skeleton using a disposable data directory. No production data changes.
3. Add read-only session/train/switch-list APIs and a simple iPad page. Test empty state, missing IDs, filtering, ordering, and completed-waybill behavior.
4. Add pairing/authentication and server-side movement completion through existing services. Test duplicate requests, stale states, pickup-before-setout, spot restrictions, capacity, and cancelled/completed sessions.
5. Test desktop/mobile coexistence and restore interlocks. Verify refresh behavior on both screens.
6. Add Start/Stop Companion integration and packaging requirements. Test on the actual iPad over home Wi-Fi.

First coding request for the new chat: inspect the supplied source, implement only the read-only server milestone against a test layout, and provide exact files/commands. Expand to movement writes after verification.

## What to bring into regular ChatGPT

Upload this handoff first. Then supply current copies of the relevant service/model files and tests as requested. GitHub alone is insufficient because packaging/data-path work is not committed. Regular chat may not access the local filesystem, run commands, or edit the repository. Paste actual terminal output for troubleshooting. Do not upload the live database or personal backups unless deliberately needed.

Suggested opening message:

> Continue my Model Railroad Operations iPad browser companion using the attached handoff. The Windows app is installed and my layout restored. Browser development has not started. I will apply changes in Visual Studio Code. Begin with the read-only session/train/switch-list milestone using an isolated layout. First identify which current source files you need, then provide small complete edits and verification commands. Preserve the desktop workflows and do not assume GitHub has my latest uncommitted changes.

## Existing release files

- `ModelRailroadOperations.spec`: folder-based PyInstaller build.
- `packaging/build.ps1`, `packaging/installer.iss`, `packaging/README.md`.
- `requirements-runtime.txt`, `requirements-build.txt`: tested dependency pins.
- `RELEASE_PREPARATION.md`: data transfer and release checks.
- Build tools verified: PyInstaller 6.22.3, hooks 2026.7, Inno Setup 7.1.0.
- Build configuration selects matching Qt runtime DLLs and excludes a conflicting ICU library found on the build machine's PATH. Preserve that correction.
- Installer: `dist/installer/ModelRailroadOperations-Setup-1.0.0.exe`.
- Do not rebuild, install, commit, or push merely because this handoff mentions those actions; follow the user's next request.
