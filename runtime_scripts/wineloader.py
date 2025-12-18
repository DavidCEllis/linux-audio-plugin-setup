#! /usr/bin/env python3

# Based on https://github.com/microfortnight/yabridge-bottles-wineloader
# This uses a default bottle and runner instead of reverting to system WINE when
# no prefix is given.

"""
Try to find the appropriate wine runtime for a wine prefix that has been created
by bottles.

System WINE will only be used if specified by the bottle
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

CONFIG_PATH = Path(__file__).resolve().parents[1] / "runtime_config" / "wine_settings.json"


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
                return SYSTEM_WINE
            elif runner:
                # The bottle runtime
                bottles_root = (
                    Path(WINEPREFIX).parents[1] / "runners" / runner / "bin" / "wine"
                )
                return str(bottles_root)
    else:
        # Set the wine prefix to avoid having yabridge mess with the user's default ~/.wine prefix
        os.environ["WINEPREFIX"] = config.default_prefix

    return config.default_wine


def main() -> int:
    wine_exe = get_wine_executable()
    if not os.path.exists(wine_exe):
        raise FileNotFoundError(f"wine executable not found: '{wine_exe}'")

    # Python's os.exec* functions treat the first argument as the name of the executable
    args = ["wine", *sys.argv[1:]]

    tempf = Path(__file__).resolve().parent / "tempf.txt"
    with open(tempf, mode='a') as f:
        f.write(f"Prefix={WINEPREFIX} | {os.environ.get('WINEPREFIX')}\n")

    # Execute wine and replace the python process
    os.execvp(wine_exe, args)


if __name__ == "__main__":
    main()
