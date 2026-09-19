"""Windowed executable entry point with opt-in isolated build verification."""
import sys

if __name__ == "__main__":
    if "--verify-build" in sys.argv:
        from verify_build import verify
        raise SystemExit(verify())
    from modelrailroadops.__main__ import main
    raise SystemExit(main())
