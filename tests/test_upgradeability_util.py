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
    missing_vars, new_vars, tainted_vars, new_funcs, modified_funcs, tainted_funcs = compare(v1, v2)
    assert len(missing_vars) == 0
    assert new_vars == [v2.get_state_variable_from_name("stateC")]
    assert tainted_vars == [
        v2.get_state_variable_from_name("stateB"),
        v2.get_state_variable_from_name("bug")
    ]
    assert new_funcs == [v2.get_function_from_signature("i()")]
    assert modified_funcs == [v2.get_function_from_signature("checkB()")]
    assert tainted_funcs == [
        v2.get_function_from_signature("g(uint256)"),
        v2.get_function_from_signature("h()")
    ]
