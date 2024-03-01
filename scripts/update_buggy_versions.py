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
    url = "https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs_by_version.json"
    json_data = retrieve_json(url)
    version_bugs = organize_data(json_data)

    with open(Path.cwd() / Path("slither/utils/buggy_versions.py"), "w") as file:
        file.write(f"bugs_by_version = {version_bugs}")
