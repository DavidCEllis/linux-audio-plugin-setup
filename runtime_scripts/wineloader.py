#! /usr/bin/env python3

# Based on https://github.com/microfortnight/yabridge-bottles-wineloader
# Converted to Python and with a YABRIDGE backup if there is no system WINE

"""
Try to find the appropriate wine runtime for a wine prefix that has been created
by bottles.

Intended so yabridge doesn't use system wine which won't work if it is up to date.
"""

import os
import shutil
import sys
import subprocess

from pathlib import Path

YQ_BIN = shutil.which("yq")

if YQ_BIN is None:
    raise FileNotFoundError("'yq' is not installed or is not available on PATH")

# Look for system wine on PATH
SYSTEM_WINE = shutil.which("wine")
WINEPREFIX = os.environ.get("WINEPREFIX", "")
YABRIDGE_WINE = os.environ.get("YABRIDGE_WINE", "")


def get_wine_executable() -> str | None:
    bottle_path = Path(WINEPREFIX) / "bottle.yml"
    if bottle_path.exists():
        # Parse the bottle yaml data
        result = subprocess.run(
            [
                YQ_BIN,
                "-r",
                ".Runner",
                bottle_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        runner = result.stdout.strip()

        if runner.startswith("sys-"):
            return SYSTEM_WINE
        elif runner:
            # The bottle runtime
            bottles_root = (
                Path(WINEPREFIX).parents[1] / "runners" / runner / "bin" / "wine"
            )
            return str(bottles_root)
        else:
            return YABRIDGE_WINE

    return SYSTEM_WINE or YABRIDGE_WINE or None


def main() -> int:
    wine_exe = get_wine_executable()
    if not wine_exe:
        raise FileNotFoundError("Could not find a usable 'wine' executable")
    elif not os.path.exists(wine_exe):
        raise FileNotFoundError(f"wine executable not found: '{wine_exe}'")

    # Python's os.exec* functions treat the first argument as the name of the executable
    args = ["wine", *sys.argv[1:]]

    # Execute wine and replace the python process
    os.execvp(wine_exe, args)


if __name__ == "__main__":
    main()
