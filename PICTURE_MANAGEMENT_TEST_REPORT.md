# Picture Management — Combined Implementation and Acceptance Test Report

This is the single current report for **locomotive picture editing, passenger-car picture editing, and unified car/locomotive/passenger picture backup and restore**. It supersedes the earlier locomotive-only report. Physical desktop acceptance testing is still required.

## 1. Delivered functionality

- **Motive Power → Add/Edit Locomotive:** preview, Add Picture, Change Picture, and Remove Picture.
- **Passenger Equipment → Add/Edit Passenger Car:** the same picture controls, with passenger fields preserved.
- Both editors accept PNG, JPG, and JPEG, validate the selected file, and show an aspect-ratio-preserving preview bounded to 400 × 150 pixels.
- Picture selection/removal stays in memory until Save. Cancel leaves existing pictures unchanged and does not create an orphan picture for a canceled new record.
- Reporting-mark/number changes move the associated picture safely. Occupied target filenames, ambiguous multiple files, and normalized identity collisions are rejected instead of silently overwriting another picture.
- **File → Backup Database…** creates one ZIP with the database and all three managed picture collections. **File → Restore Database…** restores the included collections and creates a safety ZIP first.
- Freight car picture behavior and Waybill rendering were not redesigned. Passenger/locomotive pictures are not added to the iPad companion, Operations Session displays, or printed operator sheets.
- No schema migration, EXE rebuild, commit, or push was performed. Existing companion synchronization was preserved.

## 2. Files changed and added

All paths are relative to `C:\Users\jgmil\Documents\ModelRailroadOps`. This inventory covers the combined, still-uncommitted picture feature work.

Changed tracked files:

| File | Purpose |
| --- | --- |
| `src/modelrailroadops/services/locomotive_service.py` | Coordinate locomotive saves with reversible picture changes and identity checks. |
| `src/modelrailroadops/services/passenger_car_service.py` | Equivalent passenger-car save and identity protection. |
| `src/modelrailroadops/services/database_backup_service.py` | Include all image collections; legacy compatibility, restore rollback, and archive path checks. |
| `src/modelrailroadops/ui/dialogs/add_locomotive_dialog.py` | Locomotive picture preview/selection/removal and error display. |
| `src/modelrailroadops/ui/dialogs/add_passenger_car_dialog.py` | Passenger picture preview/selection/removal and error display. |
| `src/modelrailroadops/ui/main_window.py` | Updated backup/restore explanatory messages. |
| `src/modelrailroadops/ui/widgets/dashboard_widget.py` | Clarifies manual ZIP versus automatic database-only backups. |
| `tests/test_database_backup_service.py` | Multi-collection round trips, safety copies, empty/legacy collections, restore failure, and unsafe paths. |

Added files:

| File | Purpose |
| --- | --- |
| `src/modelrailroadops/services/image_storage.py` | Shared registry of the three managed image folders. |
| `src/modelrailroadops/services/locomotive_image_service.py` | Shared equipment-image validation, naming, discovery, and reversible file operations; locomotive defaults preserve the original API. |
| `src/modelrailroadops/services/passenger_image_service.py` | Passenger-specific configuration of that shared implementation. |
| `tests/test_locomotive_images.py` | Locomotive storage, save/cancel, failure recovery, path, and editor tests. |
| `tests/test_passenger_images.py` | Passenger equivalents plus same-identity collection isolation and real-picture unified backup/restore. |
| `LOCOMOTIVE_IMAGE_TEST_REPORT.md` | Earlier report, retained and marked superseded. |
| `PICTURE_MANAGEMENT_TEST_REPORT.md` | This consolidated report. |

Existing handoff documents and the untracked `data/` directory were not incorporated into the change. Automated tests used isolated temporary data, not the user's production database or photographs.

## 3. Storage, identity, and save behavior

| Collection | Directory under the active data root | Example |
| --- | --- | --- |
| Existing freight car pictures | `Car_Images` | Existing naming remains unchanged. |
| Locomotive pictures | `Locomotive_Images` | `L_UP_1996.png` |
| Passenger pictures | `Passenger_Images` | `P_GN_A1.png` |

The active root follows `modelrailroadops.paths.DATA_DIRECTORY`. Normally source runs use the project's `data` directory; packaged runs use `%LOCALAPPDATA%\ModelRailroadOperations`. A `MODELRAILROADOPS_DATA_DIR` override takes precedence. No editor hard-codes the source data directory.

Locomotive and passenger names trim outer spaces and uppercase reporting marks/numbers. Characters other than A–Z, digits, and hyphens are escaped as UTF-8 `%XX` sequences. This includes underscores inside either identity component, preventing separator ambiguity. Prefixes avoid reserved Windows device names.

Selected PNG/JPG/JPEG files are decoded and stored as PNG; the original file is never modified or deleted. Existing managed names with `.png`, `.jpg`, `.jpeg`, or uppercase equivalents can be found. Arbitrary manual filenames are not automatically associated.

A locomotive and passenger car may share a reporting mark/number because their directories and prefixes differ. Within either roster, identities that normalize to the same picture key are rejected to prevent ambiguous ownership.

On Save, picture changes occur around the database commit. Ordinary write/commit failures trigger rollback. On Cancel, no permanent picture operation occurs. Remove Picture only removes the managed copy after a successful Save. Rename changes the managed filename while preserving the image; changing a passenger car's descriptive Name does not change its picture identity.

## 4. Unified backup and restore

- Manual layout ZIPs contain `railroad.db`, `Car_Images/`, `Locomotive_Images/`, and `Passenger_Images/`.
- Explicit empty-folder entries allow a new ZIP to restore an intentionally empty picture collection.
- Older car-only ZIPs preserve locomotive/passenger image collections they do not contain, rather than silently deleting them. Their database still replaces the current database, so some preserved image files may not match records in that older database.
- Restore stages and validates the archive, creates a full safety ZIP, and replaces the database and included picture collections. It attempts to recover the previous database/folders if an installation step fails.
- Unsafe archive paths and linked image paths are rejected. The restore-failure test verifies rollback after the car collection is replaced but locomotive installation fails.
- **Automatic session backups and `.db` backups remain database-only. Use a manual ZIP for pictures.**
- Use the updated application to restore new multi-collection archives; older versions may reject their additional folders.

## 5. Automated results

### Final focused run

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_passenger_images.py tests/test_locomotive_images.py tests/test_database_backup_service.py tests/test_packaging_cleanup.py tests/test_presentation_output.py tests/test_operations_sessions_completed_passenger.py tests/test_switch_list_completed_session.py -q
```

**Exact result: `84 passed in 18.22s`**

Coverage includes:

- Supported formats, picture discovery, no-image behavior, source-file preservation and independence.
- Import, replacement, rename, removal, duplicate/case/file collisions, and separate locomotive/passenger identity spaces.
- Canceled Add/Edit/Remove operations, editor Save/reopen, aspect ratio, and normal roster fields.
- Database-commit rollback for add/replace/rename/remove and simulated picture-write failure.
- Runtime override and packaged path behavior.
- Unified ZIP round trips, legacy archives, empty collections, safety backups, restore rollback, and unsafe archive paths.
- A round trip using actual generated freight, locomotive, and passenger image files and a temporary application database.
- Existing presentation, passenger operations, completed-session, and packaging regressions.

### Complete regression suite

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

**Exact result: `168 passed, 2 warnings in 29.45s`**

The two warnings are unchanged web-library deprecations:

1. Starlette TestClient's use of HTTPX is deprecated.
2. AnyIO's `anyio.abc.BlockingPortal` alias is deprecated.

Formatting used Python 3.13 as the explicit target for the passenger additions. `git diff --check` found no whitespace errors; Git emitted its normal Windows LF/CRLF advisories. These automated results do not replace physical desktop testing.

## 6. Safe manual test preparation

- [ ] Have two visibly different test photographs available, using JPG and PNG; a JPEG-extension file is useful for an additional format check.
- [ ] Close the normal application so the test instance cannot be confused with it.
- [ ] Use the updated source application. An older installed EXE does not contain these changes.
- [ ] Prefer a separate test data directory, especially for restore tests.

To start a fresh isolated test instance, open a **new PowerShell window** and run:

```powershell
Set-Location 'C:\Users\jgmil\Documents\ModelRailroadOps'
$env:MODELRAILROADOPS_DATA_DIR = Join-Path $env:TEMP ('ModelRailroadOps-PictureTests-' + [guid]::NewGuid().ToString('N'))
Write-Output $env:MODELRAILROADOPS_DATA_DIR
.\.venv\Scripts\python.exe .\main.py
```

- [ ] Record the printed test directory. The image folders used below will be inside it.
- [ ] Confirm the **Database Override Active** warning points to that test directory, not the normal database.
- [ ] If needed, restore a known layout backup into this isolated instance to obtain freight cars/Waybills with existing pictures. Confirm the override path before restoring.
- [ ] Keep test ZIPs in a separate folder, outside the managed picture folders.

Close this PowerShell window after testing; its override does not change future launches from other windows. Do not copy test data over the production database.

### Test record

- Date/tester:
- Test data directory:
- Locomotive test identity (suggestion: TEST / L1):
- Passenger test identity (suggestion: TEST / P1):
- Original picture:
- Replacement picture:
- Backup ZIP:

## 7. Editor acceptance cycle — run once for each roster

Run Tests A–F first in **Motive Power → Add/Edit Locomotive**, then in **Passenger Equipment → Add/Edit Passenger Car**. Use different record identities unless deliberately testing collection isolation.

### A. Add, save, and reopen

- [ ] Start a new record and enter a unique reporting mark/number plus the ordinary fields you want to verify.
- [ ] Confirm **No Image Available** and disabled **Remove Picture**.
- [ ] Click **Add Picture**, select a JPG photograph, and confirm the correct preview appears without stretching.
- [ ] Confirm **Change Picture** and enabled **Remove Picture** are now shown.
- [ ] Save, reopen the same record, and confirm its picture remains.
- [ ] Verify ordinary fields remain correct: locomotive model/type/horsepower or passenger name/type/length, plus status and notes as applicable.

**PASS:** Correct picture and fields persist; the preview is not distorted. **FAIL:** Missing/wrong picture, unexpected field changes, error, or distorted preview.

- [ ] Locomotive PASS — notes:
- [ ] Passenger PASS — notes:

### B. Replace and cancel replacement

- [ ] Choose **Change Picture**, select the visibly different PNG, and Save.
- [ ] Reopen and confirm the replacement appears.
- [ ] Choose the original picture again, but click **Cancel** on the editor instead of Save.
- [ ] Reopen and verify the last saved replacement still appears.
- [ ] Check that both source photographs still exist and are unchanged.

**PASS:** Save changes the managed picture; Cancel does not; source files are untouched. **FAIL:** A canceled replacement persists or a source file is modified/deleted.

- [ ] Locomotive PASS — notes:
- [ ] Passenger PASS — notes:

### C. Cancel new record and cancel removal

- [ ] Start another unique record, select a picture, and Cancel the editor.
- [ ] Verify that record was not added and no image with its managed filename was created.
- [ ] Edit the previously saved pictured record and click **Remove Picture**.
- [ ] Verify the preview shows **No Image Available**.
- [ ] Cancel, reopen, and verify its saved picture is still present.

**PASS:** Neither canceled action changes persistent data or pictures. **FAIL:** An orphan managed picture appears or a canceled removal deletes the saved image.

- [ ] Locomotive PASS — notes:
- [ ] Passenger PASS — notes:

### D. Rename and collision protection

- [ ] Change the pictured record's number to a unique value, Save, and reopen.
- [ ] Verify its picture follows the new number.
- [ ] Change the reporting mark to a unique value, Save, and reopen; verify the picture again.
- [ ] Check its folder: the old managed name should be gone and the new identity's file should exist.
- [ ] Create a second record in the same roster with a different picture.
- [ ] Try changing the first record's identity to exactly match the second, then Save.
- [ ] Verify an error appears and the dialog remains open. Cancel and verify both records/pictures are unchanged.

**PASS:** Pictures follow valid renames; collisions are rejected without overwriting. **FAIL:** Orphaned/wrong picture, silent overwrite, or incorrect record changes.

- [ ] Locomotive PASS — notes:
- [ ] Passenger PASS — notes:

Optional occupied-file check, isolated data only: place a disposable image named `L_TEST_BLOCKED.png` in Locomotive_Images or `P_TEST_BLOCKED.png` in Passenger_Images without creating that record. Try renaming a pictured record in the corresponding roster to TEST / BLOCKED. Save must display a picture-collision error and preserve both files. Cancel and remove only your disposable collision-test file afterward.

### E. Invalid picture and normal no-picture behavior

- [ ] Cancel the file chooser without selecting anything; verify the preview is unchanged.
- [ ] Optionally select a disposable invalid file with a `.jpg` extension; verify a useful error and unchanged preview.
- [ ] Add another record without selecting a picture, Save, and reopen without errors.
- [ ] Change an ordinary field on that no-picture record and verify Save still works.

**PASS:** Invalid/canceled selection does not damage the prior picture; no-picture records work normally. **FAIL:** An invalid picture is saved, a prior picture is lost, or normal editing fails.

- [ ] Locomotive PASS — notes:
- [ ] Passenger PASS — notes:

### F. Saved removal

- [ ] On a disposable pictured record, click **Remove Picture**, then **Save**.
- [ ] Reopen and verify **No Image Available** and disabled **Remove Picture**.
- [ ] Confirm its managed file is gone and its original source photograph remains.
- [ ] Before the backup test, ensure at least one other pictured record remains in each roster, or add pictures again.

**PASS:** Only the managed picture is removed; the equipment record and source photograph remain. **FAIL:** The picture returns after reopening or unrelated files/records are removed.

- [ ] Locomotive PASS — notes:
- [ ] Passenger PASS — notes:

## 8. Separate collections with the same identity

- [ ] In the isolated test layout, create a locomotive and passenger car with the same reporting mark/number (for example TEST / SAME).
- [ ] Give each a visibly different picture and Save.
- [ ] Reopen each editor and verify it shows its own picture.
- [ ] Replace or remove the passenger picture and Save.
- [ ] Reopen the locomotive and verify its picture is unaffected.

**PASS:** Pictures remain independent across the two rosters. **FAIL:** One roster displays or changes the other roster's picture.

- [ ] PASS — notes:

## 9. One ZIP backup/restore round trip

**Use the isolated test instance: restoring intentionally replaces database records and included image collections.**

- [ ] Have a freight car with a working Waybill picture, a pictured locomotive, and a pictured passenger car.
- [ ] Record which picture each displays. Close any open editors.
- [ ] Choose **File → Backup Database…** and save `picture-test-before.zip` outside the picture folders.
- [ ] Inspect the ZIP in File Explorer: verify `railroad.db`, `Car_Images/`, `Locomotive_Images/`, and `Passenger_Images/`, with the expected files.
- [ ] Change the test locomotive's picture and Save.
- [ ] Change or remove the test passenger car's picture and Save.
- [ ] Reopen both to confirm the changed state before restoring. Close the editors.
- [ ] Choose **File → Restore Database…**, select `picture-test-before.zip`, read the warning, and confirm.
- [ ] Verify successful restore and note the safety-backup path.
- [ ] Reopen the locomotive: its pre-backup picture must be restored.
- [ ] Reopen the passenger car: its pre-backup picture must be restored.
- [ ] Open the freight car's Waybill preview: its original picture must still work.
- [ ] Inspect the safety ZIP: it must contain the picture collections as they existed immediately before restore, including your changed locomotive picture.

**PASS:** One ZIP restores all three picture collections with the database, and the safety ZIP preserves pre-restore state. **FAIL:** Missing/wrong pictures, broken freight image rendering, restore failure, or missing safety backup. If no freight picture was available, mark that part NOT TESTED rather than PASS.

- [ ] PASS — notes:

## 10. Optional legacy and empty-collection checks

- [ ] Save a new ZIP while one picture collection is empty. Add a picture to that collection, then restore the ZIP. The collection should become empty again; the safety ZIP should preserve the newly added picture.
- [ ] Restore an older car-only ZIP in the isolated layout. Verify locomotive/passenger files remain on disk when those folders are absent from the archive. The restored database may not contain records corresponding to all retained pictures.

**PASS:** New empty collections restore faithfully; legacy omission does not silently erase newer collections. **FAIL:** Empty collections are not restored correctly or older ZIPs delete omitted newer collections.

- [ ] PASS / NOT RUN — notes:

## 11. Limits and operating cautions

- One picture per locomotive/passenger car; no cropping, gallery, online lookup, companion display, or printed-sheet picture changes were added.
- Ordinary exceptions trigger rollback, but database/filesystem operations are not a single power-loss-proof transaction. Keep backups; avoid simultaneous desktop editors or manual picture-folder edits during Save/Restore.
- Deleting an entire equipment record still does not automatically delete its picture. If desired, Remove Picture and Save before deleting the record. Retained images block silent reuse of their managed filenames.
- `.db`/automatic session backups do not include pictures. New multi-collection ZIPs should be restored with the updated application.
- No EXE/installer rebuild was performed. Test from source now; rebuild later for installed copies.
- Physical Windows interaction and visual acceptance remain unverified until you complete this checklist. Qt tests verify preview sizing and behavior but are not a substitute for your normal desktop checks.

## 12. Final acceptance record

- [ ] Locomotive tests A–F passed.
- [ ] Passenger tests A–F passed.
- [ ] Same-identity collection-isolation test passed.
- [ ] Unified ZIP restore and safety backup passed.
- [ ] Existing freight Waybill pictures remain correct.
- [ ] No unexpected errors, changed equipment fields, or overwritten source photographs.

Overall result: **PASS / FAIL / PARTIAL / NOT RUN**

For any failure, record the section, roster, reporting mark/number, active test data directory, exact action, expected/actual result, and error text or screenshot. Do not repeat a destructive restore on the normal database to investigate a test failure.
