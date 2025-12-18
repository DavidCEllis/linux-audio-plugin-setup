#! /usr/bin/env python3
# This sets up the wineloader script so yabridge uses the correct versions of wine

import argparse
import json
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tkinter import Tk, filedialog


WINELOADER_SCRIPT = Path(__file__).parents[1] / "runtime_scripts/wineloader.py"
WINELOADER_CONF = Path(__file__).parents[1] / "runtime_config/wineloader.conf"
CONFIG_PATH = Path(__file__).parents[1] / "user_config/wine_settings.json"

if not (WINELOADER_CONF.exists() and WINELOADER_SCRIPT.exists()):
    raise FileNotFoundError("Could not find wineloader.py and/or wineloader.conf")


# Bottles paths
BASE_PATH = Path.home() / ".var" / "app" / "com.usebottles.bottles" / "data" / "bottles" # Base flatpak path
RUNTIME_PATH = BASE_PATH / "runners"  # Folder for bottles' wine runtimes
BOTTLES_PATH = BASE_PATH / "bottles"  # Folder for bottles' bottles


# File dialog helpers
@contextmanager
def handle_tk_root():
    """
    Short decorator to create, hide and destroy the necessary Tk root
    Using tkinter directly without defining the root first leaves a small
    blank window. This hides the window.
    """
    root = Tk()
    root.withdraw()
    try:
        yield
    finally:
        root.destroy()


@handle_tk_root()
def askopenfilename(**options):
    """
    Passes to askopenfilenname
    :param options: askopenfilename options (see tkinter docs)
    :return: Path of filename or None
    """
    open_filename = filedialog.askopenfilename(**options)

    if open_filename:
        return Path(open_filename)
    else:
        return None


@dataclass
class Config:
    default_wine: str
    default_prefix: str

    @classmethod
    def create(cls):
        default_wine = askopenfilename(
            title="Select the default 'wine' executable",
            initialdir=RUNTIME_PATH,
        )

        default_bottle = askopenfilename(
            title="Select the default wine prefix bottle.yml file",
            initialdir=BOTTLES_PATH,
            filetypes=[("YAML Files", "*.yml")]
        )

        default_prefix = default_bottle.parent

        return cls(str(default_wine), str(default_prefix))

    def write(self, config_path: Path) -> None:
        config_text = json.dumps(
            {
                "default_wine": self.default_wine,
                "default_prefix": self.default_prefix,
            },
            indent=2,
        )
        config_path.parent.mkdir(exist_ok=True)
        config_path.write_text(config_text)


def install(script_dest: Path, conf_dest: Path):
    # Make sure the bin folder exists and symlink wineloader.py into it
    script_dest.parent.mkdir(parents=True, exist_ok=True)
    script_dest.unlink(missing_ok=True)
    script_dest.symlink_to(WINELOADER_SCRIPT.absolute())
    print(f"Link from '{WINELOADER_SCRIPT}' to '{script_dest}' created")

    # Symlink the conf file too
    conf_dest.parent.mkdir(parents=True, exist_ok=True)
    conf_dest.unlink(missing_ok=True)
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


def make_wineloader_executable(wineloader_script):
    # Make sure the script is executable
    subprocess.run(
        ["chmod", "+x", wineloader_script],
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
        config = Config.create()
        config.write(CONFIG_PATH)
        print(f"Config written to '{CONFIG_PATH}'")

        make_wineloader_executable(WINELOADER_SCRIPT)
        install(script_dest, conf_dest)
        create_yabridge_symlink()
        print("Restart or logout/login to complete installation")


if __name__ == "__main__":
    main()