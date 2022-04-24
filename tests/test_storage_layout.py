import json
import os
import subprocess
from subprocess import PIPE, Popen

from slither import Slither

SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_TEST_ROOT = os.path.join(SLITHER_ROOT, "tests", "storage-layout")

# the storage layout has not yet changed between solidity versions so we will test with one version of the compiler


def test_storage_layout():
    subprocess.run(["solc-select", "use", "0.8.10"], stdout=subprocess.PIPE, check=True)

    test_item = os.path.join(STORAGE_TEST_ROOT, "storage_layout-0.8.10.sol")

    sl = Slither(test_item, solc_force_legacy_json=False, disallow_partial=True)

    with Popen(["solc", test_item, "--storage-layout"], stdout=PIPE) as process:
        for line in process.stdout:  # parse solc output
            if '{"storage":[{' in line.decode("utf-8"):  # find the storage layout
                layout = iter(json.loads(line)["storage"])
                while True:
                    try:
                        for contract in sl.contracts:
                            curr_var = next(layout)
                            var_name = curr_var["label"]
                            sl_name = contract.variables_as_dict[var_name]
                            slot, offset = contract.compilation_unit.storage_layout_of(
                                contract, sl_name
                            )
                            assert slot == int(curr_var["slot"])
                            assert offset == int(curr_var["offset"])
                    except StopIteration:
                        break
                    except KeyError as e:
                        print(f"not found {e} ")
