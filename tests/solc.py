import subprocess
from typing import List


def get_solc_versions() -> List[str]:
    """
    get a list of all the supported versions of solidity, sorted from earliest to latest
    :return: ascending list of versions, for example ["0.4.0", "0.4.1", ...]
    """
    result = subprocess.run(["solc-select", "versions"], stdout=subprocess.PIPE, check=True)
    solc_versions = result.stdout.decode("utf-8").split("\n")

    # there's an extra newline so just remove all empty strings
    solc_versions = [version.split(" ")[0] for version in solc_versions if version != ""]

    solc_versions = sorted(solc_versions, key=lambda x: list(map(int, x.split("."))))
    return solc_versions


def install_solc_version(solc_version: str):
    """
    install solc version using solc-select
    :param solc_version: solc version to be installed, for example "0.8.7"
    """
    try:
        subprocess.run(["solc-select", "install", solc_version], stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(
            "Failed to install solc version", solc_version, e.stderr.decode("utf-8")
        ) from e
