# Application icon — concept C

Approved by the user: angled cream/gold streamliner on navy, concept C from the original board.

`concept-c.png` is the standalone artwork produced with the built-in image-generation tool using the imagegen skill. It is build-source artwork only, not packaged personal data.

Final refinement prompt: "Edit target supplied locomotive app icon. Preserve locomotive and rails exactly. Fix background: uniform solid dark navy everywhere behind train and tracks and to all four square canvas edges. Fully opaque image, NO transparency anywhere, no rounded tile, no black holes or blotches, no texture, no glow. Cream and gold locomotive and tracks unchanged. Square standalone application icon, no text."

Run `python packaging/make_icon.py` with the project's environment to regenerate `src/modelrailroadops/resources/application.ico`. It contains 16, 24, 32, 48, 64, 128, and 256 pixel PNG representations. The ICO is used for both EXEs, the desktop window, and the installer. The package audit permits only this exact project resource and checks its source hash; personal photograph exclusions remain unchanged.
