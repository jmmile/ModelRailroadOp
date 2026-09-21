# Concept C application icon

The selected cream/gold angled locomotive on navy is now used by the desktop window, both Windows executables, and the installer. Windows shortcuts inherit the executable icon. Equipment picture collections and the database are not affected.

## Files

- `packaging/artwork/concept-c.png`: approved standalone artwork, derived with the built-in image generation tool using the imagegen skill.
- `packaging/artwork/README.md`: artwork provenance, final refinement prompt, regeneration instructions.
- `packaging/make_icon.py`: reproducible conversion into Windows ICO.
- `src/modelrailroadops/resources/application.ico`: 16/24/32/48/64/128/256-pixel icon representations.
- `src/modelrailroadops/ui/main_window.py`: sets the desktop window icon.
- `ModelRailroadOperations.spec`: embeds the icon in both EXEs and includes the runtime ICO.
- `packaging/installer.iss`: sets the installer icon.
- `packaging/release_audit.py`: exact resource source allowance and bundled icon hash verification. Personal-photo exclusions remain in effect.
- `packaging/verify_build.py`: verifies the packaged window icon loads.
- `tests/test_application_icon.py`: validates every ICO representation and Qt loading.
- `packaging/README.md`: updates icon description.
- `packaging/ICON_RELEASE_REPORT.md`: this report.

## Automated checks

Full test suite: **209 passed, 2 warnings in 29.26 seconds**. The warnings are existing Starlette/HTTPX and AnyIO deprecations. `git diff --check` passed, with Windows line-ending notices.

## Manual checks after installing

- [ ] Close desktop and companion, then install the rebuilt release installer.
- [ ] Confirm the installer and application shortcuts display the locomotive icon.
- [ ] Launch the desktop and confirm the window/taskbar icon.
- [ ] Check readability at your normal Windows display scaling.

Windows may cache older shortcut icons. If the old icon remains, recreate the shortcut or sign out and back in. No commit or push was performed.
