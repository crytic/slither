from pathlib import Path
import shutil
import sysconfig

from slither.utils.colors import yellow, green, red


def check_path_config(name: str) -> tuple[bool, Path | None, list[Path]]:
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
        binary_path = Path(binary_path).resolve()
        this_code = Path(__file__).resolve()
        this_binary = list(filter(lambda x: this_code.is_relative_to(x[1]), possible_paths))
        binary_here = len(this_binary) > 0 and all(
            binary_path.is_relative_to(script) for script, _ in this_binary
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
