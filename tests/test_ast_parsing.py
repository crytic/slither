import json
import os
import re
import subprocess
import sys
from collections import namedtuple
from distutils.version import StrictVersion
from typing import List, Dict
from deepdiff import DeepDiff

import pytest
from crytic_compile import CryticCompile, save_to_zip
from crytic_compile.utils.zip import load_from_zip

from slither import Slither
from slither.printers.guidance.echidna import Echidna

# these solc versions only support legacy ast format

LEGACY_SOLC_VERS = [f"0.4.{v}" for v in range(12)]

SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_ROOT = os.path.join(SLITHER_ROOT, "tests", "ast-parsing")

ALL_04 = range(0, 27)
ALL_05 = range(0, 18)
ALL_06 = range(0, 13)
ALL_07 = range(0, 7)
ALL_08 = range(0, 13)

# these are tests that are currently failing right now
XFAIL = (
    [f"emit_0.4.{ver}_legacy" for ver in ALL_04]
    + [f"emit_0.4.{ver}_compact" for ver in range(12, 27)]
    + [f"function_0.6.{ver}_legacy" for ver in ALL_06]
    + [f"function_0.7.{ver}_legacy" for ver in ALL_07]
    + [f"function_0.7.{ver}_compact" for ver in range(1, 7)]
    + [f"import_0.4.{ver}_legacy" for ver in ALL_04]
    + [f"import_0.4.{ver}_compact" for ver in range(12, 27)]
    + [f"import_0.5.{ver}_legacy" for ver in ALL_05]
    + [f"import_0.5.{ver}_compact" for ver in ALL_05]
    + [f"import_0.6.{ver}_legacy" for ver in ALL_06]
    + [f"import_0.6.{ver}_compact" for ver in ALL_06]
    + [f"import_0.7.{ver}_legacy" for ver in ALL_07]
    + [f"import_0.7.{ver}_compact" for ver in ALL_07]
    + [f"import_0.8.{ver}_compact" for ver in ALL_08]
    + [f"indexrangeaccess_0.6.{ver}_legacy" for ver in range(1, 13)]
    + [f"indexrangeaccess_0.7.{ver}_legacy" for ver in ALL_07]
    + [f"literal_0.7.{ver}_legacy" for ver in ALL_07]
    + [f"literal_0.8.{ver}_legacy" for ver in ALL_08]
    + [f"literal_0.7.{ver}_compact" for ver in ALL_07]
    + [f"literal_0.8.{ver}_compact" for ver in ALL_08]
    + [f"memberaccess_0.6.{ver}_legacy" for ver in range(8, 13)]
    + [f"memberaccess_0.7.{ver}_legacy" for ver in range(0, 3)]
    + [f"struct_0.6.{ver}_legacy" for ver in ALL_06]
    + [f"struct_0.7.{ver}_legacy" for ver in ALL_07]
    + [f"struct_0.8.{ver}_legacy" for ver in ALL_08]
    + [f"trycatch_0.6.{ver}_legacy" for ver in ALL_06]
    + [f"trycatch_0.7.{ver}_legacy" for ver in ALL_07]
    + [f"variable_0.6.{ver}_legacy" for ver in range(5, 23)]
    + [f"variable_0.6.{ver}_compact" for ver in range(5, 23)]
    + [f"variable_0.7.{ver}_legacy" for ver in range(0, 2)]
    + [f"variable_0.7.{ver}_compact" for ver in range(0, 2)]
    + [f"variabledeclaration_0.4.{ver}_legacy" for ver in ALL_04]
    + [f"variabledeclaration_0.5.{ver}_legacy" for ver in ALL_05]
    + [f"variabledeclaration_0.6.{ver}_legacy" for ver in ALL_06]
    + [f"variabledeclaration_0.7.{ver}_legacy" for ver in ALL_07]
    + [f"variabledeclaration_0.8.{ver}_legacy" for ver in ALL_08]
    + [f"variabledeclaration_0.4.{ver}_compact" for ver in range(12, 27)]
)


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

    for key, test in tests.items():
        if len(test) > 1:
            tests[key] = sorted(test, key=StrictVersion)

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


Item = namedtuple(
    "TestItem",
    [
        "test_id",
        "base_ver",
        "solc_ver",
        "is_legacy",
    ],
)


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

                if legacy_json and solc_ver > "0.8":
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

# create the output folder if needed
try:
    os.mkdir("test_artifacts")
except OSError:
    pass


def set_solc(test_item: Item):
    subprocess.run(["solc-select", "use", test_item.solc_ver], stdout=subprocess.PIPE, check=True)


@pytest.mark.parametrize("test_item", ALL_TESTS, ids=id_test)
def test_parsing(test_item: Item):
    flavor = "legacy" if test_item.is_legacy else "compact"
    test_file = os.path.join(
        TEST_ROOT, "compile", f"{test_item.test_id}-{test_item.solc_ver}-{flavor}.zip"
    )
    expected_file = os.path.join(
        TEST_ROOT, "expected", f"{test_item.test_id}-{test_item.solc_ver}-{flavor}.json"
    )

    if id_test(test_item) in XFAIL:
        pytest.xfail("this test needs to be fixed")

    # set_solc(test_item)

    cc = load_from_zip(test_file)[0]

    sl = Slither(
        cc,
        solc_force_legacy_json=test_item.is_legacy,
        disallow_partial=True,
        skip_analyze=True,
    )

    actual = generate_output(sl)

    try:
        with open(expected_file, "r", encoding="utf8") as f:
            expected = json.load(f)
    except OSError:
        pytest.xfail("the file for this test was not generated")
        raise

    diff = DeepDiff(expected, actual, ignore_order=True, verbose_level=2, view="tree")

    if diff:
        for change in diff.get("values_changed", []):
            path_list = re.findall(r"\['(.*?)'\]", change.path())
            path = "_".join(path_list)
            with open(
                f"test_artifacts/{id_test(test_item)}_{path}_expected.dot", "w", encoding="utf8"
            ) as f:
                f.write(change.t1)
            with open(
                f"test_artifacts/{id_test(test_item)}_{path}_actual.dot", "w", encoding="utf8"
            ) as f:
                f.write(change.t2)

    assert not diff, diff.pretty()

    sl = Slither(cc, solc_force_legacy_json=test_item.is_legacy, disallow_partial=True)
    sl.register_printer(Echidna)
    sl.run_printers()


def _generate_test(test_item: Item, skip_existing=False):
    flavor = "legacy" if test_item.is_legacy else "compact"
    test_file = os.path.join(
        TEST_ROOT, "compile", f"{test_item.test_id}-{test_item.solc_ver}-{flavor}.zip"
    )
    expected_file = os.path.join(
        TEST_ROOT, "expected", f"{test_item.test_id}-{test_item.solc_ver}-{flavor}.json"
    )

    if expected_file in XFAIL:
        return
    if skip_existing:
        if os.path.isfile(expected_file):
            return
    if id_test(test_item) in XFAIL:
        return
    # set_solc(test_item)
    try:
        cc = load_from_zip(test_file)[0]
        sl = Slither(
            cc,
            solc_force_legacy_json=test_item.is_legacy,
            disallow_partial=True,
            skip_analyze=True,
        )
    # pylint: disable=broad-except
    except Exception as e:
        print(e)
        print(test_item)
        print(f"{expected_file} failed")
        return

    actual = generate_output(sl)
    print(f"Generate {expected_file}")
    with open(expected_file, "w", encoding="utf8") as f:
        json.dump(actual, f, indent="  ")


def _generate_compile(test_item: Item, skip_existing=False):
    flavor = "legacy" if test_item.is_legacy else "compact"
    test_file = os.path.join(TEST_ROOT, f"{test_item.test_id}-{test_item.base_ver}.sol")
    expected_file = os.path.join(
        TEST_ROOT, "compile", f"{test_item.test_id}-{test_item.solc_ver}-{flavor}.zip"
    )

    if skip_existing:
        if os.path.isfile(expected_file):
            return

    set_solc(test_item)

    cc = CryticCompile(test_file, solc_force_legacy_json=test_item.is_legacy)
    print(f"Compiled to {expected_file}")
    save_to_zip([cc], expected_file)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["--generate", "--overwrite", "--compile"]:
        print(
            "To generate the missing json artifacts run\n\tpython tests/test_ast_parsing.py --generate"
        )
        print(
            "To re-generate all the json artifacts run\n\tpython tests/test_ast_parsing.py --overwrite"
        )
        print("To compile json artifacts run\n\tpython tests/test_ast_parsing.py --compile")
        print("\tThis will overwrite the previous json files")
    elif sys.argv[1] == "--generate":
        for next_test in ALL_TESTS:
            _generate_test(next_test, skip_existing=True)
    elif sys.argv[1] == "--overwrite":
        for next_test in ALL_TESTS:
            _generate_test(next_test)
    elif sys.argv[1] == "--compile":
        for next_test in ALL_TESTS:
            _generate_compile(next_test, skip_existing=True)
