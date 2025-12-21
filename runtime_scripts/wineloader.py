#! /usr/bin/env python3

# Based on https://github.com/microfortnight/yabridge-bottles-wineloader
# This uses a default bottle and runner instead of reverting to system WINE when
# no prefix is given.

"""
Try to find the appropriate wine runtime for a wine prefix that has been created
by bottles.

If system wine does not exist a separate wine install will be used with the prefix
the user defines during setup.
"""

import json
import os
import shutil
import sys
import subprocess

from dataclasses import dataclass
from pathlib import Path

YQ_BIN = shutil.which("yq")

if YQ_BIN is None:
    raise FileNotFoundError("'yq' is not installed or is not available on PATH")

# Look for system wine on PATH
SYSTEM_WINE = shutil.which("wine")
WINEPREFIX = os.environ.get("WINEPREFIX")

CONFIG_PATH = Path(__file__).resolve().parents[1] / "user_config" / "wine_settings.json"


@dataclass
class Config:
    default_wine: str
    default_prefix: str

    @classmethod
    def from_json(cls, config_path: Path):

        if not config_path.exists():
            raise FileNotFoundError("Could not find the config file '{config_path}'")

        conf = json.loads(config_path.read_text())

        return cls(
            default_wine=conf["default_wine"],
            default_prefix=conf["default_prefix"],
        )


def get_wine_executable() -> str:
    config = Config.from_json(CONFIG_PATH)

    wine_runtime = SYSTEM_WINE or config.default_wine

    if WINEPREFIX:
        # Attempt to get the runtime path from the wine prefix
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
                if SYSTEM_WINE is None:
                    raise FileNotFoundError("System WINE requested by bottle but not found on PATH")
                wine_runtime = SYSTEM_WINE
            elif runner:
                # The bottle runtime
                bottles_wine_binary = (
                    Path(WINEPREFIX).parents[1] / "runners" / runner / "bin" / "wine"
                )
                wine_runtime = str(bottles_wine_binary)
    elif not SYSTEM_WINE:
        # If there is no system wine, don't create a default prefix in the user dir
        # Use the one setup during initialisation
        os.environ["WINEPREFIX"] = config.default_prefix

    return wine_runtime


def main() -> int:
    wine_exe = get_wine_executable()
    if not os.path.exists(wine_exe):
        raise FileNotFoundError(f"wine executable not found: '{wine_exe}'")

    # Python's os.exec* functions treat the first argument as the name of the executable
    args = ["wine", *sys.argv[1:]]

    # Some tempfile writing used when debugging
    # tempf = Path(__file__).resolve().parent / "tempf.txt"
    # with open(tempf, mode='a') as f:
    #     f.write(f"Prefix={WINEPREFIX} | {os.environ.get('WINEPREFIX')}\n")

    # Execute wine and replace the python process
    os.execvp(wine_exe, args)


if __name__ == "__main__":
    main()
