import os
import json
import re

from solc_select import solc_select
from deepdiff import DeepDiff

from slither import Slither
from slither.core.declarations import Function
from slither.core.variables import StateVariable
from slither.utils.upgradeability import compare

SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPGRADE_TEST_ROOT = os.path.join(SLITHER_ROOT, "tests", "upgradeability-util")


# pylint: disable=too-many-locals
def test_upgrades_compare() -> None:
    solc_select.switch_global_version("0.8.2", always_install=True)

    sl = Slither(os.path.join(UPGRADE_TEST_ROOT, "TestUpgrades.sol"))
    v1 = sl.get_contract_from_name("ContractV1")[0]
    v2 = sl.get_contract_from_name("ContractV2")[0]
    diff = compare(v1, v2)
    for key, lst in diff.items():
        if len(lst) > 0:
            print(f'      * {str(key).replace("-", " ")}:')
            for obj in lst:
                if isinstance(obj, StateVariable):
                    print(f"          * {obj.full_name}")
                elif isinstance(obj, Function):
                    print(f"          * {obj.signature_str}")
    with open("upgrade_diff.json", "w", encoding="utf-8") as file:
        json_str = diff_to_json_str(diff)
        diff_json = json.loads(json_str)
        json.dump(diff_json, file, indent=4)

    expected_file = os.path.join(UPGRADE_TEST_ROOT, "TEST_upgrade_diff.json")
    actual_file = os.path.join(SLITHER_ROOT, "upgrade_diff.json")

    with open(expected_file, "r", encoding="utf8") as f:
        expected = json.load(f)
    with open(actual_file, "r", encoding="utf8") as f:
        actual = json.load(f)

    diff = DeepDiff(expected, actual, ignore_order=True, verbose_level=2, view="tree")
    if diff:
        for change in diff.get("values_changed", []):
            path_list = re.findall(r"\['(.*?)'\]", change.path())
            path = "_".join(path_list)
            with open(f"{path}_expected.txt", "w", encoding="utf8") as f:
                f.write(str(change.t1))
            with open(f"{path}_actual.txt", "w", encoding="utf8") as f:
                f.write(str(change.t2))

    assert not diff


def diff_to_json_str(diff: dict) -> str:
    out: dict = {}
    for key in diff.keys():
        out[key] = []
        for obj in diff[key]:
            if isinstance(obj, StateVariable):
                out[key].append(obj.canonical_name)
            elif isinstance(obj, Function):
                out[key].append(obj.signature_str)
    return str(out).replace("'", '"')
