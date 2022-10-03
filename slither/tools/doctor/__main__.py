import argparse
import logging
from pathlib import Path

from crytic_compile import cryticparser
import crytic_compile.crytic_compile as crytic_compile

from slither.tools.doctor.packages import get_installed_version, get_github_version
from slither.tools.doctor.utils import report_section, snip_section
from slither.utils.colors import red, yellow, green


def parse_args() -> argparse.Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(
        description="Troubleshoot running Slither on your project",
        usage="slither-doctor project",
    )

    parser.add_argument("project", help="The codebase to be tested.")

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    return parser.parse_args()


def show_versions() -> None:
    versions = {
        "Slither": (get_installed_version("slither-analyzer"), get_github_version("slither")),
        "crytic-compile": (
            get_installed_version("crytic-compile"),
            get_github_version("crytic-compile"),
        ),
        "solc-select": (get_installed_version("solc-select"), get_github_version("solc-select")),
    }

    outdated = {
        name
        for name, (installed, latest) in versions.items()
        if not installed or not latest or latest > installed
    }

    for name, (installed, latest) in versions.items():
        color = yellow if name in outdated else green
        print(f"{name + ':':<16}{color(installed or 'N/A'):<16} (latest is {latest or 'Unknown'})")

    if len(outdated) > 0:
        print()
        print(
            yellow(
                f"Please update {', '.join(outdated)} to the latest release before creating a bug report."
            )
        )
    else:
        print()
        print(green("Your tools are up to date."))


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
    except Exception as e:
        with snip_section("Project compilation failed :( The following error was generated:"):
            logging.exception(e)


def main():
    args = parse_args()
    kwargs = vars(args)

    with report_section("Software versions"):
        show_versions()

    with report_section("Project platform"):
        detect_platform(**kwargs)

    with report_section("Project compilation"):
        compile_project(**kwargs)

    # TODO other checks


if __name__ == "__main__":
    main()
