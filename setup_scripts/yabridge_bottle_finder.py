#! /usr/bin/env python3
# This script will search for the standard VST Folders in 'bottles' and automatically add them to YABridge
# This assumes that bottles has been installed from the flatpak

import shutil
import subprocess
from pathlib import Path


BASE_PATH = Path.home() / ".var" / "app" / "com.usebottles.bottles"  # Base flatpak path
BOTTLES_PATH = BASE_PATH / "data" / "bottles" / "bottles"  # Folder for bottles' bottles

if not BOTTLES_PATH.exists():
    raise FileNotFoundError(f"No bottles folder found at '{BOTTLES_PATH}'")

YABRIDGECTL = shutil.which("yabridgectl")
if not YABRIDGECTL:
    raise FileNotFoundError("yabridgectl could not be found on PATH")


def find_vst_folders(bottles_path: Path) -> set[Path]:
    """
    Get a list of potential VST folders from within the bottles windows drives

    :param bottles_folder: The base folder for individual bottles
                           ~/.var/app/com.usebottles.bottles/data/bottles/bottles
    :return: list of possible VST folders
    """
    vst_foldernames = {"VST3", "VSTPlugins", "VST2", "VstPlugins"}

    folders = {f[0] for f in bottles_path.walk() if f[0].name in vst_foldernames}

    return folders


def get_existing_vst_folders() -> set[Path]:
    """
    Get a set of existing VST folders from YABridge

    :return: set of bridge folders
    """
    result = subprocess.run(
        [YABRIDGECTL, "list"],
        capture_output=True,
        check=True,
        text=True,
    )
    folders = {Path(f) for f in result.stdout.strip().split("\n")}
    return folders


def set_yabridge_vst_folders() -> None:
    """
    Add new VST folders in bottles to yabridge
    Remove VST folders that no longer exist on the system
    """
    existing_vst_folders = get_existing_vst_folders()
    new_vst_folders = find_vst_folders(BOTTLES_PATH)

    add_vst_folders = new_vst_folders - existing_vst_folders
    remove_vst_folders = [p for p in existing_vst_folders if not p.exists()]

    if remove_vst_folders:
        print("Removing VST folders that no longer exist:")
        for p in remove_vst_folders:
            print(f"\t{p}")
            subprocess.run(
                [
                    YABRIDGECTL,
                    "rm",
                    p,
                ],
                capture_output=True,
                check=True,
            )

    if add_vst_folders:
        print("Adding new VST folders:")
        for p in add_vst_folders:
            print(f"\t{p}")
            subprocess.run(
                [
                    YABRIDGECTL,
                    "add",
                    p,
                ],
                capture_output=True,
                check=True,
            )

    if not add_vst_folders and not remove_vst_folders:
        print("No changes to yabridge VST folders")


def main():
    set_yabridge_vst_folders()


if __name__ == "__main__":
    main()
