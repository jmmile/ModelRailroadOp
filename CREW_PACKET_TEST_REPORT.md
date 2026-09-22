# Crew operating packet

## Where to find it

Operations Sessions → select a session → **Crew Packet**. The report buttons have their own row below the session controls. The packet includes every train assigned to the selected session, plus a warning section for any train referenced by its freight moves but missing from the session assignments.

Use **Refresh Packet** after changing the operating plan, **Print** for a paper copy, or **Save PDF**. Printing or saving is read-only and never starts a session, moves a car, or checks off work in the database. Refreshing clears an old packet first so a failed refresh cannot accidentally print stale work.

## Contents

1. Crew operating checklist: select/validate the session, confirm assignments, prepare motive power and equipment, locate cars, build the train, and work the route.
2. Train preparation: assigned locomotives and passenger equipment in consist order, route stops, tracks, and arrival/departure times.
3. Freight work checklist: route-ordered pickups and set-outs with car identity/type/length, exact origin and destination, move and waybill IDs, current location, instructions, and separate paper boxes for physical work and application recording. Completed instructions are marked reference-only.
4. Session closeout: reconcile cars aboard, return exceptions, compare actual locations, record unresolved work, review all trains, complete the session through the new summary/checklist, and back up when appropriate.

The user's full-cycle PDF informed the operating sequence and tab guidance. Deliberate cancellation testing and repeated pickups were not copied as mandatory crew tasks. Returns remain an exception procedure. The original PDF is unchanged.

## Implementation files

- `src/modelrailroadops/services/crew_packet_service.py`: read-only session, consist, route, and freight packet data.
- `src/modelrailroadops/ui/operations/crew_packet_dialog.py`: packet layout, multipage preview, printing, safe PDF saving. Failed exports preserve an existing destination file.
- `src/modelrailroadops/ui/operations/operations_sessions_widget.py`: Crew Packet action and separate report-button row.
- `tests/test_crew_packet.py`: ten packet/data/layout/export tests.
- `.gitignore`: excludes temporary QA renders and generated sample output.
- `CREW_PACKET_TEST_REPORT.md`: this report.

Earlier uncommitted end-of-session summary changes remain in place and are required by the packet. No new dependencies, database migrations, or packaging changes are needed; the existing build discovers the imported modules.

## Verification

- Initial focused packet and session-summary tests: **13 passed in 4.14 seconds**.
- Final complete suite: **226 passed, 2 warnings in 30.45 seconds**.
- Warnings: existing Starlette/HTTPX and AnyIO deprecations.
- `git diff --check`: passed (Windows line-ending notices only).
- Fictional demonstration PDF rendered and visually inspected on all four Letter-size pages with the normal Windows font engine. Checks, tables, page numbers, and headings are readable; no clipping observed.
- The headless Qt font engine initially produced black text blocks. The normal Windows rendering was separately verified; offscreen test PDF existence alone is not treated as visual proof.
- Demonstration file: `output/pdf/Crew-Packet-Demonstration.pdf`. It contains fabricated equipment and locations, not production data.

## Manual acceptance

- [ ] Rebuild with `powershell -NoProfile -ExecutionPolicy Bypass -File packaging\build.ps1`, then close the desktop/companion and install the new installer.
- [ ] Select a planned session and open Crew Packet. Confirm correct session/date and all assigned trains.
- [ ] Compare locomotive and passenger equipment order with the session's assignments.
- [ ] Compare route/timetable and freight destinations, including industry spots and general tracks, with the program.
- [ ] Preview all pages, print one packet, and confirm readability at your normal printer settings.
- [ ] Save PDF and open it in your usual reader. Canceling either save or print must not change the session.
- [ ] Complete one real move through Switch List or the companion, then Refresh Packet. That instruction should say COMPLETED - reference only; do not physically repeat it.
- [ ] Confirm the crew checklist and closing procedure make sense during an actual operating session.

## Boundaries

This is a printable packet, not an interactive PDF form. Checkmarks/handwritten notes are not saved in the database. Counts and locations are snapshots when refreshed, not live while printed. The packet does not determine freight consist order, authorize route changes, allocate missing equipment, carry work forward, or automatically record passenger stops. Very long notes or large consists can span additional pages; inspect print preview before printing. Source changes have been tested; the installed EXE has not been rebuilt or updated in this task.

No production database or picture collection was modified. No commit or push was performed.
