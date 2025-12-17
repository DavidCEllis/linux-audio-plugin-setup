#! /usr/bin/env python3
# Create the pipewire sinks folder and install the sink conf file
# Use a symlink

import argparse
import shutil
import subprocess
from pathlib import Path

PIPEWIRE = shutil.which("pipewire")
if not PIPEWIRE:
    raise FileNotFoundError("'pipewire' utility not found could not install sinks")

CONF_FILE = Path(__file__).parents[1] / "runtime_config" / "plugin-routing-sink.conf"
if not CONF_FILE.exists():
    raise FileNotFoundError("Could not find 'plugin-routing-sink.conf' conf file")


def update_sinks_conf(conf_file: Path, remove: bool = False) -> None:
    conf_folder = Path.home() / ".config" / "pipewire" / "pipewire.conf.d"
    conf_folder.mkdir(parents=True, exist_ok=True)

    dest = conf_folder / "plugin-routing-sink.conf"

    if remove:
        try:
            dest.unlink()
        except FileNotFoundError:
            print(f"'{dest}' has already been removed, no action taken.")
        except PermissionError:
            print(f"You do not have permission to modify '{dest}'")
        else:
            print(f"'{dest}' removed")
    else:
        print(f"Linking from '{conf_file}' to '{dest}'")
        dest.unlink(missing_ok=True)
        dest.symlink_to(conf_file.absolute())


def reload_pipewire():
    subprocess.run(
        ["systemctl", "--user", "restart", "pipewire"],
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(description="Script to install pipewire sinks")
    parser.add_argument("--remove", action="store_true", help="Remove the installed conf file")
    args = parser.parse_args()

    update_sinks_conf(CONF_FILE, args.remove)
    reload_pipewire()


if __name__ == "__main__":
    main()
