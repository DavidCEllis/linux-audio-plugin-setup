#! /usr/bin/env python3
# This sets up the wineloader script so yabridge uses the correct versions of wine

import argparse
import subprocess
from pathlib import Path

WINELOADER_SCRIPT = Path(__file__).parents[1] / "runtime_scripts/wineloader.py"
WINELOADER_CONF = Path(__file__).parents[1] / "runtime_config/wineloader.conf"

if not (WINELOADER_CONF.exists() and WINELOADER_SCRIPT.exists()):
    raise FileNotFoundError("Could not find wineloader.py and/or wineloader.conf")

def install(script_dest: Path, conf_dest: Path):
    # Make sure the bin folder exists and symlink wineloader.py into it
    script_dest.parent.mkdir(parents=True, exist_ok=True)
    script_dest.symlink_to(WINELOADER_SCRIPT.absolute())
    print(f"Link from '{WINELOADER_SCRIPT}' to '{script_dest}' created")

    # Symlink the conf file too
    conf_dest.parent.mkdir(parents=True, exist_ok=True)
    conf_dest.symlink_to(WINELOADER_CONF.absolute())
    print(f"Link from '{WINELOADER_CONF}' to '{conf_dest}' created")


def uninstall(script_dest: Path, conf_dest: Path):
    try:
        script_dest.unlink()
    except FileNotFoundError:
        print(f"'{script_dest}' has already been removed")
    else:
        print(f"'{script_dest}' removed")

    try:
        conf_dest.unlink()
    except FileNotFoundError:
        print(f"'{conf_dest}' has already been removed")
    else:
        print(f"'{conf_dest}' removed")


def make_wineloader_executable():
    # Make sure the script is executable
    subprocess.run(
        ["chmod", "+x", WINELOADER_SCRIPT],
        check=True,
    )


def create_yabridge_symlink():
    yabridge_source = Path.home() / ".local/share/yabridge/yabridgectl"
    yabridge_dest = Path.home() / ".local/bin/yabridgectl"

    if yabridge_dest.exists():
        print(f"yabridgectl already installed at '{yabridge_dest}'")
        return

    if not yabridge_source.exists():
        raise FileNotFoundError(f"Could not find the yabridgectl executable at '{yabridge_source}'")

    subprocess.run(
        ["chmod", "+x", yabridge_source],
        check=True,
    )

    yabridge_dest.symlink_to(yabridge_source.absolute())


def remove_yabridge_symlink():
    yabridge_dest = Path.home() / ".local/bin/yabridgectl"

    try:
        yabridge_dest.unlink()
    except FileNotFoundError:
        print(f"'{yabridge_dest}' has already been removed")
    else:
        print(f"'{yabridge_dest}' removed")


def main():
    parser = argparse.ArgumentParser(
        description="Install yabridge and the wineloader script"
    )
    parser.add_argument(
        "--remove",
        help="Remove the yabridge binary, wineloader script and environment variables"
    )

    args = parser.parse_args()

    local_dir = Path.home() / ".local"
    config_dir = Path.home() / ".config"

    script_dest = local_dir / "bin/wineloader.py"
    conf_dest = config_dir / "environment.d/wineloader.conf"

    if args.remove:
        remove_yabridge_symlink()
        uninstall(script_dest, conf_dest)
    else:
        make_wineloader_executable()
        install(script_dest, conf_dest)
        create_yabridge_symlink()
        print("Restart or logout/login to complete installation")


if __name__ == "__main__":
    main()