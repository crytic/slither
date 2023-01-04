from pathlib import Path
from typing import List, Optional, Tuple
import shutil
import sys
import sysconfig

from slither.utils.colors import yellow, green, red


def path_is_relative_to(path: Path, relative_to: Path) -> bool:
    """
    Check if a path is relative to another one.

    Compatibility wrapper for Path.is_relative_to
    """
    if sys.version_info >= (3, 9, 0):
        return path.is_relative_to(relative_to)

    path_parts = path.resolve().parts
    relative_to_parts = relative_to.resolve().parts

    if len(path_parts) < len(relative_to_parts):
        return False

    for (a, b) in zip(path_parts, relative_to_parts):
        if a != b:
            return False

    return True


def check_path_config(name: str) -> Tuple[bool, Optional[Path], List[Path]]:
    """
    Check if a given Python binary/script is in PATH.
    :return: Returns if the binary on PATH corresponds to this installation,
             its path (if present), and a list of possible paths where this
             binary might be found.
    """
    binary_path = shutil.which(name)
    possible_paths = []

    for scheme in sysconfig.get_scheme_names():
        script_path = Path(sysconfig.get_path("scripts", scheme))
        purelib_path = Path(sysconfig.get_path("purelib", scheme))
        script_binary_path = shutil.which(name, path=script_path)
        if script_binary_path is not None:
            possible_paths.append((script_path, purelib_path))

    binary_here = False
    if binary_path is not None:
        binary_path = Path(binary_path)
        this_code = Path(__file__)
        this_binary = list(filter(lambda x: path_is_relative_to(this_code, x[1]), possible_paths))
        binary_here = len(this_binary) > 0 and all(
            path_is_relative_to(binary_path, script) for script, _ in this_binary
        )

    return binary_here, binary_path, list(set(script for script, _ in possible_paths))


def check_slither_path(**_kwargs) -> None:
    binary_here, binary_path, possible_paths = check_path_config("slither")
    show_paths = False

    if binary_path:
        print(green(f"`slither` found in PATH at `{binary_path}`."))
        if binary_here:
            print(green("Its location matches this slither-doctor installation."))
        else:
            print(
                yellow(
                    "This path does not correspond to this slither-doctor installation.\n"
                    + "Double-check the order of directories in PATH if you have several Slither installations."
                )
            )
            show_paths = True
    else:
        print(red("`slither` was not found in PATH."))
        show_paths = True

    if show_paths:
        print()
        print("Consider adding one of the following directories to PATH:")
        for path in possible_paths:
            print(f"  * {path}")
