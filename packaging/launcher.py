"""Windowed executable entry point with opt-in isolated build verification."""

import sys
from pathlib import Path

if __name__ == "__main__":
    if "--verify-build" in sys.argv:
        from verify_build import verify

        raise SystemExit(verify())
    if (
        "--companion" in sys.argv
        or Path(sys.executable).stem == "Model Railroad Companion"
    ):
        from modelrailroadops.database.database import initialize_database
        from modelrailroadops.web.server import run

        initialize_database()
        run()
        raise SystemExit(0)
    from modelrailroadops.__main__ import main

    raise SystemExit(main())
