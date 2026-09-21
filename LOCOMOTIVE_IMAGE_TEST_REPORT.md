# Locomotive Pictures and Unified Picture Backup — Implementation and Acceptance Tests

> Historical report. Passenger picture editing has now been added. Use [PICTURE_MANAGEMENT_TEST_REPORT.md](PICTURE_MANAGEMENT_TEST_REPORT.md) for the consolidated implementation summary, latest results, and complete manual acceptance cycle.

## Delivered

The desktop Add/Edit Locomotive dialog now includes a bounded, aspect-ratio-preserving preview, Add/Change Picture, and Remove Picture. PNG, JPG, and JPEG files are validated and copied into application-managed storage when Save succeeds. Cancel does not apply picture changes. No database migration was needed.

The existing File → Backup Database utility now makes one layout ZIP containing the database and all registered picture collections. File → Restore Database restores those collections, with a complete safety ZIP created first. Passenger-picture storage is registered for the next feature; passenger-picture editing/display has not been implemented.

No commits or pushes were made. The existing companion synchronization at checkpoint `251c768` was left untouched. Tests used temporary databases and generated temporary pictures, not the user's normal railroad database or image collections.

## Files

All paths below are relative to `C:\Users\jgmil\Documents\ModelRailroadOps`.

Changed:

- `src/modelrailroadops/services/locomotive_service.py`
- `src/modelrailroadops/services/database_backup_service.py`
- `src/modelrailroadops/ui/dialogs/add_locomotive_dialog.py`
- `src/modelrailroadops/ui/main_window.py`
- `src/modelrailroadops/ui/widgets/dashboard_widget.py`
- `tests/test_database_backup_service.py`

Added:

- `src/modelrailroadops/services/locomotive_image_service.py`
- `src/modelrailroadops/services/image_storage.py`
- `tests/test_locomotive_images.py`
- `LOCOMOTIVE_IMAGE_TEST_REPORT.md` (this report)

Existing handoff documents and untracked data were not added or changed by this work.

## Storage and safeguards

- Pictures are stored under `DATA_DIRECTORY / "Locomotive_Images"`.
- Typical source-run location: `C:\Users\jgmil\Documents\ModelRailroadOps\data\Locomotive_Images`.
- Packaged application location follows the existing runtime path rules, normally `%LOCALAPPDATA%\ModelRailroadOperations\Locomotive_Images`.
- `MODELRAILROADOPS_DATA_DIR` overrides the data root, including the image directory.
- Example managed filename: `L_UP_1996.png`.
- Naming trims outer spaces and uppercases the reporting mark and number. Other than letters, digits, and hyphens, UTF-8 bytes are escaped as `%XX`. Underscores inside values are escaped, so they cannot be confused with the separator. The `L_` prefix prevents Windows reserved-name problems.
- Selected PNG/JPG/JPEG files are decoded and stored as PNG. Existing managed filenames with PNG/JPG/JPEG extensions are discoverable, including uppercase extensions. Manually named files must follow the managed naming convention; arbitrary filenames are not automatically matched.
- Add/Change stages decoded picture data in memory. The original source photograph is never deleted or modified, and there is no ongoing dependency on its location after import.
- Save wraps picture changes around the database commit. Ordinary file/database failures roll back the associated changes; database-failure rollback is tested for add, replace, rename, and remove.
- Renaming the reporting mark/number moves the existing picture to its new managed name. Occupied target names and ambiguous multiple-image matches cause an error rather than silent overwrite.
- Locomotive identities that differ only by case or normalize to the same picture key are rejected as ambiguous, even though the existing SQLite uniqueness constraint may distinguish them.
- Remove Picture is staged until Save. Cancel preserves the original managed file. Remove deletes only the application's managed copy, not the source photograph.
- Existing Car_Images lookup and Waybill rendering code were not changed.

## One backup utility for picture collections

The shared registry in `image_storage.py` contains:

1. `Car_Images`
2. `Locomotive_Images`
3. `Passenger_Images` — reserved for future passenger-picture management

New layout ZIPs include explicit entries for each collection, even when empty. Thus restoring a new backup accurately restores an intentionally empty collection. Legacy ZIPs lacking locomotive/passenger collections leave those newer collections unchanged. Their database is still restored, so preserved pictures may not all correspond to records in that older database; this policy avoids silently deleting newer photographs.

Restore stages and validates the archive, rejects unsafe paths, creates a safety ZIP containing all current collections, and then replaces data and the included image collections. If installation fails, it attempts to restore the prior database and image folders. A regression test simulates failure while installing the locomotive collection after the car collection has changed.

Automatic session backups and legacy `.db` backups remain **database-only**. Use the manual **ZIP** backup to include pictures. Older application versions may reject these new multi-collection ZIPs; restore them using the updated application.

## Automated verification

Initial locomotive-image and presentation tests: **38 passed in 24.70s**.

Final expanded focused command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_locomotive_images.py tests/test_database_backup_service.py tests/test_packaging_cleanup.py tests/test_presentation_output.py tests/test_operations_sessions_completed_passenger.py tests/test_switch_list_completed_session.py -q
```

Result: **65 passed in 14.60s**.

Full suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: **149 passed, 2 warnings in 39.31s**.

Coverage includes image formats/discovery, safe naming, no-image behavior, source preservation, replacement/removal/rename, collisions, duplicate files, failed database commits, failed picture writes, runtime override and packaged paths, editor Save/reopen/Cancel, preview aspect ratio, unified archive round trips, legacy archives, empty collections, restore rollback, and unsafe archive paths. Existing operations, presentation, packaging, and companion tests remain passing.

Warnings:

- Starlette's HTTPX TestClient deprecation.
- AnyIO's `BlockingPortal` alias deprecation.

`git diff --check` reported no whitespace errors. Git emitted its standard Windows LF/CRLF advisories. Black completed formatting of the new helpers/tests but emitted a Python target-version advisory. No runtime test failures resulted.

An offscreen editor render confirmed that the preview and buttons fit within the dialog. The offscreen environment rendered text as missing-font boxes, so normal Windows text rendering and physical interaction still need manual checking.

## Manual acceptance checklist

Run the updated **source application**, not an old installed EXE. No installer or EXE was rebuilt. Prefer an isolated test database/data directory, particularly for the restore tests. Do not replace your production database to set up a test.

Record:

- Date/tester:
- Data directory used:
- Test locomotive identity:
- Original photo filename:
- Replacement photo filename:
- Backup ZIP filename:

### 1. Add a locomotive with a picture

- [ ] Open Motive Power and the locomotive roster.
- [ ] Choose Add Locomotive.
- [ ] Enter a unique test reporting mark and number, such as TEST / IMG1.
- [ ] Confirm the preview says **No Image Available** and Remove Picture is disabled.
- [ ] Click **Add Picture** and select a JPG or PNG photograph.
- [ ] Confirm the preview shows the selected photograph without stretching.
- [ ] Confirm the button changes to **Change Picture** and Remove Picture is enabled.
- [ ] Click Save.
- [ ] Reopen that locomotive for editing.
- [ ] Confirm the same photograph remains and the locomotive fields are correct.

PASS: The saved locomotive reopens with the selected picture and correct fields. FAIL: Missing/wrong picture, distorted preview, error, or changed locomotive fields.

Result/notes:

### 2. Replace and cancel replacement

- [ ] Click Change Picture, select a different photograph, and Save.
- [ ] Reopen and confirm the replacement is shown.
- [ ] Select the first photograph again but click Cancel instead of Save.
- [ ] Reopen and confirm the last saved replacement still appears.
- [ ] Confirm both original source photographs still exist outside the application's managed folder.

PASS: Save persists the replacement; Cancel does not replace it; source photographs are untouched.

Result/notes:

### 3. Cancel Add and cancel Remove

- [ ] Start adding another unique test locomotive.
- [ ] Select a picture, then Cancel the entire dialog.
- [ ] Confirm the locomotive was not added.
- [ ] Check Locomotive_Images and confirm no managed file for that canceled identity was created.
- [ ] Edit the saved test locomotive and click Remove Picture.
- [ ] Confirm the preview changes to No Image Available.
- [ ] Click Cancel, reopen, and confirm its saved picture is still present.

PASS: Neither canceled action changes stored records/pictures.

Result/notes:

### 4. Rename with picture

- [ ] Edit the test locomotive and change its number to a unique value such as IMG2.
- [ ] Save and reopen it.
- [ ] Verify its picture follows the renamed locomotive.
- [ ] Change its reporting mark to another unique test mark, Save, and reopen.
- [ ] Verify its picture still appears.
- [ ] In Locomotive_Images, confirm the managed filename follows the new identity and the old name is gone.
- [ ] Open another locomotive with a picture and verify that picture was not changed.

PASS: Both identity changes preserve the correct picture and do not affect another locomotive.

Result/notes:

### 5. Collision protection

- [ ] Create a second test locomotive with a different picture and unique identity.
- [ ] Try changing the first test locomotive's identity to match the second.
- [ ] Click Save and verify an error is shown and the dialog remains open.
- [ ] Cancel and reopen both locomotives.
- [ ] Confirm their identities and pictures remain unchanged.

Optional file-collision test — isolated test data only:

- [ ] Copy a disposable picture into Locomotive_Images as `L_TEST_BLOCKED.png`, with no locomotive using that identity.
- [ ] Try renaming a pictured test locomotive to TEST / BLOCKED and Save.
- [ ] Verify the occupied-picture error appears and neither picture is overwritten.
- [ ] Cancel the dialog. Remove only the disposable test file you created when finished.

PASS: Duplicate identities and occupied picture filenames are rejected without data/picture loss.

Result/notes:

### 6. Unified ZIP backup and restore

Perform this test in an isolated test layout. Restore intentionally replaces records and included picture collections.

- [ ] Ensure the test layout has at least one working car picture and one locomotive picture.
- [ ] Optionally place a disposable picture in its `Passenger_Images` folder to verify reserved-folder backup; no passenger-picture UI exists yet.
- [ ] Choose **File → Backup Database…** and save a new ZIP in a separate backup folder.
- [ ] Open the ZIP in File Explorer and confirm it contains `railroad.db`, `Car_Images/`, `Locomotive_Images/`, and `Passenger_Images/`.
- [ ] Verify the relevant picture files are inside their corresponding ZIP folders.
- [ ] Change the test locomotive's picture and Save.
- [ ] Choose **File → Restore Database…**, select that ZIP, and read the replacement warning before confirming.
- [ ] Confirm restore completes successfully and reports a safety backup.
- [ ] Reopen the test locomotive and verify its pre-backup picture has returned.
- [ ] Open a car's Waybill preview and verify its car picture still appears.
- [ ] If a passenger-folder test file was included, verify it is restored in Passenger_Images.
- [ ] Inspect the safety ZIP and confirm it contains the locomotive picture from immediately before the restore.

PASS: One ZIP preserves/restores all included collections, car pictures remain usable, and the safety ZIP retains the pre-restore state. FAIL: Missing collection, incorrect image, failed restore, or missing safety backup.

Result/notes:

### 7. Older backup compatibility (optional, isolated layout only)

- [ ] Obtain an older car-only layout ZIP and keep a separate current full ZIP backup.
- [ ] Note the current locomotive/passenger picture files.
- [ ] Restore the older car-only ZIP in the isolated layout.
- [ ] Confirm the older database/car pictures restore, while locomotive/passenger picture files remain on disk.
- [ ] Do not expect every retained picture to match a locomotive in the older restored database.

PASS: Newer collections are not silently deleted merely because an older archive did not include them.

Result/notes:

### 8. Remove picture and normal no-picture editing

- [ ] Edit a pictured test locomotive, click Remove Picture, then Save.
- [ ] Reopen and verify **No Image Available** and disabled Remove Picture.
- [ ] Verify the application's managed picture is gone and the source photograph remains.
- [ ] Add a locomotive without selecting a picture; Save and reopen without errors.
- [ ] Edit an existing no-picture locomotive and verify ordinary fields still save correctly.

PASS: Saved removal affects only the managed picture; no-picture locomotives still work normally.

Result/notes:

## Limitations and next steps

- Passenger-picture Add/Edit controls and locomotive pictures in Operations Sessions/iPad companion remain separate features.
- This does not rebuild the executable or installer. Rebuild before expecting these changes in the installed application.
- Normal exceptions trigger file rollback, but database/filesystem changes are not a single crash-proof transaction. Power loss or unrecoverable disk errors can require recovery from backup. Avoid running multiple desktop editors or manually changing managed image files during Save/Restore.
- Deleting an entire locomotive still uses the existing delete behavior; it does not automatically delete its picture. Use Remove Picture and Save before deleting a locomotive if you want its managed photograph removed. Retained files intentionally block silent reuse of that identity's picture filename.
- Restoring old database-only backups does not restore or reconcile pictures.
- Physical Windows acceptance tests above remain to be performed.

Overall manual result: PASS / FAIL / PARTIAL / NOT RUN
