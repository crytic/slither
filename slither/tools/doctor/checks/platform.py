import logging
from pathlib import Path

from crytic_compile import crytic_compile

from slither.tools.doctor.utils import snip_section
from slither.utils.colors import red, yellow, green


def detect_platform(project: str, **kwargs) -> None:
    path = Path(project)
    if path.is_file():
        print(
            yellow(
                f"{project!r} is a file. Using it as target will manually compile your code with solc and _not_ use a compilation framework. Is that what you meant to do?"
            )
        )
        return

    print(f"Trying to detect project type for {project!r}")

    supported_platforms = crytic_compile.get_platforms()
    skip_platforms = {"solc", "solc-json", "archive", "standard", "etherscan"}
    detected_platforms = {
        platform.NAME: platform.is_supported(project, **kwargs)
        for platform in supported_platforms
        if platform.NAME.lower() not in skip_platforms
    }
    platform_qty = len([platform for platform, state in detected_platforms.items() if state])

    print("Is this project using...")
    for platform, state in detected_platforms.items():
        print(f"    =>  {platform + '?':<15}{state and green('Yes') or red('No')}")
    print()

    if platform_qty == 0:
        print(red("No platform was detected! This doesn't sound right."))
        print(
            yellow(
                "Are you trying to analyze a folder with standalone solidity files, without using a compilation framework? If that's the case, then this is okay."
            )
        )
    elif platform_qty > 1:
        print(red("More than one platform was detected! This doesn't sound right."))
        print(
            red("Please use `--compile-force-framework` in Slither to force the correct framework.")
        )
    else:
        print(green("A single platform was detected."), yellow("Is it the one you expected?"))


def compile_project(project: str, **kwargs):
    print("Invoking crytic-compile on the project, please wait...")

    try:
        crytic_compile.CryticCompile(project, **kwargs)
    except Exception as e:  # pylint: disable=broad-except
        with snip_section("Project compilation failed :( The following error was generated:"):
            logging.exception(e)
