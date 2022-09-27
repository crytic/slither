from importlib import metadata
import json
from typing import Optional
from packaging.version import parse, LegacyVersion, Version
import urllib


def get_installed_version(name: str) -> Optional[LegacyVersion | Version]:
    try:
        return parse(metadata.version(name))
    except metadata.PackageNotFoundError:
        return None


def get_github_version(name: str) -> Optional[LegacyVersion | Version]:
    try:
        with urllib.request.urlopen(
            f"https://api.github.com/repos/crytic/{name}/releases/latest"
        ) as response:
            text = response.read()
            data = json.loads(text)
            return parse(data["tag_name"])
    except:
        return None
