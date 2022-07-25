import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

import pytest
from deepdiff import DeepDiff
from solc_select.solc_select import install_artifacts as install_solc_versions
from solc_select.solc_select import installed_versions as get_installed_solc_versions
from crytic_compile import CryticCompile, save_to_zip
from crytic_compile.utils.zip import load_from_zip


from slither import Slither
from slither.printers.guidance.echidna import Echidna

SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_ROOT = os.path.join(SLITHER_ROOT, "tests", "ast-parsing")

# pylint: disable=too-few-public-methods
class Test:
    def __init__(self, test_file: str, solc_versions: List[str], disable_legacy: bool = False):
        self.solc_versions = solc_versions
        self.test_file = test_file
        self.disable_legacy = disable_legacy

        versions_with_flavors: List[Tuple[str, str]] = []
        flavors = ["compact"]
        if not self.disable_legacy:
            flavors += ["legacy"]
        for version in solc_versions:
            for flavor in flavors:
                if flavor == "legacy" and version > "0.8":
                    # No legacy for >0.8
                    continue
                versions_with_flavors.append((version, flavor))
        self.versions_with_flavors = versions_with_flavors


def generate_output(sl: Slither) -> Dict[str, Dict[str, str]]:
    output = {}
    for contract in sl.contracts:
        output[contract.name] = {}

        for func_or_modifier in contract.functions + contract.modifiers:
            output[contract.name][
                func_or_modifier.full_name
            ] = func_or_modifier.slithir_cfg_to_dot_str(skip_expressions=True)

    return output


def make_version(minor: int, patch_min: int, patch_max: int) -> List[str]:
    return [f"0.{minor}.{x}" for x in range(patch_min, patch_max + 1)]


VERSIONS_04 = make_version(4, 0, 26)
VERSIONS_05 = make_version(5, 0, 17)
VERSIONS_06 = make_version(6, 0, 12)
VERSIONS_07 = make_version(7, 0, 6)
VERSIONS_08 = make_version(8, 0, 15)

ALL_VERSIONS = VERSIONS_04 + VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08

ALL_TESTS = [
    Test("using-for-0.4.0.sol", ["0.4.0"]),
    Test(
        "using-for-0.4.1.sol",
        make_version(4, 1, 26) + VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
    ),
    Test(
        "top-level-import-0.4.0.sol",
        VERSIONS_04 + VERSIONS_05 + VERSIONS_06 + ["0.7.0"],
    ),
    Test("top-level-import-0.7.1.sol", make_version(7, 1, 6) + VERSIONS_08),
    Test("function-0.4.0.sol", make_version(4, 0, 15)),
    Test("function-0.4.16.sol", make_version(4, 16, 21)),
    Test("function-0.4.22.sol", ["0.4.22"]),
    Test("function-0.4.23.sol", make_version(4, 23, 26)),
    Test("function-0.5.0.sol", VERSIONS_05),
    # TODO: legacy is failing
    Test("function-0.6.0.sol", VERSIONS_06, disable_legacy=True),
    # TODO: failing
    # Test("function-0.7.0.sol", ["0.7.0"]),
    # TODO: legacy failing with 0.7
    Test("function-0.7.1.sol", make_version(7, 1, 6), disable_legacy=True),
    Test("function-0.7.1.sol", VERSIONS_08),
    Test(
        "top-level-import-bis-0.4.0.sol",
        VERSIONS_04 + VERSIONS_05 + VERSIONS_06 + ["0.7.0"],
    ),
    Test("top-level-import-bis-0.7.1.sol", make_version(7, 1, 6) + VERSIONS_08),
    # TODO: failing
    # Test(
    #     "variabledeclaration-0.4.0.sol",
    #     make_version(4, 0, 23),
    #     disable_legacy=True,
    # ),
    # # TODO: failing
    # Test(
    #     "variabledeclaration-0.4.24.sol",
    #     make_version(4, 24, 26),
    #     disable_legacy=True,
    # ),
    Test(
        "variabledeclaration-0.5.0.sol",
        VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
        disable_legacy=True,
    ),
    Test("functioncall-0.4.0.sol", VERSIONS_04),
    Test(
        "functioncall-0.4.5.sol",
        make_version(4, 5, 9),
    ),
    Test(
        "functioncall-0.5.0.sol",
        make_version(5, 0, 2),
    ),
    Test(
        "functioncall-0.5.3.sol",
        make_version(5, 3, 17),
    ),
    Test(
        "functioncall-0.6.0.sol",
        make_version(6, 0, 1),
    ),
    Test(
        "functioncall-0.6.2.sol",
        make_version(6, 2, 7),
    ),
    Test(
        "functioncall-0.6.8.sol",
        make_version(6, 8, 12),
    ),
    Test(
        "functioncall-0.7.0.sol",
        VERSIONS_07,
    ),
    Test(
        "functioncall-0.8.0.sol",
        VERSIONS_08,
    ),
    Test(
        "break-all.sol",
        ALL_VERSIONS,
    ),
    Test(
        "top-level-nested-import-0.4.0.sol",
        VERSIONS_04 + VERSIONS_05 + VERSIONS_06 + ["0.7.0"],
    ),
    Test(
        "top-level-nested-import-0.7.1.sol",
        make_version(7, 1, 6) + VERSIONS_08,
    ),
    # + [f"variable_0.6.{ver}_legacy" for ver in range(5, 23)]
    # + [f"variable_0.6.{ver}_compact" for ver in range(5, 23)]
    # + [f"variable_0.7.{ver}_legacy" for ver in range(0, 2)]
    # + [f"variable_0.7.{ver}_compact" for ver in range(0, 2)]
    Test(
        "call_to_variable-all.sol",
        ALL_VERSIONS,
    ),
    Test("yul-0.4.0.sol", ["0.4.0"]),
    Test("yul-0.4.1.sol", make_version(4, 1, 10)),
    Test(
        "yul-0.4.11.sol",
        make_version(4, 11, 26) + VERSIONS_05 + VERSIONS_06,
    ),
    Test("yul-0.7.0.sol", make_version(7, 0, 4)),
    Test("yul-0.7.5.sol", make_version(7, 5, 6)),
    Test("yul-0.8.0.sol", VERSIONS_08),
    Test("pragma-0.4.0.sol", VERSIONS_04),
    Test("pragma-0.5.0.sol", VERSIONS_05),
    Test("pragma-0.6.0.sol", VERSIONS_06),
    Test("pragma-0.7.0.sol", VERSIONS_07),
    Test("pragma-0.8.0.sol", VERSIONS_08),
    Test(
        "assembly-all.sol",
        ALL_VERSIONS,
    ),
    Test("struct-0.4.0.sol", VERSIONS_04 + VERSIONS_05),
    # TODO: legacy failing
    Test(
        "struct-0.6.0.sol",
        VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
        disable_legacy=True,
    ),
    # TODO: currently failing
    # Test("emit-0.4.0.sol", VERSIONS_04),
    # Test(
    #     "emit-0.4.8.sol",
    #     make_version(4, 8, 20)
    # ),
    # Test(
    #     "emit-0.4.21.sol",
    #     make_version(4, 21, 26)
    # ),
    Test(
        "emit-0.5.0.sol",
        VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
    ),
    # TODO: failing
    # Test("import-0.4.0.sol", VERSIONS_04),
    # Test(
    #     "import-0.4.3.sol",
    #     make_version(4, 3, 9) + VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
    # ),
    Test("tupleexpression-0.4.0.sol", make_version(4, 0, 23)),
    Test("tupleexpression-0.4.24.sol", make_version(4, 24, 26) + VERSIONS_05),
    Test(
        "tupleexpression-0.5.3.sol",
        make_version(5, 3, 9) + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
    ),
    Test("literal-0.4.0.sol", make_version(4, 0, 9)),
    Test("literal-0.4.10.sol", make_version(4, 10, 26)),
    Test("literal-0.5.0.sol", VERSIONS_05),
    Test("literal-0.6.0.sol", VERSIONS_06),
    # TODO: failing
    # Test("literal-0.7.0.sol", VERSIONS_07 + VERSIONS_08),
    Test("memberaccess-0.4.0.sol", VERSIONS_04 + VERSIONS_05),
    Test(
        "memberaccess-0.5.3.sol",
        make_version(5, 3, 9),
    ),
    # TODO:  Legacy failing from 0.6
    Test(
        "memberaccess-0.5.3.sol",
        VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
        disable_legacy=True,
    ),
    Test("throw-0.4.0.sol", VERSIONS_04),
    Test(
        "throw-0.5.0.sol",
        VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
    ),
    Test(
        "top_level_variable2-0.4.0.sol",
        VERSIONS_04 + VERSIONS_05 + VERSIONS_06 + VERSIONS_07,
    ),
    Test("top_level_variable2-0.8.0.sol", VERSIONS_08),
    Test(
        "comment-all.sol",
        ALL_VERSIONS,
    ),
    Test("assignment-0.4.0.sol", VERSIONS_04),
    Test(
        "assignment-0.4.7.sol",
        make_version(4, 7, 9) + VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
    ),
    Test(
        "event-all.sol",
        ALL_VERSIONS,
    ),
    # TODO: legacy not working
    Test(
        "indexrangeaccess-0.4.0.sol",
        VERSIONS_04 + VERSIONS_05 + ["0.6.0"],
    ),
    Test("indexrangeaccess-0.4.0.sol", ["0.6.0"], disable_legacy=True),
    Test(
        "indexrangeaccess-0.6.1.sol",
        make_version(6, 1, 12) + VERSIONS_07 + VERSIONS_08,
        disable_legacy=True,
    ),
    Test("variable-0.4.0.sol", VERSIONS_04),
    Test("variable-0.4.5.sol", make_version(4, 5, 13)),
    Test("variable-0.4.14.sol", make_version(4, 14, 15)),
    Test("variable-0.4.16.sol", make_version(4, 16, 26)),
    Test("variable-0.5.0.sol", VERSIONS_05 + make_version(6, 0, 4)),
    Test("variable-0.6.5.sol", make_version(6, 5, 8)),
    Test("variable-0.6.9.sol", make_version(6, 9, 12) + VERSIONS_07),
    Test("variable-0.8.0.sol", VERSIONS_08),
    Test(
        "continue-all.sol",
        ALL_VERSIONS,
    ),
    Test(
        "if-all.sol",
        ALL_VERSIONS,
    ),
    Test(
        "modifier-all.sol",
        ALL_VERSIONS,
    ),
    Test("library_implicit_conversion-0.4.0.sol", VERSIONS_04),
    Test(
        "library_implicit_conversion-0.5.0.sol",
        VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
    ),
    Test("units_and_global_variables-0.4.0.sol", VERSIONS_04),
    Test("units_and_global_variables-0.5.0.sol", make_version(5, 0, 3)),
    Test("units_and_global_variables-0.5.4.sol", make_version(5, 4, 17)),
    Test("units_and_global_variables-0.6.0.sol", VERSIONS_06),
    Test("units_and_global_variables-0.7.0.sol", VERSIONS_07),
    Test("units_and_global_variables-0.8.0.sol", VERSIONS_08),
    Test("units_and_global_variables-0.8.4.sol", make_version(8, 4, 6)),
    Test("units_and_global_variables-0.8.7.sol", make_version(8, 7, 9)),
    Test(
        "push-all.sol",
        ALL_VERSIONS,
    ),
    Test(
        "indexaccess-all.sol",
        ALL_VERSIONS,
    ),
    Test("minmax-0.4.0.sol", VERSIONS_04 + VERSIONS_05 + VERSIONS_06),
    Test(
        "minmax-0.6.8.sol",
        make_version(6, 8, 9) + VERSIONS_07 + VERSIONS_08,
    ),
    Test(
        "minmax-0.8.8.sol",
        make_version(8, 8, 15),
    ),
    Test("dowhile-0.4.0.sol", VERSIONS_04),
    Test(
        "dowhile-0.4.5.sol",
        make_version(4, 5, 9) + VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
    ),
    Test(
        "custom_error-0.4.0.sol",
        ALL_VERSIONS,
    ),
    Test("custom_error-0.8.4.sol", make_version(8, 4, 9)),
    Test(
        "top-level-0.4.0.sol",
        VERSIONS_04 + VERSIONS_05 + VERSIONS_06 + ["0.7.0"],
    ),
    Test("top-level-0.7.1.sol", make_version(7, 1, 3)),
    Test("top-level-0.7.4.sol", make_version(7, 4, 6) + VERSIONS_08),
    Test("contract-0.4.0.sol", make_version(4, 0, 21)),
    Test("contract-0.4.22.sol", make_version(4, 22, 26) + VERSIONS_05),
    Test("contract-0.6.0.sol", VERSIONS_06 + VERSIONS_07 + VERSIONS_08),
    Test(
        "import_interface_with_struct_from_top_level-0.4.0.sol",
        VERSIONS_04 + VERSIONS_05 + VERSIONS_06 + make_version(7, 0, 5),
    ),
    Test(
        "import_interface_with_struct_from_top_level-0.7.6.sol",
        ["0.7.6"] + VERSIONS_08,
    ),
    Test("scope-0.4.0.sol", VERSIONS_04),
    Test(
        "scope-0.5.0.sol",
        VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
    ),
    Test(
        "conditional-all.sol",
        ALL_VERSIONS,
    ),
    Test(
        "for-all.sol",
        ALL_VERSIONS,
    ),
    Test("trycatch-0.4.0.sol", VERSIONS_04 + VERSIONS_05),
    # TODO: legacy failing
    Test(
        "trycatch-0.6.0.sol",
        VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
        disable_legacy=True,
    ),
    Test(
        "unchecked-0.4.0.sol",
        VERSIONS_04 + VERSIONS_05 + VERSIONS_06 + VERSIONS_07,
    ),
    Test("unchecked-0.8.0.sol", VERSIONS_08),
    Test(
        "return-all.sol",
        ALL_VERSIONS,
    ),
    Test("binaryoperation-0.4.0.sol", VERSIONS_04),
    Test(
        "binaryoperation-0.4.7.sol",
        make_version(4, 7, 9) + VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + make_version(8, 0, 12),
    ),
    Test("newexpression-0.4.0.sol", VERSIONS_04),
    Test(
        "newexpression-0.5.0.sol",
        VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
    ),
    Test(
        "enum-0.4.0.sol",
        VERSIONS_04 + VERSIONS_05 + VERSIONS_06 + VERSIONS_07,
    ),
    Test("enum-0.8.0.sol", VERSIONS_08),
    Test(
        "top_level_variable-0.4.0.sol",
        VERSIONS_04 + VERSIONS_05 + VERSIONS_06 + VERSIONS_07,
    ),
    Test("top_level_variable-0.8.0.sol", VERSIONS_08),
    Test("unaryexpression-0.4.0.sol", VERSIONS_04),
    Test(
        "unaryexpression-0.5.0.sol",
        VERSIONS_05 + VERSIONS_06 + VERSIONS_07 + VERSIONS_08,
    ),
    Test(
        "while-all.sol",
        ALL_VERSIONS,
    ),
    Test(
        "complex_imports/import_free/Caller.sol",
        ["0.8.2"],
    ),
    Test("custom_error_with_state_variable.sol", make_version(8, 4, 12)),
    Test("complex_imports/import_aliases/test.sol", VERSIONS_08),
    # 0.8.9 crashes on our testcase
    Test("user_defined_types.sol", ["0.8.8"] + make_version(8, 10, 12)),
    Test("bytes_call.sol", ["0.8.12"]),
]
# create the output folder if needed
try:
    os.mkdir("test_artifacts")
except OSError:
    pass


@pytest.mark.parametrize("test_item", ALL_TESTS, ids=lambda x: x.test_file)
def test_parsing(test_item: Test):
    flavors = ["compact"]
    if not test_item.disable_legacy:
        flavors += ["legacy"]
    for version, flavor in test_item.versions_with_flavors:
        test_file = os.path.join(
            TEST_ROOT, "compile", f"{test_item.test_file}-{version}-{flavor}.zip"
        )
        expected_file = os.path.join(
            TEST_ROOT, "expected", f"{test_item.test_file}-{version}-{flavor}.json"
        )

        cc = load_from_zip(test_file)[0]

        sl = Slither(
            cc,
            solc_force_legacy_json=flavor == "legacy",
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
                    f"test_artifacts/{test_item.test_file}_{path}_expected.dot",
                    "w",
                    encoding="utf8",
                ) as f:
                    f.write(change.t1)
                with open(
                    f"test_artifacts/{test_item.test_file}_{version}_{flavor}_{path}_actual.dot",
                    "w",
                    encoding="utf8",
                ) as f:
                    f.write(change.t2)

        assert not diff, diff.pretty()

        sl = Slither(cc, solc_force_legacy_json=flavor == "legacy", disallow_partial=True)
        sl.register_printer(Echidna)
        sl.run_printers()


def _generate_test(test_item: Test, skip_existing=False):
    flavors = ["compact"]
    if not test_item.disable_legacy:
        flavors += ["legacy"]
    for version, flavor in test_item.versions_with_flavors:
        test_file = os.path.join(
            TEST_ROOT, "compile", f"{test_item.test_file}-{version}-{flavor}.zip"
        )
        expected_file = os.path.join(
            TEST_ROOT, "expected", f"{test_item.test_file}-{version}-{flavor}.json"
        )

        if skip_existing:
            if os.path.isfile(expected_file):
                continue

        try:
            cc = load_from_zip(test_file)[0]
            sl = Slither(
                cc,
                solc_force_legacy_json=flavor == "legacy",
                disallow_partial=True,
                skip_analyze=True,
            )
        # pylint: disable=broad-except
        except Exception as e:
            print(e)
            print(test_item)
            print(f"{expected_file} failed")
            continue

        actual = generate_output(sl)
        print(f"Generate {expected_file}")

        # pylint: disable=no-member
        Path(expected_file).parents[0].mkdir(parents=True, exist_ok=True)

        with open(expected_file, "w", encoding="utf8") as f:
            json.dump(actual, f, indent="  ")


def set_solc(version: str):
    env = dict(os.environ)
    env["SOLC_VERSION"] = version
    os.environ.clear()
    os.environ.update(env)


def _generate_compile(test_item: Test, skip_existing=False):
    for version, flavor in test_item.versions_with_flavors:
        test_file = os.path.join(TEST_ROOT, test_item.test_file)
        expected_file = os.path.join(
            TEST_ROOT, "compile", f"{test_item.test_file}-{version}-{flavor}.zip"
        )

        if skip_existing:
            if os.path.isfile(expected_file):
                continue

        set_solc(version)
        print(f"Compiled to {expected_file}")
        cc = CryticCompile(test_file, solc_force_legacy_json=flavor == "legacy")

        # pylint: disable=no-member
        Path(expected_file).parents[0].mkdir(parents=True, exist_ok=True)

        save_to_zip([cc], expected_file)


if __name__ == "__main__":

    required_solcs = set()
    for test in ALL_TESTS:
        required_solcs |= set(test.solc_versions)
    installed_solcs = set(get_installed_solc_versions())
    missing_solcs = list(required_solcs - installed_solcs)
    if missing_solcs:
        install_solc_versions(missing_solcs)

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
