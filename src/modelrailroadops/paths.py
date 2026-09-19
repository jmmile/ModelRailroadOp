"""Runtime paths shared by source runs and packaged builds."""

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIRECTORY_OVERRIDE_ENV = "MODELRAILROADOPS_DATA_DIR"


def data_directory_override():
    """
    Return the configured data-directory override, if one is active.

    The environment variable is intentionally supported for isolated
    testing and other controlled runs. Normal application launches
    should leave it unset.
    """

    override = os.environ.get(
        DATA_DIRECTORY_OVERRIDE_ENV
    )

    if not override:
        return None

    return Path(
        override
    ).expanduser().resolve()


def data_directory():
    """
    Return the directory containing runtime application data.

    An explicit MODELRAILROADOPS_DATA_DIR environment override takes
    precedence over the normal source or packaged application path.
    """

    override = data_directory_override()

    if override is not None:
        return override

    if getattr(
        sys,
        "frozen",
        False,
    ):
        return (
            Path(
                os.environ.get(
                    "LOCALAPPDATA",
                    Path.home()
                    / "AppData"
                    / "Local",
                )
            )
            / "ModelRailroadOperations"
        )

    return PROJECT_ROOT / "data"


DATA_DIRECTORY = data_directory()
