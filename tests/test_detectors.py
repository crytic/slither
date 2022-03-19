import json
import os
import pathlib
import sys
from pprint import pprint
from typing import Type, Optional, List

import pytest
from deepdiff import DeepDiff  # pip install deepdiff

from solc_select.solc_select import install_artifacts as install_solc_versions
from solc_select.solc_select import installed_versions as get_installed_solc_versions

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


def set_solc(test_item: Test):  # pylint: disable=too-many-lines
    # hacky hack hack to pick the solc version we want
    env = dict(os.environ)
    env["SOLC_VERSION"] = test_item.solc_ver
    os.environ.clear()
    os.environ.update(env)


def id_test(test_item: Test):
    return f"{test_item.detector}: {test_item.solc_ver}/{test_item.test_file}"


ALL_TEST_OBJECTS = [
    Test(
        all_detectors.UninitializedFunctionPtrsConstructor,
        "uninitialized_function_ptr_constructor.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UninitializedFunctionPtrsConstructor,
        "uninitialized_function_ptr_constructor.sol",
        "0.5.8",
    ),
    Test(
        all_detectors.UninitializedFunctionPtrsConstructor,
        "uninitialized_function_ptr_constructor.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyBenign,
        "reentrancy-benign.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ReentrancyBenign,
        "reentrancy-benign.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyBenign,
        "reentrancy-benign.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ReentrancyBenign,
        "reentrancy-benign.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "reentrancy-write.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "reentrancy-write.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "reentrancy-write.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "reentrancy-write.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "DAO.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "comment.sol",
        "0.8.2",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "no-reentrancy-staticcall.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "no-reentrancy-staticcall.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "no-reentrancy-staticcall.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.BooleanEquality,
        "boolean-constant-equality.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.BooleanEquality,
        "boolean-constant-equality.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.BooleanEquality,
        "boolean-constant-equality.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.BooleanEquality,
        "boolean-constant-equality.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.BooleanConstantMisuse,
        "boolean-constant-misuse.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.BooleanConstantMisuse,
        "boolean-constant-misuse.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.BooleanConstantMisuse,
        "boolean-constant-misuse.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.BooleanConstantMisuse,
        "boolean-constant-misuse.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UncheckedLowLevel,
        "unchecked_lowlevel.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UncheckedLowLevel,
        "unchecked_lowlevel.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UncheckedLowLevel,
        "unchecked_lowlevel.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UncheckedLowLevel,
        "unchecked_lowlevel.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UnindexedERC20EventParameters,
        "erc20_indexed.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnindexedERC20EventParameters,
        "erc20_indexed.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnindexedERC20EventParameters,
        "erc20_indexed.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnindexedERC20EventParameters,
        "erc20_indexed.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.IncorrectERC20InterfaceDetection,
        "incorrect_erc20_interface.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.IncorrectERC20InterfaceDetection,
        "incorrect_erc20_interface.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.IncorrectERC20InterfaceDetection,
        "incorrect_erc20_interface.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.IncorrectERC20InterfaceDetection,
        "incorrect_erc20_interface.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.IncorrectERC721InterfaceDetection,
        "incorrect_erc721_interface.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.IncorrectERC721InterfaceDetection,
        "incorrect_erc721_interface.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.IncorrectERC721InterfaceDetection,
        "incorrect_erc721_interface.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.IncorrectERC721InterfaceDetection,
        "incorrect_erc721_interface.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UninitializedStateVarsDetection,
        "uninitialized.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UninitializedStateVarsDetection,
        "uninitialized.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UninitializedStateVarsDetection,
        "uninitialized.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UninitializedStateVarsDetection,
        "uninitialized.sol",
        "0.7.6",
    ),
    Test(all_detectors.Backdoor, "backdoor.sol", "0.4.25"),
    Test(all_detectors.Backdoor, "backdoor.sol", "0.5.16"),
    Test(all_detectors.Backdoor, "backdoor.sol", "0.6.11"),
    Test(all_detectors.Backdoor, "backdoor.sol", "0.7.6"),
    Test(all_detectors.Suicidal, "suicidal.sol", "0.4.25"),
    Test(all_detectors.Suicidal, "suicidal.sol", "0.5.16"),
    Test(all_detectors.Suicidal, "suicidal.sol", "0.6.11"),
    Test(all_detectors.Suicidal, "suicidal.sol", "0.7.6"),
    Test(
        all_detectors.ConstantPragma,
        "pragma.0.4.25.sol",
        "0.4.25",
        ["pragma.0.4.24.sol"],
    ),
    Test(
        all_detectors.ConstantPragma,
        "pragma.0.5.16.sol",
        "0.5.16",
        ["pragma.0.5.15.sol"],
    ),
    Test(
        all_detectors.ConstantPragma,
        "pragma.0.6.11.sol",
        "0.6.11",
        ["pragma.0.6.10.sol"],
    ),
    Test(
        all_detectors.ConstantPragma,
        "pragma.0.7.6.sol",
        "0.7.6",
        ["pragma.0.7.5.sol"],
    ),
    Test(all_detectors.IncorrectSolc, "static.sol", "0.4.25"),
    Test(all_detectors.IncorrectSolc, "static.sol", "0.5.14"),
    Test(all_detectors.IncorrectSolc, "static.sol", "0.5.16"),
    Test(all_detectors.IncorrectSolc, "dynamic_1.sol", "0.5.16"),
    Test(all_detectors.IncorrectSolc, "dynamic_2.sol", "0.5.16"),
    Test(all_detectors.IncorrectSolc, "static.sol", "0.6.10"),
    Test(all_detectors.IncorrectSolc, "static.sol", "0.6.11"),
    Test(all_detectors.IncorrectSolc, "dynamic_1.sol", "0.6.11"),
    Test(all_detectors.IncorrectSolc, "dynamic_2.sol", "0.6.11"),
    Test(all_detectors.IncorrectSolc, "static.sol", "0.7.4"),
    Test(all_detectors.IncorrectSolc, "static.sol", "0.7.6"),
    Test(all_detectors.IncorrectSolc, "dynamic_1.sol", "0.7.6"),
    Test(all_detectors.IncorrectSolc, "dynamic_2.sol", "0.7.6"),
    Test(
        all_detectors.ReentrancyEth,
        "reentrancy.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ReentrancyEth,
        "reentrancy_indirect.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ReentrancyEth,
        "reentrancy.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyEth,
        "reentrancy_indirect.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyEth,
        "reentrancy.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ReentrancyEth,
        "reentrancy_indirect.sol",
        "0.6.11",
    ),
    Test(all_detectors.ReentrancyEth, "reentrancy.sol", "0.7.6"),
    Test(
        all_detectors.ReentrancyEth,
        "reentrancy_indirect.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ReentrancyEth,
        "DAO.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UninitializedStorageVars,
        "uninitialized_storage_pointer.sol",
        "0.4.25",
    ),
    Test(all_detectors.TxOrigin, "tx_origin.sol", "0.4.25"),
    Test(all_detectors.TxOrigin, "tx_origin.sol", "0.5.16"),
    Test(all_detectors.TxOrigin, "tx_origin.sol", "0.6.11"),
    Test(all_detectors.TxOrigin, "tx_origin.sol", "0.7.6"),
    Test(
        all_detectors.UnusedStateVars,
        "unused_state.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnusedStateVars,
        "unused_state.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnusedStateVars,
        "unused_state.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnusedStateVars,
        "unused_state.sol",
        "0.7.6",
    ),
    Test(all_detectors.LockedEther, "locked_ether.sol", "0.4.25"),
    Test(all_detectors.LockedEther, "locked_ether.sol", "0.5.16"),
    Test(all_detectors.LockedEther, "locked_ether.sol", "0.6.11"),
    Test(all_detectors.LockedEther, "locked_ether.sol", "0.7.6"),
    Test(
        all_detectors.ArbitrarySend,
        "arbitrary_send.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ArbitrarySend,
        "arbitrary_send.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ArbitrarySend,
        "arbitrary_send.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ArbitrarySend,
        "arbitrary_send.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.Assembly,
        "inline_assembly_contract.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.Assembly,
        "inline_assembly_library.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.Assembly,
        "inline_assembly_contract.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.Assembly,
        "inline_assembly_library.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.Assembly,
        "inline_assembly_contract.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.Assembly,
        "inline_assembly_library.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.Assembly,
        "inline_assembly_contract.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.Assembly,
        "inline_assembly_library.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.LowLevelCalls,
        "low_level_calls.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.LowLevelCalls,
        "low_level_calls.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.LowLevelCalls,
        "low_level_calls.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.LowLevelCalls,
        "low_level_calls.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ConstCandidateStateVars,
        "const_state_variables.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ConstCandidateStateVars,
        "const_state_variables.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ConstCandidateStateVars,
        "const_state_variables.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ConstCandidateStateVars,
        "const_state_variables.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ConstCandidateStateVars,
        "immutable.sol",
        "0.8.0",
    ),
    Test(
        all_detectors.ExternalFunction,
        "external_function.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ExternalFunction,
        "external_function_2.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ExternalFunction,
        "external_function_3.sol",
        "0.4.25",
    ),    
    Test(
        all_detectors.ExternalFunction,
        "external_function.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ExternalFunction,
        "external_function_2.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ExternalFunction,
        "external_function_3.sol",
        "0.5.16",
    ),    
    Test(
        all_detectors.ExternalFunction,
        "external_function.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ExternalFunction,
        "external_function_2.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ExternalFunction,
        "external_function_3.sol",
        "0.6.11",
    ),    
    Test(
        all_detectors.ExternalFunction,
        "external_function.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ExternalFunction,
        "external_function_2.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ExternalFunction,
        "external_function_3.sol",
        "0.7.6",
    ),    
    Test(
        all_detectors.NamingConvention,
        "naming_convention.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.NamingConvention,
        "naming_convention.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.NamingConvention,
        "naming_convention.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.NamingConvention,
        "naming_convention.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ControlledDelegateCall,
        "controlled_delegatecall.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ControlledDelegateCall,
        "controlled_delegatecall.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ControlledDelegateCall,
        "controlled_delegatecall.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ControlledDelegateCall,
        "controlled_delegatecall.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UninitializedLocalVars,
        "uninitialized_local_variable.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UninitializedLocalVars,
        "uninitialized_local_variable.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UninitializedLocalVars,
        "uninitialized_local_variable.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UninitializedLocalVars,
        "uninitialized_local_variable.sol",
        "0.7.6",
    ),
    Test(all_detectors.ConstantFunctionsAsm, "constant.sol", "0.4.25"),
    Test(
        all_detectors.ConstantFunctionsState,
        "constant.sol",
        "0.4.25",
    ),
    Test(all_detectors.ConstantFunctionsAsm, "constant.sol", "0.5.16"),
    Test(
        all_detectors.ConstantFunctionsState,
        "constant.sol",
        "0.5.16",
    ),
    Test(all_detectors.ConstantFunctionsAsm, "constant.sol", "0.6.11"),
    Test(
        all_detectors.ConstantFunctionsState,
        "constant.sol",
        "0.6.11",
    ),
    Test(all_detectors.ConstantFunctionsAsm, "constant.sol", "0.7.6"),
    Test(all_detectors.ConstantFunctionsState, "constant.sol", "0.7.6"),
    Test(
        all_detectors.UnusedReturnValues,
        "unused_return.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnusedReturnValues,
        "unused_return.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnusedReturnValues,
        "unused_return.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnusedReturnValues,
        "unused_return.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UncheckedTransfer,
        "unused_return_transfers.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ShadowingAbstractDetection,
        "shadowing_abstract.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ShadowingAbstractDetection,
        "shadowing_abstract.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ShadowingAbstractDetection,
        "shadowing_state_variable.sol",
        "0.7.5",
    ),
    Test(
        all_detectors.ShadowingAbstractDetection,
        "public_gap_variable.sol",
        "0.7.5",
    ),
    Test(
        all_detectors.StateShadowing,
        "shadowing_state_variable.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.StateShadowing,
        "shadowing_state_variable.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.StateShadowing,
        "shadowing_state_variable.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.StateShadowing,
        "shadowing_state_variable.sol",
        "0.7.5",
    ),
    Test(
        all_detectors.StateShadowing,
        "public_gap_variable.sol",
        "0.7.5",
    ),
    Test(
        all_detectors.StateShadowing,
        "shadowing_state_variable.sol",
        "0.7.6",
    ),
    Test(all_detectors.Timestamp, "timestamp.sol", "0.4.25"),
    Test(all_detectors.Timestamp, "timestamp.sol", "0.5.16"),
    Test(all_detectors.Timestamp, "timestamp.sol", "0.6.11"),
    Test(all_detectors.Timestamp, "timestamp.sol", "0.7.6"),
    Test(
        all_detectors.MultipleCallsInLoop,
        "multiple_calls_in_loop.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MultipleCallsInLoop,
        "multiple_calls_in_loop.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.MultipleCallsInLoop,
        "multiple_calls_in_loop.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.MultipleCallsInLoop,
        "multiple_calls_in_loop.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.BuiltinSymbolShadowing,
        "shadowing_builtin_symbols.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.BuiltinSymbolShadowing,
        "shadowing_builtin_symbols.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.LocalShadowing,
        "shadowing_local_variable.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.LocalShadowing,
        "shadowing_local_variable.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.LocalShadowing,
        "shadowing_local_variable.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.LocalShadowing,
        "shadowing_local_variable.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.RightToLeftOverride,
        "right_to_left_override.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.RightToLeftOverride,
        "right_to_left_override.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.RightToLeftOverride,
        "right_to_left_override.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.RightToLeftOverride,
        "unicode_direction_override.sol",
        "0.8.0",
    ),
    Test(all_detectors.VoidConstructor, "void-cst.sol", "0.4.25"),
    Test(all_detectors.VoidConstructor, "void-cst.sol", "0.5.16"),
    Test(all_detectors.VoidConstructor, "void-cst.sol", "0.6.11"),
    Test(all_detectors.VoidConstructor, "void-cst.sol", "0.7.6"),
    Test(
        all_detectors.UncheckedSend,
        "unchecked_send.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UncheckedSend,
        "unchecked_send.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UncheckedSend,
        "unchecked_send.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UncheckedSend,
        "unchecked_send.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ReentrancyEvent,
        "reentrancy-events.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ReentrancyEvent,
        "reentrancy-events.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ReentrancyEvent,
        "reentrancy-events.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.IncorrectStrictEquality,
        "incorrect_equality.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.IncorrectStrictEquality,
        "incorrect_equality.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.IncorrectStrictEquality,
        "incorrect_equality.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.IncorrectStrictEquality,
        "incorrect_equality.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.TooManyDigits,
        "too_many_digits.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.TooManyDigits,
        "too_many_digits.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.TooManyDigits,
        "too_many_digits.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.TooManyDigits,
        "too_many_digits.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "Buggy.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "Fixed.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "whitelisted.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "Buggy.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "Fixed.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "whitelisted.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "Buggy.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "Fixed.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "whitelisted.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "Buggy.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "Fixed.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "whitelisted.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ABIEncoderV2Array,
        "storage_ABIEncoderV2_array.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ABIEncoderV2Array,
        "storage_ABIEncoderV2_array.sol",
        "0.5.10",
    ),
    Test(
        all_detectors.ABIEncoderV2Array,
        "storage_ABIEncoderV2_array.sol",
        "0.5.9",
    ),
    Test(
        all_detectors.ArrayByReference,
        "array_by_reference.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ArrayByReference,
        "array_by_reference.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ArrayByReference,
        "array_by_reference.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ArrayByReference,
        "array_by_reference.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.AssertStateChange,
        "assert_state_change.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.AssertStateChange,
        "assert_state_change.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.AssertStateChange,
        "assert_state_change.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.AssertStateChange,
        "assert_state_change.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ArrayLengthAssignment,
        "array_length_assignment.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ArrayLengthAssignment,
        "array_length_assignment.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.CostlyOperationsInLoop,
        "multiple_costly_operations_in_loop.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.CostlyOperationsInLoop,
        "multiple_costly_operations_in_loop.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.CostlyOperationsInLoop,
        "multiple_costly_operations_in_loop.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.CostlyOperationsInLoop,
        "multiple_costly_operations_in_loop.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.FunctionInitializedState,
        "function_init_state_variables.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.FunctionInitializedState,
        "function_init_state_variables.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.FunctionInitializedState,
        "function_init_state_variables.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.FunctionInitializedState,
        "function_init_state_variables.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.MappingDeletionDetection,
        "MappingDeletion.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MappingDeletionDetection,
        "MappingDeletion.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.MappingDeletionDetection,
        "MappingDeletion.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.MappingDeletionDetection,
        "MappingDeletion.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.PublicMappingNested,
        "public_mappings_nested.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.RedundantStatements,
        "redundant_statements.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.RedundantStatements,
        "redundant_statements.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.RedundantStatements,
        "redundant_statements.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.RedundantStatements,
        "redundant_statements.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ReusedBaseConstructor,
        "reused_base_constructor.sol",
        "0.4.21",
    ),
    Test(
        all_detectors.ReusedBaseConstructor,
        "reused_base_constructor.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.StorageSignedIntegerArray,
        "storage_signed_integer_array.sol",
        "0.5.10",
    ),
    Test(
        all_detectors.StorageSignedIntegerArray,
        "storage_signed_integer_array.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "unimplemented.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "unimplemented.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "unimplemented.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "unimplemented.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "unimplemented_interfaces.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "unimplemented_interfaces.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "unimplemented_interfaces.sol",
        "0.7.6",
    ),
    Test(all_detectors.BadPRNG, "bad_prng.sol", "0.4.25"),
    Test(all_detectors.BadPRNG, "bad_prng.sol", "0.5.16"),
    Test(all_detectors.BadPRNG, "bad_prng.sol", "0.6.11"),
    Test(all_detectors.BadPRNG, "bad_prng.sol", "0.7.6"),
    Test(
        all_detectors.MissingEventsAccessControl,
        "missing_events_access_control.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MissingEventsAccessControl,
        "missing_events_access_control.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.MissingEventsAccessControl,
        "missing_events_access_control.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.MissingEventsAccessControl,
        "missing_events_access_control.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.MissingEventsArithmetic,
        "missing_events_arithmetic.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MissingEventsArithmetic,
        "missing_events_arithmetic.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.MissingEventsArithmetic,
        "missing_events_arithmetic.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.MissingEventsArithmetic,
        "missing_events_arithmetic.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ModifierDefaultDetection,
        "modifier_default.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ModifierDefaultDetection,
        "modifier_default.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.ModifierDefaultDetection,
        "modifier_default.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.ModifierDefaultDetection,
        "modifier_default.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.IncorrectUnaryExpressionDetection,
        "invalid_unary_expression.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MissingZeroAddressValidation,
        "missing_zero_address_validation.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MissingZeroAddressValidation,
        "missing_zero_address_validation.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.MissingZeroAddressValidation,
        "missing_zero_address_validation.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.MissingZeroAddressValidation,
        "missing_zero_address_validation.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.PredeclarationUsageLocal,
        "predeclaration_usage_local.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.DeadCode,
        "dead-code.sol",
        "0.8.0",
    ),
    Test(
        all_detectors.WriteAfterWrite,
        "write-after-write.sol",
        "0.8.0",
    ),
    Test(
        all_detectors.MsgValueInLoop,
        "msg_value_loop.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MsgValueInLoop,
        "msg_value_loop.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.MsgValueInLoop,
        "msg_value_loop.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.MsgValueInLoop,
        "msg_value_loop.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.MsgValueInLoop,
        "msg_value_loop.sol",
        "0.8.0",
    ),
    Test(
        all_detectors.DelegatecallInLoop,
        "delegatecall_loop.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.DelegatecallInLoop,
        "delegatecall_loop.sol",
        "0.5.16",
    ),
    Test(
        all_detectors.DelegatecallInLoop,
        "delegatecall_loop.sol",
        "0.6.11",
    ),
    Test(
        all_detectors.DelegatecallInLoop,
        "delegatecall_loop.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.DelegatecallInLoop,
        "delegatecall_loop.sol",
        "0.8.0",
    ),
    Test(
        all_detectors.ProtectedVariables,
        "comment.sol",
        "0.8.2",
    ),
]


def get_all_tests() -> List[Test]:
    installed_solcs = set(get_installed_solc_versions())
    required_solcs = {test.solc_ver for test in ALL_TEST_OBJECTS}
    missing_solcs = list(required_solcs - installed_solcs)
    if missing_solcs:
        install_solc_versions(missing_solcs)

    return ALL_TEST_OBJECTS


ALL_TESTS = get_all_tests()

GENERIC_PATH = "/GENERIC_PATH"


@pytest.mark.parametrize("test_item", ALL_TESTS, ids=id_test)
def test_detector(test_item: Test):
    test_dir_path = pathlib.Path(
        pathlib.Path().absolute(),
        "tests",
        "detectors",
        test_item.detector.ARGUMENT,
        test_item.solc_ver,
    )
    test_file_path = str(pathlib.Path(test_dir_path, test_item.test_file))
    expected_result_path = str(pathlib.Path(test_dir_path, test_item.expected_result).absolute())

    set_solc(test_item)
    sl = Slither(test_file_path)
    sl.register_detector(test_item.detector)
    results = sl.run_detectors()

    with open(expected_result_path, encoding="utf8") as f:
        expected_result = json.load(f)

    results_as_string = json.dumps(results)

    for additional_file in test_item.additional_files:
        additional_path = str(pathlib.Path(test_dir_path, additional_file).absolute())
        results_as_string = results_as_string.replace(
            additional_path, str(pathlib.Path(GENERIC_PATH))
        )
    results_as_string = results_as_string.replace(test_file_path, str(pathlib.Path(GENERIC_PATH)))

    results = json.loads(results_as_string)

    diff = DeepDiff(results, expected_result, ignore_order=True, verbose_level=2)
    if diff:
        pprint(diff)
        diff_as_dict = diff.to_dict()

        if "iterable_item_added" in diff_as_dict:
            print("#### Findings added")
            for finding_added in diff_as_dict["iterable_item_added"].values():
                print(finding_added["description"])
        if "iterable_item_removed" in diff_as_dict:
            print("#### Findings removed")
            for finding_added in diff_as_dict["iterable_item_removed"].values():
                print(finding_added["description"])
        assert False


def _generate_test(test_item: Test, skip_existing=False):
    test_dir_path = pathlib.Path(
        pathlib.Path().absolute(),
        "tests",
        "detectors",
        test_item.detector.ARGUMENT,
        test_item.solc_ver,
    )
    test_file_path = str(pathlib.Path(test_dir_path, test_item.test_file))
    expected_result_path = str(pathlib.Path(test_dir_path, test_item.expected_result).absolute())

    if skip_existing:
        if os.path.isfile(expected_result_path):
            return

    set_solc(test_item)
    sl = Slither(test_file_path)
    sl.register_detector(test_item.detector)
    results = sl.run_detectors()

    results_as_string = json.dumps(results)
    results_as_string = results_as_string.replace(test_file_path, str(pathlib.Path(GENERIC_PATH)))

    for additional_file in test_item.additional_files:
        additional_path = str(pathlib.Path(test_dir_path, additional_file).absolute())
        results_as_string = results_as_string.replace(
            additional_path, str(pathlib.Path(GENERIC_PATH))
        )

    results = json.loads(results_as_string)
    with open(expected_result_path, "w", encoding="utf8") as f:
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
