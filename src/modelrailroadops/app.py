"""Compatibility entry point for older launch configurations."""
from modelrailroadops.__main__ import Application, main

__all__ = ["Application", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
