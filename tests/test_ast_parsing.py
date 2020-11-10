import errno
import json
import os
import subprocess
import sys
from collections import namedtuple
from distutils.version import StrictVersion
from typing import List, Dict

import pytest
from deepdiff import DeepDiff

from slither import Slither

# these solc versions only support legacy ast format
LEGACY_SOLC_VERS = [f"0.4.{v}" for v in range(12)]

SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_ROOT = os.path.join(SLITHER_ROOT, "tests", "ast-parsing")

# these are tests that are currently failing right now
XFAIL = [
    "for_0.4.0_legacy",
    "for_0.4.1_legacy",
    "for_0.4.2_legacy",
    "for_0.4.3_legacy",
    "for_0.4.4_legacy",
    "for_0.4.5_legacy",
    "for_0.4.6_legacy",
    "for_0.4.7_legacy",
    "for_0.4.8_legacy",
    "for_0.4.9_legacy",
    "for_0.4.10_legacy",
    "for_0.4.11_legacy",
    "for_0.4.12_legacy",
    "for_0.4.13_legacy",
    "for_0.4.14_legacy",
    "for_0.4.15_legacy",
    "for_0.4.16_legacy",
    "for_0.4.17_legacy",
    "for_0.4.18_legacy",
    "for_0.4.19_legacy",
    "for_0.4.20_legacy",
    "for_0.4.21_legacy",
    "for_0.4.22_legacy",
    "for_0.4.23_legacy",
    "for_0.4.24_legacy",
    "for_0.4.25_legacy",
    "for_0.4.26_legacy",
    "for_0.5.0_legacy",
    "for_0.5.1_legacy",
    "for_0.5.2_legacy",
    "for_0.5.3_legacy",
    "for_0.5.4_legacy",
    "for_0.5.5_legacy",
    "for_0.5.6_legacy",
    "for_0.5.7_legacy",
    "for_0.5.8_legacy",
    "for_0.5.9_legacy",
    "for_0.5.10_legacy",
    "for_0.5.11_legacy",
    "for_0.5.12_legacy",
    "for_0.5.13_legacy",
    "for_0.5.14_legacy",
    "for_0.5.15_legacy",
    "for_0.5.16_legacy",
    "for_0.5.17_legacy",
    "for_0.6.0_legacy",
    "for_0.6.1_legacy",
    "for_0.6.2_legacy",
    "for_0.6.3_legacy",
    "for_0.6.4_legacy",
    "for_0.6.5_legacy",
    "for_0.6.6_legacy",
    "for_0.6.7_legacy",
    "for_0.6.8_legacy",
    "for_0.6.9_legacy",
    "for_0.6.10_legacy",
    "for_0.6.11_legacy",
    "for_0.6.12_legacy",
    "for_0.7.0_legacy",
    "for_0.7.1_legacy",
    "for_0.7.2_legacy",
    "for_0.7.3_legacy",
    "for_0.7.4_legacy",
    "function_0.6.0_legacy",
    "function_0.6.1_legacy",
    "function_0.6.2_legacy",
    "function_0.6.3_legacy",
    "function_0.6.4_legacy",
    "function_0.6.5_legacy",
    "function_0.6.6_legacy",
    "function_0.6.7_legacy",
    "function_0.6.8_legacy",
    "function_0.6.9_legacy",
    "function_0.6.10_legacy",
    "function_0.6.11_legacy",
    "function_0.6.12_legacy",
    "function_0.7.0_legacy",
    "function_0.7.1_legacy",
    "function_0.7.1_compact",
    "function_0.7.2_legacy",
    "function_0.7.2_compact",
    "function_0.7.3_legacy",
    "function_0.7.3_compact",
    "function_0.7.4_legacy",
    "function_0.7.4_compact",
    "import_0.4.0_legacy",
    "import_0.4.1_legacy",
    "import_0.4.2_legacy",
    "import_0.4.3_legacy",
    "import_0.4.4_legacy",
    "import_0.4.5_legacy",
    "import_0.4.6_legacy",
    "import_0.4.7_legacy",
    "import_0.4.8_legacy",
    "import_0.4.9_legacy",
    "import_0.4.10_legacy",
    "import_0.4.11_legacy",
    "import_0.4.12_legacy",
    "import_0.4.12_compact",
    "import_0.4.13_legacy",
    "import_0.4.13_compact",
    "import_0.4.14_legacy",
    "import_0.4.14_compact",
    "import_0.4.15_legacy",
    "import_0.4.15_compact",
    "import_0.4.16_legacy",
    "import_0.4.16_compact",
    "import_0.4.17_legacy",
    "import_0.4.17_compact",
    "import_0.4.18_legacy",
    "import_0.4.18_compact",
    "import_0.4.19_legacy",
    "import_0.4.19_compact",
    "import_0.4.20_legacy",
    "import_0.4.20_compact",
    "import_0.4.21_legacy",
    "import_0.4.21_compact",
    "import_0.4.22_legacy",
    "import_0.4.22_compact",
    "import_0.4.23_legacy",
    "import_0.4.23_compact",
    "import_0.4.24_legacy",
    "import_0.4.24_compact",
    "import_0.4.25_legacy",
    "import_0.4.25_compact",
    "import_0.4.26_legacy",
    "import_0.4.26_compact",
    "import_0.5.0_legacy",
    "import_0.5.0_compact",
    "import_0.5.1_legacy",
    "import_0.5.1_compact",
    "import_0.5.2_legacy",
    "import_0.5.2_compact",
    "import_0.5.3_legacy",
    "import_0.5.3_compact",
    "import_0.5.4_legacy",
    "import_0.5.4_compact",
    "import_0.5.5_legacy",
    "import_0.5.5_compact",
    "import_0.5.6_legacy",
    "import_0.5.6_compact",
    "import_0.5.7_legacy",
    "import_0.5.7_compact",
    "import_0.5.8_legacy",
    "import_0.5.8_compact",
    "import_0.5.9_legacy",
    "import_0.5.9_compact",
    "import_0.5.10_legacy",
    "import_0.5.10_compact",
    "import_0.5.11_legacy",
    "import_0.5.11_compact",
    "import_0.5.12_legacy",
    "import_0.5.12_compact",
    "import_0.5.13_legacy",
    "import_0.5.13_compact",
    "import_0.5.14_legacy",
    "import_0.5.14_compact",
    "import_0.5.15_legacy",
    "import_0.5.15_compact",
    "import_0.5.16_legacy",
    "import_0.5.16_compact",
    "import_0.5.17_legacy",
    "import_0.5.17_compact",
    "import_0.6.0_legacy",
    "import_0.6.0_compact",
    "import_0.6.1_legacy",
    "import_0.6.1_compact",
    "import_0.6.2_legacy",
    "import_0.6.2_compact",
    "import_0.6.3_legacy",
    "import_0.6.3_compact",
    "import_0.6.4_legacy",
    "import_0.6.4_compact",
    "import_0.6.5_legacy",
    "import_0.6.5_compact",
    "import_0.6.6_legacy",
    "import_0.6.6_compact",
    "import_0.6.7_legacy",
    "import_0.6.7_compact",
    "import_0.6.8_legacy",
    "import_0.6.8_compact",
    "import_0.6.9_legacy",
    "import_0.6.9_compact",
    "import_0.6.10_legacy",
    "import_0.6.10_compact",
    "import_0.6.11_legacy",
    "import_0.6.11_compact",
    "import_0.6.12_legacy",
    "import_0.6.12_compact",
    "import_0.7.0_legacy",
    "import_0.7.0_compact",
    "import_0.7.1_legacy",
    "import_0.7.1_compact",
    "import_0.7.2_legacy",
    "import_0.7.2_compact",
    "import_0.7.3_legacy",
    "import_0.7.3_compact",
    "import_0.7.4_legacy",
    "import_0.7.4_compact",
    "indexrangeaccess_0.6.1_legacy",
    "indexrangeaccess_0.6.2_legacy",
    "indexrangeaccess_0.6.3_legacy",
    "indexrangeaccess_0.6.4_legacy",
    "indexrangeaccess_0.6.5_legacy",
    "indexrangeaccess_0.6.6_legacy",
    "indexrangeaccess_0.6.7_legacy",
    "indexrangeaccess_0.6.8_legacy",
    "indexrangeaccess_0.6.9_legacy",
    "indexrangeaccess_0.6.10_legacy",
    "indexrangeaccess_0.6.11_legacy",
    "indexrangeaccess_0.6.12_legacy",
    "indexrangeaccess_0.7.0_legacy",
    "indexrangeaccess_0.7.1_legacy",
    "indexrangeaccess_0.7.2_legacy",
    "indexrangeaccess_0.7.3_legacy",
    "indexrangeaccess_0.7.4_legacy",
    "literal_0.7.0_legacy",
    "literal_0.7.0_compact",
    "literal_0.7.1_legacy",
    "literal_0.7.1_compact",
    "literal_0.7.2_legacy",
    "literal_0.7.2_compact",
    "literal_0.7.3_legacy",
    "literal_0.7.3_compact",
    "literal_0.7.4_legacy",
    "literal_0.7.4_compact",
    "memberaccess_0.6.8_legacy",
    "memberaccess_0.6.9_legacy",
    "memberaccess_0.6.10_legacy",
    "memberaccess_0.6.11_legacy",
    "memberaccess_0.6.12_legacy",
    "memberaccess_0.7.0_legacy",
    "memberaccess_0.7.1_legacy",
    "memberaccess_0.7.2_legacy",
    "struct_0.6.0_legacy",
    "struct_0.6.1_legacy",
    "struct_0.6.2_legacy",
    "struct_0.6.3_legacy",
    "struct_0.6.4_legacy",
    "struct_0.6.5_legacy",
    "struct_0.6.6_legacy",
    "struct_0.6.7_legacy",
    "struct_0.6.8_legacy",
    "struct_0.6.9_legacy",
    "struct_0.6.10_legacy",
    "struct_0.6.11_legacy",
    "struct_0.6.12_legacy",
    "struct_0.7.0_legacy",
    "struct_0.7.1_legacy",
    "struct_0.7.2_legacy",
    "struct_0.7.3_legacy",
    "struct_0.7.4_legacy",
    "trycatch_0.6.0_legacy",
    "trycatch_0.6.1_legacy",
    "trycatch_0.6.2_legacy",
    "trycatch_0.6.3_legacy",
    "trycatch_0.6.4_legacy",
    "trycatch_0.6.5_legacy",
    "trycatch_0.6.6_legacy",
    "trycatch_0.6.7_legacy",
    "trycatch_0.6.8_legacy",
    "trycatch_0.6.9_legacy",
    "trycatch_0.6.10_legacy",
    "trycatch_0.6.11_legacy",
    "trycatch_0.6.12_legacy",
    "trycatch_0.7.0_legacy",
    "trycatch_0.7.1_legacy",
    "trycatch_0.7.2_legacy",
    "trycatch_0.7.3_legacy",
    "trycatch_0.7.4_legacy",
    "variable_0.6.5_legacy",
    "variable_0.6.5_compact",
    "variable_0.6.6_legacy",
    "variable_0.6.6_compact",
    "variable_0.6.7_legacy",
    "variable_0.6.7_compact",
    "variable_0.6.8_legacy",
    "variable_0.6.8_compact",
    "variable_0.6.9_legacy",
    "variable_0.6.9_compact",
    "variable_0.6.10_legacy",
    "variable_0.6.10_compact",
    "variable_0.6.11_legacy",
    "variable_0.6.11_compact",
    "variable_0.6.12_legacy",
    "variable_0.6.12_compact",
    "variable_0.7.0_legacy",
    "variable_0.7.0_compact",
    "variable_0.7.1_legacy",
    "variable_0.7.1_compact",
    "variabledeclaration_0.4.0_legacy",
    "variabledeclaration_0.4.1_legacy",
    "variabledeclaration_0.4.2_legacy",
    "variabledeclaration_0.4.3_legacy",
    "variabledeclaration_0.4.4_legacy",
    "variabledeclaration_0.4.5_legacy",
    "variabledeclaration_0.4.6_legacy",
    "variabledeclaration_0.4.7_legacy",
    "variabledeclaration_0.4.8_legacy",
    "variabledeclaration_0.4.9_legacy",
    "variabledeclaration_0.4.10_legacy",
    "variabledeclaration_0.4.11_legacy",
    "variabledeclaration_0.4.12_legacy",
    "variabledeclaration_0.4.12_compact",
    "variabledeclaration_0.4.13_legacy",
    "variabledeclaration_0.4.13_compact",
    "variabledeclaration_0.4.14_legacy",
    "variabledeclaration_0.4.14_compact",
    "variabledeclaration_0.4.15_legacy",
    "variabledeclaration_0.4.15_compact",
    "variabledeclaration_0.4.16_legacy",
    "variabledeclaration_0.4.16_compact",
    "variabledeclaration_0.4.17_legacy",
    "variabledeclaration_0.4.17_compact",
    "variabledeclaration_0.4.18_legacy",
    "variabledeclaration_0.4.18_compact",
    "variabledeclaration_0.4.19_legacy",
    "variabledeclaration_0.4.19_compact",
    "variabledeclaration_0.4.20_legacy",
    "variabledeclaration_0.4.20_compact",
    "variabledeclaration_0.4.21_legacy",
    "variabledeclaration_0.4.21_compact",
    "variabledeclaration_0.4.22_legacy",
    "variabledeclaration_0.4.22_compact",
    "variabledeclaration_0.4.23_legacy",
    "variabledeclaration_0.4.23_compact",
    "variabledeclaration_0.4.24_legacy",
    "variabledeclaration_0.4.24_compact",
    "variabledeclaration_0.4.25_legacy",
    "variabledeclaration_0.4.25_compact",
    "variabledeclaration_0.4.26_legacy",
    "variabledeclaration_0.4.26_compact",
    "variabledeclaration_0.5.0_legacy",
    "variabledeclaration_0.5.1_legacy",
    "variabledeclaration_0.5.2_legacy",
    "variabledeclaration_0.5.3_legacy",
    "variabledeclaration_0.5.4_legacy",
    "variabledeclaration_0.5.5_legacy",
    "variabledeclaration_0.5.6_legacy",
    "variabledeclaration_0.5.7_legacy",
    "variabledeclaration_0.5.8_legacy",
    "variabledeclaration_0.5.9_legacy",
    "variabledeclaration_0.5.10_legacy",
    "variabledeclaration_0.5.11_legacy",
    "variabledeclaration_0.5.12_legacy",
    "variabledeclaration_0.5.13_legacy",
    "variabledeclaration_0.5.14_legacy",
    "variabledeclaration_0.5.15_legacy",
    "variabledeclaration_0.5.16_legacy",
    "variabledeclaration_0.5.17_legacy",
    "variabledeclaration_0.6.0_legacy",
    "variabledeclaration_0.6.1_legacy",
    "variabledeclaration_0.6.2_legacy",
    "variabledeclaration_0.6.3_legacy",
    "variabledeclaration_0.6.4_legacy",
    "variabledeclaration_0.6.5_legacy",
    "variabledeclaration_0.6.6_legacy",
    "variabledeclaration_0.6.7_legacy",
    "variabledeclaration_0.6.8_legacy",
    "variabledeclaration_0.6.9_legacy",
    "variabledeclaration_0.6.10_legacy",
    "variabledeclaration_0.6.11_legacy",
    "variabledeclaration_0.6.12_legacy",
    "variabledeclaration_0.7.0_legacy",
    "variabledeclaration_0.7.1_legacy",
    "variabledeclaration_0.7.2_legacy",
    "variabledeclaration_0.7.3_legacy",
    "variabledeclaration_0.7.4_legacy",
]


def get_solc_versions() -> List[str]:
    """
    get a list of all the supported versions of solidity, sorted from earliest to latest
    :return: ascending list of versions, for example ["0.4.0", "0.4.1", ...]
    """
    result = subprocess.run(["solc", "--versions"], stdout=subprocess.PIPE, check=True)
    solc_versions = result.stdout.decode("utf-8").split("\n")

    # there's an extra newline so just remove all empty strings
    solc_versions = [version for version in solc_versions if version != ""]
    solc_versions.reverse()
    return solc_versions


def get_tests(solc_versions) -> Dict[str, List[str]]:
    """
    parse the list of testcases on disk
    :param solc_versions: the list of valid solidity versions
    :return: a dictionary of test id to list of base solidity versions supported
    """
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


Item = namedtuple("TestItem", ["test_id", "base_ver", "solc_ver", "is_legacy",],)


def get_all_test() -> List[Item]:
    """
    generate a list of testcases by testing each test id with every solidity version for both legacy and compact ast
    :return: the testcases
    """
    solc_versions = get_solc_versions()
    tests = get_tests(solc_versions)

    ret = []

    for test, base_vers in tests.items():
        print(f"generating testcases id={test} vers={base_vers}")

        base_ver_idx = 0

        for solc_ver in solc_versions:
            # if it's time to move to the next base version, do it now
            if base_ver_idx + 1 < len(base_vers) and base_vers[base_ver_idx + 1] == solc_ver:
                base_ver_idx += 1

            for legacy_json in [True, False]:
                if not legacy_json and solc_ver in LEGACY_SOLC_VERS:
                    continue

                ret.append(
                    Item(
                        test_id=test,
                        base_ver=base_vers[base_ver_idx],
                        solc_ver=solc_ver,
                        is_legacy=legacy_json,
                    )
                )
    return ret


def id_test(test_item: Item):
    flavor = "legacy" if test_item.is_legacy else "compact"
    return f"{test_item.test_id}_{test_item.solc_ver}_{flavor}"


def generate_output(sl: Slither) -> Dict[str, Dict[str, str]]:
    output = {}
    for contract in sl.contracts:
        output[contract.name] = {}

        for func_or_modifier in contract.functions + contract.modifiers:
            output[contract.name][
                func_or_modifier.full_name
            ] = func_or_modifier.slithir_cfg_to_dot_str(skip_expressions=True)

    return output


ALL_TESTS = get_all_test()


def set_solc(test_item: Item):
    # hacky hack hack to pick the solc version we want
    env = dict(os.environ)
    env["SOLC_VERSION"] = test_item.solc_ver
    os.environ.clear()
    os.environ.update(env)


@pytest.mark.parametrize("test_item", ALL_TESTS, ids=id_test)
def test_parsing(test_item: Item):
    flavor = "legacy" if test_item.is_legacy else "compact"
    test_file = os.path.join(TEST_ROOT, f"{test_item.test_id}-{test_item.base_ver}.sol")
    expected_file = os.path.join(
        TEST_ROOT, "expected", f"{test_item.test_id}-{test_item.solc_ver}-{flavor}.json"
    )

    if id_test(test_item) in XFAIL:
        pytest.xfail("this test needs to be fixed")

    set_solc(test_item)

    sl = Slither(
        test_file,
        solc_force_legacy_json=test_item.is_legacy,
        disallow_partial=True,
        skip_analyze=True,
    )

    actual = generate_output(sl)

    try:
        with open(expected_file, "r") as f:
            expected = json.load(f)
    except OSError as e:
        pytest.xfail("the file for this test was not generated")
        raise

    diff = DeepDiff(expected, actual, ignore_order=True, verbose_level=2)

    assert not diff, diff.pretty()


def _generate_test(test_item: Item, skip_existing=False):
    flavor = "legacy" if test_item.is_legacy else "compact"
    test_file = os.path.join(TEST_ROOT, f"{test_item.test_id}-{test_item.base_ver}.sol")
    expected_file = os.path.join(
        TEST_ROOT, "expected", f"{test_item.test_id}-{test_item.solc_ver}-{flavor}.json"
    )

    if skip_existing:
        if os.path.isfile(expected_file):
            return

    if id_test(test_item) in XFAIL:
        return

    set_solc(test_item)

    sl = Slither(
        test_file,
        solc_force_legacy_json=test_item.is_legacy,
        disallow_partial=True,
        skip_analyze=True,
    )

    actual = generate_output(sl)

    with open(expected_file, "w") as f:
        json.dump(actual, f, ident="  ")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["--generate", "--overwrite"]:
        print("To generate the missing json artifacts run\n\tpython tests/test_ast_parsing.py --generate")
        print("To re-generate all the json artifacts run\n\tpython tests/test_ast_parsing.py --overwrite")
        print("\tThis will overwrite the previous json files")
    elif sys.argv[1] == "--generate":
        for test in ALL_TESTS:
            _generate_test(test, skip_existing=True)
    elif sys.argv[1] == "--overwrite":
        for test in ALL_TESTS:
            _generate_test(test)
