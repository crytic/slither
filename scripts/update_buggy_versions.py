import json
from pathlib import Path
import urllib.request


def retrieve_json(url):
    with urllib.request.urlopen(url) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)


def organize_data(json_data):
    version_bugs = {}
    for version, info in json_data.items():
        version_bugs[version] = info["bugs"]
    return version_bugs


if __name__ == "__main__":
    bug_list_url = (
        "https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs_by_version.json"
    )
    bug_data = retrieve_json(bug_list_url)
    bugs_by_version = organize_data(bug_data)

    with open(Path.cwd() / Path("slither/utils/buggy_versions.py"), "w", encoding="utf-8") as file:
        file.write("# pylint: disable=too-many-lines\n")
        file.write(f"bugs_by_version = {bugs_by_version}")
