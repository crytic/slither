import json
import os
import pathlib
import sys
from pprint import pprint
from typing import Type, Optional, List

import pytest
from deepdiff import DeepDiff  # pip install deepdiff

from slither import Slither
from slither.detectors.abstract_detector import AbstractDetector
from slither.detectors.attributes.const_functions_asm import ConstantFunctionsAsm
from slither.detectors.attributes.const_functions_state import ConstantFunctionsState
from slither.detectors.attributes.constant_pragma import ConstantPragma
from slither.detectors.attributes.incorrect_solc import IncorrectSolc
from slither.detectors.attributes.locked_ether import LockedEther
from slither.detectors.erc.incorrect_erc20_interface import IncorrectERC20InterfaceDetection
from slither.detectors.erc.incorrect_erc721_interface import IncorrectERC721InterfaceDetection
from slither.detectors.erc.unindexed_event_parameters import UnindexedERC20EventParameters
from slither.detectors.examples.backdoor import Backdoor
from slither.detectors.functions.arbitrary_send import ArbitrarySend
from slither.detectors.functions.external_function import ExternalFunction
from slither.detectors.functions.suicidal import Suicidal
from slither.detectors.naming_convention.naming_convention import NamingConvention
from slither.detectors.operations.block_timestamp import Timestamp
from slither.detectors.operations.low_level_calls import LowLevelCalls
from slither.detectors.operations.unchecked_low_level_return_values import UncheckedLowLevel
from slither.detectors.operations.unchecked_send_return_value import UncheckedSend
from slither.detectors.operations.unused_return_values import UnusedReturnValues
from slither.detectors.operations.void_constructor import VoidConstructor
from slither.detectors.reentrancy.reentrancy_eth import ReentrancyEth
from slither.detectors.reentrancy.reentrancy_events import ReentrancyEvent
from slither.detectors.shadowing.abstract import ShadowingAbstractDetection
from slither.detectors.shadowing.builtin_symbols import BuiltinSymbolShadowing
from slither.detectors.shadowing.local import LocalShadowing
from slither.detectors.shadowing.state import StateShadowing
from slither.detectors.source.rtlo import RightToLeftOverride
from slither.detectors.statements.assembly import Assembly
from slither.detectors.statements.boolean_constant_equality import BooleanEquality
from slither.detectors.statements.calls_in_loop import MultipleCallsInLoop
from slither.detectors.statements.controlled_delegatecall import ControlledDelegateCall
from slither.detectors.statements.incorrect_strict_equality import IncorrectStrictEquality
from slither.detectors.statements.too_many_digits import TooManyDigits
from slither.detectors.statements.tx_origin import TxOrigin
from slither.detectors.variables.possible_const_state_variables import ConstCandidateStateVars
from slither.detectors.variables.uninitialized_local_variables import UninitializedLocalVars
from slither.detectors.variables.uninitialized_state_variables import (
    UninitializedStateVarsDetection,
)
from slither.detectors.variables.uninitialized_storage_variables import UninitializedStorageVars
from slither.detectors.variables.unused_state_variables import UnusedStateVars


class Test:  # pylint: disable=too-few-public-methods
    def __init__(
        self,
        detector: Type[AbstractDetector],
        test_file: str,
        solc_ver: str,
        additional_files: Optional[List[str]] = None,
    ):
        """


        :param detector:
        :param test_file:
        :param solc_ver:
        :param additional_files: If the test changes additional files, list them here to allow the
        test to update the source mapping
        """
        self.detector = detector
        self.test_file = test_file
        self.expected_result = test_file + "." + solc_ver + "." + detector.__name__ + ".json"
        self.solc_ver = solc_ver
        if additional_files is None:
            self.additional_files = []
        else:
            self.additional_files = additional_files


def set_solc(test_item: Test):
    # hacky hack hack to pick the solc version we want
    env = dict(os.environ)
    env["SOLC_VERSION"] = test_item.solc_ver
    os.environ.clear()
    os.environ.update(env)


def id_test(test_item: Test):
    return f"{test_item.detector}: {test_item.test_file}"


ALL_TESTS = [
    Test(BooleanEquality, "tests/detectors/boolean-constant-equality/boolean-constant-equality.sol", "0.4.25"),
    Test(UncheckedLowLevel, "tests/detectors/unchecked-lowlevel/unchecked_lowlevel.sol", "0.4.25"),
    Test(
        UncheckedLowLevel,
        "tests/detectors/unchecked-lowlevel/unchecked_lowlevel-0.5.1.sol",
        "0.5.1",
    ),
    Test(
        UncheckedLowLevel,
        "tests/detectors/unchecked-lowlevel/unchecked_lowlevel-0.5.1.sol",
        "0.5.1",
    ),
    Test(
        UnindexedERC20EventParameters, "tests/detectors/erc20-indexed/erc20_indexed.sol", "0.4.25"
    ),
    Test(
        IncorrectERC20InterfaceDetection,
        "tests/detectors/erc20-interface/incorrect_erc20_interface.sol",
        "0.4.25",
    ),
    Test(
        IncorrectERC721InterfaceDetection,
        "tests/detectors/erc721-interface/incorrect_erc721_interface.sol",
        "0.4.25",
    ),
    Test(
        UninitializedStateVarsDetection,
        "tests/detectors/uninitialized-state/uninitialized.sol",
        "0.4.25",
    ),
    Test(
        UninitializedStateVarsDetection,
        "tests/detectors/uninitialized-state/uninitialized-0.5.1.sol",
        "0.5.1",
    ),
    Test(Backdoor, "tests/detectors/backdoor/backdoor.sol", "0.4.25"),
    Test(Backdoor, "tests/detectors/backdoor/backdoor.sol", "0.5.1"),
    Test(Suicidal, "tests/detectors/backdoor/backdoor.sol", "0.4.25"),
    Test(Suicidal, "tests/detectors/backdoor/backdoor.sol", "0.5.1"),
    Test(
        ConstantPragma,
        "tests/detectors/pragma/pragma.0.4.24.sol",
        "0.4.25",
        ["tests/detectors/pragma/pragma.0.4.23.sol"],
    ),
    Test(IncorrectSolc, "tests/detectors/solc-version/old_solc.sol", "0.4.21"),
    Test(IncorrectSolc, "tests/detectors/solc-version/solc_version_incorrect.sol", "0.4.25"),
    Test(IncorrectSolc, "tests/detectors/solc-version/solc_version_incorrect_05.sol", "0.5.7"),
    Test(ReentrancyEth, "tests/detectors/reentrancy-eth/reentrancy.sol", "0.4.25"),
    Test(ReentrancyEth, "tests/detectors/reentrancy-eth/reentrancy_indirect.sol", "0.4.25"),
    Test(ReentrancyEth, "tests/detectors/reentrancy-eth/reentrancy-0.5.1.sol", "0.5.1"),
    Test(
        UninitializedStorageVars,
        "tests/detectors/uninitialized-storage/uninitialized_storage_pointer.sol",
        "0.4.25",
    ),
    Test(TxOrigin, "tests/detectors/tx-origin/tx_origin.sol", "0.4.25"),
    Test(TxOrigin, "tests/detectors/tx-origin/tx_origin-0.5.1.sol", "0.5.1"),
    Test(UnusedStateVars, "tests/detectors/unused-state/unused_state.sol", "0.4.25"),
    Test(UnusedStateVars, "tests/detectors/unused-state/unused_state.sol", "0.5.1"),
    Test(LockedEther, "tests/detectors/locked-ether/locked_ether.sol", "0.4.25"),
    Test(LockedEther, "tests/detectors/locked-ether/locked_ether-0.5.1.sol", "0.5.1"),
    Test(ArbitrarySend, "tests/detectors/arbitrary-send/arbitrary_send.sol", "0.4.25"),
    Test(ArbitrarySend, "tests/detectors/arbitrary-send/arbitrary_send-0.5.1.sol", "0.5.1"),
    Test(Assembly, "tests/detectors/assembly/inline_assembly_contract.sol", "0.4.25"),
    Test(Assembly, "tests/detectors/assembly/inline_assembly_library.sol", "0.4.25"),
    Test(Assembly, "tests/detectors/assembly/inline_assembly_contract-0.5.1.sol", "0.5.1"),
    Test(Assembly, "tests/detectors/assembly/inline_assembly_library-0.5.1.sol", "0.5.1"),
    Test(LowLevelCalls, "tests/detectors/low-level-calls/low_level_calls.sol", "0.4.25"),
    Test(LowLevelCalls, "tests/detectors/low-level-calls/low_level_calls.sol", "0.5.1"),
    Test(
        ConstCandidateStateVars,
        "tests/detectors/constable-states/const_state_variables.sol",
        "0.4.25",
    ),
    Test(
        ConstCandidateStateVars,
        "tests/detectors/constable-states/const_state_variables.sol",
        "0.5.1",
    ),
    Test(ExternalFunction, "tests/detectors/external-function/external_function.sol", "0.4.25"),
    Test(ExternalFunction, "tests/detectors/external-function/external_function_2.sol", "0.4.25"),
    Test(ExternalFunction, "tests/detectors/external-function/external_function.sol", "0.5.1"),
    Test(ExternalFunction, "tests/detectors/external-function/external_function_2.sol", "0.5.1"),
    Test(NamingConvention, "tests/detectors/naming-convention/naming_convention.sol", "0.4.25"),
    Test(NamingConvention, "tests/detectors/naming-convention/naming_convention.sol", "0.5.1"),
    Test(
        ControlledDelegateCall,
        "tests/detectors/controlled-delegatecall/controlled_delegatecall.sol",
        "0.4.25",
    ),
    Test(
        ControlledDelegateCall,
        "tests/detectors/controlled-delegatecall/controlled_delegatecall.sol",
        "0.5.1",
    ),
    Test(
        UninitializedLocalVars,
        "tests/detectors/uninitialized-local/uninitialized_local_variable.sol",
        "0.4.25",
    ),
    Test(ConstantFunctionsAsm, "tests/detectors/constant/constant.sol", "0.4.25"),
    Test(ConstantFunctionsState, "tests/detectors/constant/constant.sol", "0.4.25"),
    Test(ConstantFunctionsAsm, "tests/detectors/constant/constant-0.5.1.sol", "0.5.1"),
    Test(ConstantFunctionsState, "tests/detectors/constant/constant-0.5.1.sol", "0.5.1"),
    Test(UnusedReturnValues, "tests/detectors/unused-return/unused_return.sol", "0.4.25"),
    Test(UnusedReturnValues, "tests/detectors/unused-return/unused_return.sol", "0.5.1"),
    Test(
        ShadowingAbstractDetection,
        "tests/detectors/shadowing-abstract/shadowing_abstract.sol",
        "0.4.25",
    ),
    Test(StateShadowing, "tests/detectors/shadowing-state/shadowing_state_variable.sol", "0.4.25"),
    Test(Timestamp, "tests/detectors/timestamp/timestamp.sol", "0.4.25"),
    Test(Timestamp, "tests/detectors/timestamp/timestamp.sol", "0.5.1"),
    Test(MultipleCallsInLoop, "tests/detectors/calls-loop/multiple_calls_in_loop.sol", "0.4.25"),
    Test(
        BuiltinSymbolShadowing,
        "tests/detectors/shadowing-builtin/shadowing_builtin_symbols.sol",
        "0.4.25",
    ),
    Test(LocalShadowing, "tests/detectors/shadowing-local/shadowing_local_variable.sol", "0.4.25"),
    Test(RightToLeftOverride, "tests/detectors/rtlo/right_to_left_override.sol", "0.4.25"),
    Test(VoidConstructor, "tests/detectors/void-cst/void-cst.sol", "0.5.1"),
    Test(UncheckedSend, "tests/detectors/unchecked-send/unchecked_send-0.5.1.sol", "0.5.1"),
    Test(ReentrancyEvent, "tests/detectors/reentrancy-events/reentrancy-0.5.1-events.sol", "0.5.1"),
    Test(
        IncorrectStrictEquality,
        "tests/detectors/incorrect-equality/incorrect_equality.sol",
        "0.5.1",
    ),
    Test(TooManyDigits, "tests/detectors/too-many-digits/too_many_digits.sol", "0.5.1"),
]
GENERIC_PATH = "/GENERIC_PATH"


@pytest.mark.parametrize("test_item", ALL_TESTS, ids=id_test)
def test_detector(test_item: Test):
    set_solc(test_item)
    sl = Slither(test_item.test_file)
    sl.register_detector(test_item.detector)
    results = sl.run_detectors()

    with open(test_item.expected_result, encoding="utf8") as f:
        expected_result = json.load(f)

    results_as_string = json.dumps(results)
    current_path = str(pathlib.Path(pathlib.Path().absolute(), test_item.test_file).absolute())
    for additional_file in test_item.additional_files:
        additional_path = str(pathlib.Path(pathlib.Path().absolute(), additional_file).absolute())
        results_as_string = results_as_string.replace(
            additional_path, str(pathlib.Path(GENERIC_PATH))
        )
    results_as_string = results_as_string.replace(current_path, str(pathlib.Path(GENERIC_PATH)))
    results = json.loads(results_as_string)

    diff = DeepDiff(results, expected_result, ignore_order=True, verbose_level=2)
    if diff:
        pprint(diff)
        diff_as_dict = diff.to_dict()

        if "iterable_item_added" in diff_as_dict:
            print("#### Findings added")
            for findings_added in diff_as_dict["iterable_item_added"].values():
                for finding_added in findings_added:
                    print(finding_added["description"])
        if "iterable_item_removed" in diff_as_dict:
            print("#### Findings removed")
            for findings_added in diff_as_dict["iterable_item_removed"].values():
                for finding_added in findings_added:
                    print(finding_added["description"])
        assert False


def _generate_test(test_item: Test, skip_existing=False):

    if skip_existing:
        if os.path.isfile(test_item.expected_result):
            return

    set_solc(test_item)
    sl = Slither(test_item.test_file)
    sl.register_detector(test_item.detector)
    results = sl.run_detectors()

    results_as_string = json.dumps(results)
    current_path = str(pathlib.Path(pathlib.Path().absolute(), test_item.test_file).absolute())
    results_as_string = results_as_string.replace(current_path, str(pathlib.Path(GENERIC_PATH)))

    for additional_file in test_item.additional_files:
        additional_path = str(pathlib.Path(pathlib.Path().absolute(), additional_file).absolute())
        results_as_string = results_as_string.replace(
            additional_path, str(pathlib.Path(GENERIC_PATH))
        )

    results = json.loads(results_as_string)

    with open(test_item.expected_result, "w") as f:
        f.write(json.dumps(results, indent=4))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("To generate the json artifacts run\n\tpython tests/test_detectors.py --generate")
    elif sys.argv[1] == "--generate":
        for next_test in ALL_TESTS:
            _generate_test(next_test, skip_existing=True)
    elif sys.argv[1] == "--overwrite":
        for next_test in ALL_TESTS:
            _generate_test(next_test)
