import errno
import json
import os
import subprocess
from collections import namedtuple
from distutils.version import StrictVersion
from typing import List, Dict

import pytest
from deepdiff import DeepDiff

from slither import Slither

LEGACY_SOLC_VERS = [f"0.4.{v}" for v in range(12)]


def get_solc_versions() -> List[str]:
    result = subprocess.run(["solc", "--versions"], stdout=subprocess.PIPE, check=True)
    solc_versions = result.stdout.decode("utf-8").split("\n")

    # remove empty strings if any
    solc_versions = [version for version in solc_versions if version != ""]
    solc_versions.reverse()
    return solc_versions


def get_tests(solc_versions) -> Dict[str, List[str]]:
    slither_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(slither_root, "tests", "ast-parsing")

    tests: Dict[str, List[str]] = {}

    for name in os.listdir(test_dir):
        if not name.endswith(".sol"):
            continue

        test_name, test_ver = name[:-4].rsplit("-", 1)

        if test_name not in tests:
            tests[test_name] = []

        tests[test_name].append(test_ver)

    for key in tests:
        if len(tests[key]) > 1:
            tests[key] = sorted(tests[key], key=StrictVersion)

    # validate tests
    for test, vers in tests.items():
        if len(vers) == 1:
            if vers[0] != "all":
                raise Exception("only one test found but not called all", test)
        else:
            for ver in vers:
                if ver not in solc_versions:
                    raise Exception("base version not found", test, ver)

    return tests

TestItem = namedtuple("TestItem",
                      ["solc_version",
                       "is_legacy",
                       "test_file",
                       "expected_file"])

def get_all_test() -> List[TestItem]:

    solc_versions = get_solc_versions()
    tests = get_tests(solc_versions)

    slither_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_dir = os.path.join(slither_root, "tests", "ast-parsing")

    ret = []

    for test, vers in tests.items():
        print("running test", test, vers)

        ver_idx = 0

        for ver in solc_versions:
            if ver_idx + 1 < len(vers) and vers[ver_idx + 1] == ver:
                ver_idx += 1

            test_file = os.path.join(test_dir, f"{test}-{vers[ver_idx]}.sol")


            for legacy_json in [True, False]:
                if not legacy_json and ver in LEGACY_SOLC_VERS:
                    continue

                flavor = "legacy" if legacy_json else "compact"
                expected_file = os.path.join(test_dir, "expected", f"{test}-{ver}-{flavor}.json")

                ret.append(TestItem(solc_version=ver,
                                    is_legacy=legacy_json,
                                    test_file=test_file,
                                    expected_file=expected_file))
    return ret

def id_test(test_item: TestItem):
    return test_item.test_file + "_" + str(test_item.is_legacy) + "_" + test_item.solc_version + "_"

ALL_TESTS = get_all_test()

@pytest.mark.parametrize("test_item", ALL_TESTS, ids=id_test)
def test_parsing(test_item: TestItem):

    env = dict(os.environ)
    env["SOLC_VERSION"] = test_item.solc_version
    os.environ.clear()
    os.environ.update(env)

    sl = Slither(test_item.test_file,
            solc_force_legacy_json=test_item.is_legacy,
            disallow_partial=True,
            skip_analyze=True)

    actual = {}
    for contract in sl.contracts:
        actual[contract.name] = {}

        for func_or_modifier in contract.functions + contract.modifiers:
            actual[contract.name][
                func_or_modifier.full_name
            ] = func_or_modifier.slithir_cfg_to_dot_str(skip_expressions=True)

    try:
        with open(test_item.expected_file, "r") as f:
            expected = json.load(f)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

        with open(test_item.expected_file, "w") as f:
            json.dump(actual, f, indent="  ")
            expected = actual

    diff = DeepDiff(expected, actual, ignore_order=True, verbose_level=2)

    assert not diff

