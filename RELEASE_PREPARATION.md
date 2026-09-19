# Windows release preparation

## Data locations

Source runs keep using the project's `data` folder. Packaged runs use
`%LOCALAPPDATA%/ModelRailroadOperations`. `MODELRAILROADOPS_DATA_DIR` overrides
both for isolated testing. Database, images, backups, and logs use this root.
Installation resources must be bundled separately from writable user data.

## Moving a layout to the EXE or laptop

1. In the source application, use File > Backup Database to save a ZIP.
2. Start the packaged application. A fresh data folder gets an empty database.
3. Use File > Restore Database to choose the ZIP. This imports the database
   and car images. It preserves a complete safety backup before replacement.
4. Verify roster totals, waybills, and pictures before operating.

ZIP restores replace the image collection; DB restores leave images alone.
Automatic session backups remain database-only and retain ten snapshots.
Manual backups and restore safety backups are not automatically pruned.
No existing layout is automatically moved or overwritten on first launch.

## Startup and release contents

Both entry points use `modelrailroadops.__main__`. Startup creates schema and
runs migrations; it does not invoke `seed_database.py` or insert sample industries.
All database import paths share one engine and session factory. Startup errors
are logged to `logs/application.log` under the data folder (three rotated copies).
Runtime packages are listed in `requirements-runtime.txt`; capture tested exact
versions when producing the first build. Never bundle the working database,
backups, logs, sample-data scripts, personal CSV files, or development tools.

## Remaining EXE acceptance checks

- Build specification, icon/version metadata, installer, and dependency pins.
- Launch from a shortcut with a different working directory.
- Transfer a real ZIP layout to an isolated packaged data folder.
- Verify image display, waybill preview, physical printing, pickup/setout,
  undo, and backup/restore through the interface.
- Test installation and upgrade on the laptop, preserving its data.

These checks require the packaged application; automated source tests do not
replace them.
