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
from slither.detectors import all_detectors


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
    Test(  # DO NOT move this specific test further down in this list, because for some inexplicable reason this test will then fail to report function bad2 ?!
        all_detectors.UninitializedFunctionPtrsConstructor,
        "tests/detectors/uninitialized-fptr-cst/0.4.25/uninitialized_function_ptr_constructor.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UninitializedFunctionPtrsConstructor,
        "tests/detectors/uninitialized-fptr-cst/0.5.8/uninitialized_function_ptr_constructor.sol",
        "0.5.8",
    ),
    Test(
        all_detectors.UninitializedFunctionPtrsConstructor,
        "tests/detectors/uninitialized-fptr-cst/0.5.16/uninitialized_function_ptr_constructor.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyBenign,
        "tests/detectors/reentrancy-benign/0.4.25/reentrancy-benign.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ReentrancyBenign,
        "tests/detectors/reentrancy-benign/0.5.16/reentrancy-benign.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyBenign,
        "tests/detectors/reentrancy-benign/0.6.11/reentrancy-benign.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ReentrancyBenign,
        "tests/detectors/reentrancy-benign/0.7.6/reentrancy-benign.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "tests/detectors/reentrancy-before-write/0.4.25/reentrancy-write.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "tests/detectors/reentrancy-before-write/0.5.16/reentrancy-write.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "tests/detectors/reentrancy-before-write/0.6.11/reentrancy-write.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "tests/detectors/reentrancy-before-write/0.7.6/reentrancy-write.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.BooleanEquality,
        "tests/detectors/boolean-constant-equality/0.4.25/boolean-constant-equality.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.BooleanEquality,
        "tests/detectors/boolean-constant-equality/0.5.16/boolean-constant-equality.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.BooleanEquality,
        "tests/detectors/boolean-constant-equality/0.6.11/boolean-constant-equality.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.BooleanEquality,
        "tests/detectors/boolean-constant-equality/0.7.6/boolean-constant-equality.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.BooleanConstantMisuse,
        "tests/detectors/boolean-constant-misuse/0.4.25/boolean-constant-misuse.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.BooleanConstantMisuse,
        "tests/detectors/boolean-constant-misuse/0.5.16/boolean-constant-misuse.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.BooleanConstantMisuse,
        "tests/detectors/boolean-constant-misuse/0.6.11/boolean-constant-misuse.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.BooleanConstantMisuse,
        "tests/detectors/boolean-constant-misuse/0.7.6/boolean-constant-misuse.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UncheckedLowLevel,
        "tests/detectors/unchecked-lowlevel/0.4.25/unchecked_lowlevel.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UncheckedLowLevel,
        "tests/detectors/unchecked-lowlevel/0.5.16/unchecked_lowlevel.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UncheckedLowLevel,
        "tests/detectors/unchecked-lowlevel/0.6.11/unchecked_lowlevel.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UncheckedLowLevel,
        "tests/detectors/unchecked-lowlevel/0.7.6/unchecked_lowlevel.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UnindexedERC20EventParameters,
        "tests/detectors/erc20-indexed/0.4.25/erc20_indexed.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnindexedERC20EventParameters,
        "tests/detectors/erc20-indexed/0.5.16/erc20_indexed.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnindexedERC20EventParameters,
        "tests/detectors/erc20-indexed/0.6.11/erc20_indexed.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnindexedERC20EventParameters,
        "tests/detectors/erc20-indexed/0.7.6/erc20_indexed.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.IncorrectERC20InterfaceDetection,
        "tests/detectors/erc20-interface/0.4.25/incorrect_erc20_interface.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.IncorrectERC20InterfaceDetection,
        "tests/detectors/erc20-interface/0.5.16/incorrect_erc20_interface.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.IncorrectERC20InterfaceDetection,
        "tests/detectors/erc20-interface/0.6.11/incorrect_erc20_interface.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.IncorrectERC20InterfaceDetection,
        "tests/detectors/erc20-interface/0.7.6/incorrect_erc20_interface.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.IncorrectERC721InterfaceDetection,
        "tests/detectors/erc721-interface/0.4.25/incorrect_erc721_interface.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.IncorrectERC721InterfaceDetection,
        "tests/detectors/erc721-interface/0.5.16/incorrect_erc721_interface.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.IncorrectERC721InterfaceDetection,
        "tests/detectors/erc721-interface/0.6.11/incorrect_erc721_interface.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.IncorrectERC721InterfaceDetection,
        "tests/detectors/erc721-interface/0.7.6/incorrect_erc721_interface.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UninitializedStateVarsDetection,
        "tests/detectors/uninitialized-state/0.4.25/uninitialized.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UninitializedStateVarsDetection,
        "tests/detectors/uninitialized-state/0.5.16/uninitialized.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UninitializedStateVarsDetection,
        "tests/detectors/uninitialized-state/0.6.11/uninitialized.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UninitializedStateVarsDetection,
        "tests/detectors/uninitialized-state/0.7.6/uninitialized.sol",
        "0.7.6",
    ),
    Test(all_detectors.Backdoor, "tests/detectors/backdoor/0.4.25/backdoor.sol", "0.4.25"),
    Test(all_detectors.Backdoor, "tests/detectors/backdoor/0.5.16/backdoor.sol", "0.5.16"),
    Test(all_detectors.Backdoor, "tests/detectors/backdoor/0.6.11/backdoor.sol", "0.6.11"),
    Test(all_detectors.Backdoor, "tests/detectors/backdoor/0.7.6/backdoor.sol", "0.7.6"),
    Test(all_detectors.Suicidal, "tests/detectors/suicidal/0.4.25/suicidal.sol", "0.4.25"),
    Test(all_detectors.Suicidal, "tests/detectors/suicidal/0.5.16/suicidal.sol", "0.5.16"),
    Test(all_detectors.Suicidal, "tests/detectors/suicidal/0.6.11/suicidal.sol", "0.6.11"),
    Test(all_detectors.Suicidal, "tests/detectors/suicidal/0.7.6/suicidal.sol", "0.7.6"),
    Test(
        all_detectors.ConstantPragma,
        "tests/detectors/pragma/0.4.25/pragma.0.4.25.sol",
        "0.4.25",
        ["tests/detectors/pragma/0.4.25/pragma.0.4.24.sol"],
    ),
    Test(
        all_detectors.ConstantPragma,
        "tests/detectors/pragma/0.5.16/pragma.0.5.16.sol",
        "0.5.16",
        ["tests/detectors/pragma/0.5.16/pragma.0.5.15.sol"],
    ),
    Test(
        all_detectors.ConstantPragma,
        "tests/detectors/pragma/0.6.11/pragma.0.6.11.sol",
        "0.6.11",
        ["tests/detectors/pragma/0.6.11/pragma.0.6.10.sol"],
    ),
    Test(
        all_detectors.ConstantPragma,
        "tests/detectors/pragma/0.7.6/pragma.0.7.6.sol",
        "0.7.6",
        ["tests/detectors/pragma/0.7.6/pragma.0.7.5.sol"],
    ),
    Test(all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.4.25/static.sol", "0.4.25"),
    Test(all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.5.14/static.sol", "0.5.14"),
    Test(all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.5.16/static.sol", "0.5.16"),
    Test(
        all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.5.16/dynamic_1.sol", "0.5.16"
    ),
    Test(
        all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.5.16/dynamic_2.sol", "0.5.16"
    ),
    Test(all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.6.10/static.sol", "0.6.10"),
    Test(all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.6.11/static.sol", "0.6.11"),
    Test(
        all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.6.11/dynamic_1.sol", "0.6.11"
    ),
    Test(
        all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.6.11/dynamic_2.sol", "0.6.11"
    ),
    Test(all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.7.4/static.sol", "0.7.4"),
    Test(all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.7.6/static.sol", "0.7.6"),
    Test(all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.7.6/dynamic_1.sol", "0.7.6"),
    Test(all_detectors.IncorrectSolc, "tests/detectors/solc-version/0.7.6/dynamic_2.sol", "0.7.6"),
    Test(
        all_detectors.ReentrancyEth,
        "tests/detectors/reentrancy-eth/0.4.25/reentrancy.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ReentrancyEth,
        "tests/detectors/reentrancy-eth/0.4.25/reentrancy_indirect.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ReentrancyEth,
        "tests/detectors/reentrancy-eth/0.5.16/reentrancy.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyEth,
        "tests/detectors/reentrancy-eth/0.5.16/reentrancy_indirect.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyEth,
        "tests/detectors/reentrancy-eth/0.6.11/reentrancy.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ReentrancyEth,
        "tests/detectors/reentrancy-eth/0.6.11/reentrancy_indirect.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ReentrancyEth, "tests/detectors/reentrancy-eth/0.7.6/reentrancy.sol", "0.7.6"
    ),
    Test(
        all_detectors.ReentrancyEth,
        "tests/detectors/reentrancy-eth/0.7.6/reentrancy_indirect.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UninitializedStorageVars,
        "tests/detectors/uninitialized-storage/0.4.25/uninitialized_storage_pointer.sol",
        "0.4.25",
    ),
    Test(all_detectors.TxOrigin, "tests/detectors/tx-origin/0.4.25/tx_origin.sol", "0.4.25"),
    Test(all_detectors.TxOrigin, "tests/detectors/tx-origin/0.5.16/tx_origin.sol", "0.5.16"),
    Test(all_detectors.TxOrigin, "tests/detectors/tx-origin/0.6.11/tx_origin.sol", "0.6.11"),
    Test(all_detectors.TxOrigin, "tests/detectors/tx-origin/0.7.6/tx_origin.sol", "0.7.6"),
    Test(
        all_detectors.UnusedStateVars,
        "tests/detectors/unused-state/0.4.25/unused_state.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnusedStateVars,
        "tests/detectors/unused-state/0.5.16/unused_state.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnusedStateVars,
        "tests/detectors/unused-state/0.6.11/unused_state.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnusedStateVars,
        "tests/detectors/unused-state/0.7.6/unused_state.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.LockedEther, "tests/detectors/locked-ether/0.4.25/locked_ether.sol", "0.4.25"
    ),
    Test(
        all_detectors.LockedEther, "tests/detectors/locked-ether/0.5.16/locked_ether.sol", "0.5.16"
    ),
    Test(
        all_detectors.LockedEther, "tests/detectors/locked-ether/0.6.11/locked_ether.sol", "0.6.11"
    ),
    Test(all_detectors.LockedEther, "tests/detectors/locked-ether/0.7.6/locked_ether.sol", "0.7.6"),
    Test(
        all_detectors.ArbitrarySend,
        "tests/detectors/arbitrary-send/0.4.25/arbitrary_send.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ArbitrarySend,
        "tests/detectors/arbitrary-send/0.5.16/arbitrary_send.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ArbitrarySend,
        "tests/detectors/arbitrary-send/0.6.11/arbitrary_send.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ArbitrarySend,
        "tests/detectors/arbitrary-send/0.7.6/arbitrary_send.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.Assembly,
        "tests/detectors/assembly/0.4.25/inline_assembly_contract.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.Assembly,
        "tests/detectors/assembly/0.4.25/inline_assembly_library.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.Assembly,
        "tests/detectors/assembly/0.5.16/inline_assembly_contract.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.Assembly,
        "tests/detectors/assembly/0.5.16/inline_assembly_library.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.Assembly,
        "tests/detectors/assembly/0.6.11/inline_assembly_contract.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.Assembly,
        "tests/detectors/assembly/0.6.11/inline_assembly_library.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.Assembly,
        "tests/detectors/assembly/0.7.6/inline_assembly_contract.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.Assembly,
        "tests/detectors/assembly/0.7.6/inline_assembly_library.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.LowLevelCalls,
        "tests/detectors/low-level-calls/0.4.25/low_level_calls.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.LowLevelCalls,
        "tests/detectors/low-level-calls/0.5.16/low_level_calls.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.LowLevelCalls,
        "tests/detectors/low-level-calls/0.6.11/low_level_calls.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.LowLevelCalls,
        "tests/detectors/low-level-calls/0.7.6/low_level_calls.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ConstCandidateStateVars,
        "tests/detectors/constable-states/0.4.25/const_state_variables.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ConstCandidateStateVars,
        "tests/detectors/constable-states/0.5.16/const_state_variables.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ConstCandidateStateVars,
        "tests/detectors/constable-states/0.6.11/const_state_variables.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ConstCandidateStateVars,
        "tests/detectors/constable-states/0.7.6/const_state_variables.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/0.4.25/external_function.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/0.4.25/external_function_2.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/0.5.16/external_function.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/0.5.16/external_function_2.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/0.6.11/external_function.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/0.6.11/external_function_2.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/0.7.6/external_function.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/0.7.6/external_function_2.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.NamingConvention,
        "tests/detectors/naming-convention/0.4.25/naming_convention.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.NamingConvention,
        "tests/detectors/naming-convention/0.5.16/naming_convention.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.NamingConvention,
        "tests/detectors/naming-convention/0.6.11/naming_convention.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.NamingConvention,
        "tests/detectors/naming-convention/0.7.6/naming_convention.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ControlledDelegateCall,
        "tests/detectors/controlled-delegatecall/0.4.25/controlled_delegatecall.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ControlledDelegateCall,
        "tests/detectors/controlled-delegatecall/0.5.16/controlled_delegatecall.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ControlledDelegateCall,
        "tests/detectors/controlled-delegatecall/0.6.11/controlled_delegatecall.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ControlledDelegateCall,
        "tests/detectors/controlled-delegatecall/0.7.6/controlled_delegatecall.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UninitializedLocalVars,
        "tests/detectors/uninitialized-local/0.4.25/uninitialized_local_variable.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UninitializedLocalVars,
        "tests/detectors/uninitialized-local/0.5.16/uninitialized_local_variable.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UninitializedLocalVars,
        "tests/detectors/uninitialized-local/0.6.11/uninitialized_local_variable.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UninitializedLocalVars,
        "tests/detectors/uninitialized-local/0.7.6/uninitialized_local_variable.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ConstantFunctionsAsm, "tests/detectors/constant/0.4.25/constant.sol", "0.4.25"
    ),
    Test(
        all_detectors.ConstantFunctionsState,
        "tests/detectors/constant/0.4.25/constant.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ConstantFunctionsAsm, "tests/detectors/constant/0.5.16/constant.sol", "0.5.16"
    ),
    Test(
        all_detectors.ConstantFunctionsState,
        "tests/detectors/constant/0.5.16/constant.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ConstantFunctionsAsm, "tests/detectors/constant/0.6.11/constant.sol", "0.6.11"
    ),
    Test(
        all_detectors.ConstantFunctionsState,
        "tests/detectors/constant/0.6.11/constant.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ConstantFunctionsAsm, "tests/detectors/constant/0.7.6/constant.sol", "0.7.6"
    ),
    Test(
        all_detectors.ConstantFunctionsState, "tests/detectors/constant/0.7.6/constant.sol", "0.7.6"
    ),
    Test(
        all_detectors.UnusedReturnValues,
        "tests/detectors/unused-return/0.4.25/unused_return.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnusedReturnValues,
        "tests/detectors/unused-return/0.5.16/unused_return.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnusedReturnValues,
        "tests/detectors/unused-return/0.6.11/unused_return.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnusedReturnValues,
        "tests/detectors/unused-return/0.7.6/unused_return.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ShadowingAbstractDetection,
        "tests/detectors/shadowing-abstract/0.4.25/shadowing_abstract.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ShadowingAbstractDetection,
        "tests/detectors/shadowing-abstract/0.5.16/shadowing_abstract.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.StateShadowing,
        "tests/detectors/shadowing-state/0.4.25/shadowing_state_variable.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.StateShadowing,
        "tests/detectors/shadowing-state/0.5.16/shadowing_state_variable.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.StateShadowing,
        "tests/detectors/shadowing-state/0.6.11/shadowing_state_variable.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.StateShadowing,
        "tests/detectors/shadowing-state/0.7.6/shadowing_state_variable.sol",
        "0.7.6",
    ),
    Test(all_detectors.Timestamp, "tests/detectors/timestamp/0.4.25/timestamp.sol", "0.4.25"),
    Test(all_detectors.Timestamp, "tests/detectors/timestamp/0.5.16/timestamp.sol", "0.5.16"),
    Test(all_detectors.Timestamp, "tests/detectors/timestamp/0.6.11/timestamp.sol", "0.6.11"),
    Test(all_detectors.Timestamp, "tests/detectors/timestamp/0.7.6/timestamp.sol", "0.7.6"),
    Test(
        all_detectors.MultipleCallsInLoop,
        "tests/detectors/calls-loop/0.4.25/multiple_calls_in_loop.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MultipleCallsInLoop,
        "tests/detectors/calls-loop/0.5.16/multiple_calls_in_loop.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.MultipleCallsInLoop,
        "tests/detectors/calls-loop/0.6.11/multiple_calls_in_loop.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.MultipleCallsInLoop,
        "tests/detectors/calls-loop/0.7.6/multiple_calls_in_loop.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.BuiltinSymbolShadowing,
        "tests/detectors/shadowing-builtin/0.4.25/shadowing_builtin_symbols.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.BuiltinSymbolShadowing,
        "tests/detectors/shadowing-builtin/0.5.16/shadowing_builtin_symbols.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.LocalShadowing,
        "tests/detectors/shadowing-local/0.4.25/shadowing_local_variable.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.LocalShadowing,
        "tests/detectors/shadowing-local/0.5.16/shadowing_local_variable.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.LocalShadowing,
        "tests/detectors/shadowing-local/0.6.11/shadowing_local_variable.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.LocalShadowing,
        "tests/detectors/shadowing-local/0.7.6/shadowing_local_variable.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.RightToLeftOverride,
        "tests/detectors/rtlo/0.4.25/right_to_left_override.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.RightToLeftOverride,
        "tests/detectors/rtlo/0.5.16/right_to_left_override.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.RightToLeftOverride,
        "tests/detectors/rtlo/0.6.11/right_to_left_override.sol",
        "0.6.11",
    ),
    Test(all_detectors.VoidConstructor, "tests/detectors/void-cst/0.4.25/void-cst.sol", "0.4.25"),
    Test(all_detectors.VoidConstructor, "tests/detectors/void-cst/0.5.16/void-cst.sol", "0.5.16"),
    Test(all_detectors.VoidConstructor, "tests/detectors/void-cst/0.6.11/void-cst.sol", "0.6.11"),
    Test(all_detectors.VoidConstructor, "tests/detectors/void-cst/0.7.6/void-cst.sol", "0.7.6"),
    Test(
        all_detectors.UncheckedSend,
        "tests/detectors/unchecked-send/0.4.25/unchecked_send.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UncheckedSend,
        "tests/detectors/unchecked-send/0.5.16/unchecked_send.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UncheckedSend,
        "tests/detectors/unchecked-send/0.6.11/unchecked_send.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UncheckedSend,
        "tests/detectors/unchecked-send/0.7.6/unchecked_send.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ReentrancyEvent,
        "tests/detectors/reentrancy-events/0.5.16/reentrancy-events.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyEvent,
        "tests/detectors/reentrancy-events/0.6.11/reentrancy-events.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ReentrancyEvent,
        "tests/detectors/reentrancy-events/0.7.6/reentrancy-events.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.IncorrectStrictEquality,
        "tests/detectors/incorrect-equality/0.4.25/incorrect_equality.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.IncorrectStrictEquality,
        "tests/detectors/incorrect-equality/0.5.16/incorrect_equality.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.IncorrectStrictEquality,
        "tests/detectors/incorrect-equality/0.6.11/incorrect_equality.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.IncorrectStrictEquality,
        "tests/detectors/incorrect-equality/0.7.6/incorrect_equality.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.TooManyDigits,
        "tests/detectors/too-many-digits/0.4.25/too_many_digits.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.TooManyDigits,
        "tests/detectors/too-many-digits/0.5.16/too_many_digits.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.TooManyDigits,
        "tests/detectors/too-many-digits/0.6.11/too_many_digits.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.TooManyDigits,
        "tests/detectors/too-many-digits/0.7.6/too_many_digits.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "tests/detectors/unprotected-upgrade/0.4.25/Buggy.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "tests/detectors/unprotected-upgrade/0.4.25/Fixed.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "tests/detectors/unprotected-upgrade/0.5.16/Buggy.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "tests/detectors/unprotected-upgrade/0.5.16/Fixed.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "tests/detectors/unprotected-upgrade/0.6.11/Buggy.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "tests/detectors/unprotected-upgrade/0.6.11/Fixed.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "tests/detectors/unprotected-upgrade/0.7.6/Buggy.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "tests/detectors/unprotected-upgrade/0.7.6/Fixed.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.NamingConvention,
        "tests/detectors/naming-convention/0.4.25/naming_convention_ignore.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ABIEncoderV2Array,
        "tests/detectors/abiencoderv2-array/0.4.25/storage_ABIEncoderV2_array.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ABIEncoderV2Array,
        "tests/detectors/abiencoderv2-array/0.5.10/storage_ABIEncoderV2_array.sol",
        "0.5.10",
    ),
    Test(
        all_detectors.ABIEncoderV2Array,
        "tests/detectors/abiencoderv2-array/0.5.11/storage_ABIEncoderV2_array.sol",
        "0.5.11",
    ),
    Test(
        all_detectors.ArrayByReference,
        "tests/detectors/array-by-reference/0.4.25/array_by_reference.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ArrayByReference,
        "tests/detectors/array-by-reference/0.5.16/array_by_reference.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ArrayByReference,
        "tests/detectors/array-by-reference/0.6.11/array_by_reference.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ArrayByReference,
        "tests/detectors/array-by-reference/0.7.6/array_by_reference.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.AssertStateChange,
        "tests/detectors/assert-state-change/0.4.25/assert_state_change.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.AssertStateChange,
        "tests/detectors/assert-state-change/0.5.16/assert_state_change.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.AssertStateChange,
        "tests/detectors/assert-state-change/0.6.11/assert_state_change.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.AssertStateChange,
        "tests/detectors/assert-state-change/0.7.6/assert_state_change.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ArrayLengthAssignment,
        "tests/detectors/controlled-array-length/0.4.25/array_length_assignment.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ArrayLengthAssignment,
        "tests/detectors/controlled-array-length/0.5.16/array_length_assignment.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.CostlyOperationsInLoop,
        "tests/detectors/costly-loop/0.4.25/multiple_costly_operations_in_loop.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.CostlyOperationsInLoop,
        "tests/detectors/costly-loop/0.5.16/multiple_costly_operations_in_loop.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.CostlyOperationsInLoop,
        "tests/detectors/costly-loop/0.6.11/multiple_costly_operations_in_loop.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.CostlyOperationsInLoop,
        "tests/detectors/costly-loop/0.7.6/multiple_costly_operations_in_loop.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.FunctionInitializedState,
        "tests/detectors/function-init-state/0.4.25/function_init_state_variables.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.FunctionInitializedState,
        "tests/detectors/function-init-state/0.5.16/function_init_state_variables.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.FunctionInitializedState,
        "tests/detectors/function-init-state/0.6.11/function_init_state_variables.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.FunctionInitializedState,
        "tests/detectors/function-init-state/0.7.6/function_init_state_variables.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.MappingDeletionDetection,
        "tests/detectors/mapping-deletion/0.4.25/MappingDeletion.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MappingDeletionDetection,
        "tests/detectors/mapping-deletion/0.5.16/MappingDeletion.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.MappingDeletionDetection,
        "tests/detectors/mapping-deletion/0.6.11/MappingDeletion.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.MappingDeletionDetection,
        "tests/detectors/mapping-deletion/0.7.6/MappingDeletion.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "tests/detectors/missing-inheritance/0.5.16/unimplemented_interfaces.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "tests/detectors/missing-inheritance/0.6.11/unimplemented_interfaces.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "tests/detectors/missing-inheritance/0.7.6/unimplemented_interfaces.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.PublicMappingNested,
        "tests/detectors/public-mappings-nested/0.4.25/public_mappings_nested.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.RedundantStatements,
        "tests/detectors/redundant-statements/0.4.25/redundant_statements.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.RedundantStatements,
        "tests/detectors/redundant-statements/0.5.16/redundant_statements.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.RedundantStatements,
        "tests/detectors/redundant-statements/0.6.11/redundant_statements.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.RedundantStatements,
        "tests/detectors/redundant-statements/0.7.6/redundant_statements.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ReusedBaseConstructor,
        "tests/detectors/reused-constructor/0.4.21/reused_base_constructor.sol",
        "0.4.21",
    ),
    Test(
        all_detectors.ReusedBaseConstructor,
        "tests/detectors/reused-constructor/0.4.25/reused_base_constructor.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.StorageSignedIntegerArray,
        "tests/detectors/storage-array/0.5.10/storage_signed_integer_array.sol",
        "0.5.10",
    ),
    Test(
        all_detectors.StorageSignedIntegerArray,
        "tests/detectors/storage-array/0.5.16/storage_signed_integer_array.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "tests/detectors/unimplemented-functions/0.4.25/unimplemented.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "tests/detectors/unimplemented-functions/0.5.16/unimplemented.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "tests/detectors/unimplemented-functions/0.6.11/unimplemented.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "tests/detectors/unimplemented-functions/0.7.6/unimplemented.sol",
        "0.7.6",
    ),
    Test(all_detectors.BadPRNG, "tests/detectors/weak-prng/0.4.25/bad_prng.sol", "0.4.25"),
    Test(all_detectors.BadPRNG, "tests/detectors/weak-prng/0.5.16/bad_prng.sol", "0.5.16"),
    Test(all_detectors.BadPRNG, "tests/detectors/weak-prng/0.6.11/bad_prng.sol", "0.6.11"),
    Test(all_detectors.BadPRNG, "tests/detectors/weak-prng/0.7.6/bad_prng.sol", "0.7.6"),
    Test(
        all_detectors.MissingEventsAccessControl,
        "tests/detectors/events-access/0.4.25/missing_events_access_control.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MissingEventsAccessControl,
        "tests/detectors/events-access/0.5.16/missing_events_access_control.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.MissingEventsAccessControl,
        "tests/detectors/events-access/0.6.11/missing_events_access_control.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.MissingEventsAccessControl,
        "tests/detectors/events-access/0.7.6/missing_events_access_control.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.MissingEventsArithmetic,
        "tests/detectors/events-maths/0.4.25/missing_events_arithmetic.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MissingEventsArithmetic,
        "tests/detectors/events-maths/0.5.16/missing_events_arithmetic.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.MissingEventsArithmetic,
        "tests/detectors/events-maths/0.6.11/missing_events_arithmetic.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.MissingEventsArithmetic,
        "tests/detectors/events-maths/0.7.6/missing_events_arithmetic.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ModifierDefaultDetection,
        "tests/detectors/incorrect-modifier/0.4.25/modifier_default.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ModifierDefaultDetection,
        "tests/detectors/incorrect-modifier/0.5.16/modifier_default.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ModifierDefaultDetection,
        "tests/detectors/incorrect-modifier/0.6.11/modifier_default.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ModifierDefaultDetection,
        "tests/detectors/incorrect-modifier/0.7.6/modifier_default.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.IncorrectUnaryExpressionDetection,
        "tests/detectors/incorrect-unary/0.4.25/invalid_unary_expression.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MissingZeroAddressValidation,
        "tests/detectors/missing-zero-check/0.4.25/missing_zero_address_validation.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MissingZeroAddressValidation,
        "tests/detectors/missing-zero-check/0.5.16/missing_zero_address_validation.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.MissingZeroAddressValidation,
        "tests/detectors/missing-zero-check/0.6.11/missing_zero_address_validation.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.MissingZeroAddressValidation,
        "tests/detectors/missing-zero-check/0.7.6/missing_zero_address_validation.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.PredeclarationUsageLocal,
        "tests/detectors/variable-scope/0.4.25/predeclaration_usage_local.sol",
        "0.4.25",
    ),
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
