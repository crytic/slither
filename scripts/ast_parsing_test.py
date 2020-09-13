import os
import subprocess
import json
import errno
import sys

import traceback
from distutils.version import StrictVersion

from deepdiff import DeepDiff

from slither import Slither

LEGACY_SOLC_VERS = [f"0.4.{v}" for v in range(12)]

result = subprocess.run(["solc", "--versions"], stdout=subprocess.PIPE, check=True)
solc_versions = result.stdout.decode("utf-8").split("\n")

# remove empty strings if any
solc_versions = [version for version in solc_versions if version != ""]
solc_versions.reverse()

print("using solc versions", solc_versions)

slither_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test_dir = os.path.join(slither_root, "tests", "ast-parsing")

tests = {}

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

env = dict(os.environ)

failures = []

for test, vers in tests.items():
    print("running test", test, vers)

    ver_idx = 0

    for ver in solc_versions:
        if ver_idx + 1 < len(vers) and vers[ver_idx + 1] == ver:
            ver_idx += 1

        test_file = os.path.join(test_dir, f"{test}-{vers[ver_idx]}.sol")
        env["SOLC_VERSION"] = ver
        os.environ.clear()
        os.environ.update(env)

        for legacy_json in [True, False]:
            if not legacy_json and ver in LEGACY_SOLC_VERS:
                continue

            flavor = "legacy" if legacy_json else "compact"

            try:
                print(f"testing test={test} file={vers[ver_idx]} solc={ver} ast={flavor}")
                slither = Slither(
                    test_file, solc_force_legacy_json=legacy_json, disallow_partial=True
                )

                actual = {}

                for contract in slither.contracts:
                    actual[contract.name] = {}

                    for func_or_modifier in contract.functions + contract.modifiers:
                        actual[contract.name][
                            func_or_modifier.full_name
                        ] = func_or_modifier.slithir_cfg_to_dot_str(skip_expressions=True)

                expected_file = os.path.join(test_dir, "expected", f"{test}-{ver}-{flavor}.json")
                try:
                    with open(expected_file, "r") as f:
                        expected = json.load(f)
                except OSError as e:
                    if e.errno != errno.ENOENT:
                        raise

                    with open(expected_file, "w") as f:
                        json.dump(actual, f, indent="  ")
                        expected = actual

                diff = DeepDiff(expected, actual, ignore_order=True, verbose_level=2)
                if diff:
                    raise Exception(diff)
            except Exception as e:  # pylint: disable=broad-except
                print(
                    f"failed test={test} file={vers[ver_idx]} solc={ver} ast={flavor} err={type(e).__name__}"
                )
                failures.append((test, vers[ver_idx], ver, flavor, traceback.format_exc()))

failures_by_test = {k: 0 for k in tests}

for e in failures:
    test_name, file_ver, solc_ver, flavor, tb = e
    print(f"failed test={test_name} file={file_ver} solc={solc_ver} ast={flavor}")
    print(tb)

    failures_by_test[test_name] += 1

for k, v in sorted(failures_by_test.items(), key=lambda v: v[1], reverse=True):
    print(f"test={k} failures={v}")

sys.exit(-1 if len(failures) > 0 else 0)
