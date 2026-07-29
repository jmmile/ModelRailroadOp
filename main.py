import sys
from pathlib import Path

# Tell Python where the application package is
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())