import sys
from pathlib import Path

# Make the src folder visible to Python
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modelrailroadops.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())