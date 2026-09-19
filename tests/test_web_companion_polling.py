"""Execute the shipped browser script with controlled DOM, fetch and timers."""

from pathlib import Path
import shutil
import subprocess

import pytest


def test_companion_polling():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required for browser-script regression coverage")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [node, str(root / "tests/companion_polling.cjs"),
         str(root / "src/modelrailroadops/web/static/index.html")],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
