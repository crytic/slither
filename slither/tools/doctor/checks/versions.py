from importlib import metadata
import json
from typing import Optional, Any
import urllib

from packaging.version import parse, Version

from slither.utils.colors import yellow, green


def get_installed_version(name: str) -> Optional[Version]:
    try:
        return parse(metadata.version(name))
    except metadata.PackageNotFoundError:
        return None


def get_github_version(name: str) -> Optional[Version]:
    try:
        # type: ignore
        with urllib.request.urlopen(
            f"https://api.github.com/repos/crytic/{name}/releases/latest"
        ) as response:
            text = response.read()
            data = json.loads(text)
            return parse(data["tag_name"])
    except:  # pylint: disable=bare-except
        return None


def show_versions(**_kwargs: Any) -> None:
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
        print(
            f"{name + ':':<16}{color(str(installed) or 'N/A'):<16} (latest is {str(latest) or 'Unknown'})"
        )

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
