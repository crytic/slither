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
    Test(
        all_detectors.ReentrancyBenign,
        "tests/detectors/reentrancy-benign/reentrancy-benign.sol",
        "0.4.26",
    ),
    Test(
        all_detectors.ReentrancyReadBeforeWritten,
        "tests/detectors/reentrancy-before-write/reentrancy-write.sol",
        "0.4.26",
    ),
    Test(
        all_detectors.BooleanEquality,
        "tests/detectors/boolean-constant-equality/boolean-constant-equality.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.BooleanConstantMisuse,
        "tests/detectors/boolean-constant-misuse/boolean-constant-misuse.sol",
        "0.6.0",
    ),
    Test(
        all_detectors.UncheckedLowLevel,
        "tests/detectors/unchecked-lowlevel/unchecked_lowlevel.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UncheckedLowLevel,
        "tests/detectors/unchecked-lowlevel/unchecked_lowlevel-0.5.1.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.UncheckedLowLevel,
        "tests/detectors/unchecked-lowlevel/unchecked_lowlevel-0.5.1.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.UnindexedERC20EventParameters,
        "tests/detectors/erc20-indexed/erc20_indexed.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.IncorrectERC20InterfaceDetection,
        "tests/detectors/erc20-interface/incorrect_erc20_interface.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.IncorrectERC721InterfaceDetection,
        "tests/detectors/erc721-interface/incorrect_erc721_interface.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UninitializedStateVarsDetection,
        "tests/detectors/uninitialized-state/uninitialized.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UninitializedStateVarsDetection,
        "tests/detectors/uninitialized-state/uninitialized-0.5.1.sol",
        "0.5.1",
    ),
    Test(all_detectors.Backdoor, "tests/detectors/backdoor/backdoor.sol", "0.4.25"),
    Test(all_detectors.Backdoor, "tests/detectors/backdoor/backdoor.sol", "0.5.1"),
    Test(all_detectors.Suicidal, "tests/detectors/backdoor/backdoor.sol", "0.4.25"),
    Test(all_detectors.Suicidal, "tests/detectors/backdoor/backdoor.sol", "0.5.1"),
    Test(
        all_detectors.ConstantPragma,
        "tests/detectors/pragma/pragma.0.4.24.sol",
        "0.4.25",
        ["tests/detectors/pragma/pragma.0.4.23.sol"],
    ),
    Test(all_detectors.IncorrectSolc, "tests/detectors/solc-version/old_solc.sol", "0.4.21"),
    Test(
        all_detectors.IncorrectSolc,
        "tests/detectors/solc-version/solc_version_incorrect.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.IncorrectSolc,
        "tests/detectors/solc-version/solc_version_incorrect_05.sol",
        "0.5.7",
    ),
    Test(all_detectors.ReentrancyEth, "tests/detectors/reentrancy-eth/reentrancy.sol", "0.4.25"),
    Test(
        all_detectors.ReentrancyEth,
        "tests/detectors/reentrancy-eth/reentrancy_indirect.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ReentrancyEth, "tests/detectors/reentrancy-eth/reentrancy-0.5.1.sol", "0.5.1"
    ),
    Test(
        all_detectors.UninitializedStorageVars,
        "tests/detectors/uninitialized-storage/uninitialized_storage_pointer.sol",
        "0.4.25",
    ),
    Test(all_detectors.TxOrigin, "tests/detectors/tx-origin/tx_origin.sol", "0.4.25"),
    Test(all_detectors.TxOrigin, "tests/detectors/tx-origin/tx_origin-0.5.1.sol", "0.5.1"),
    Test(all_detectors.UnusedStateVars, "tests/detectors/unused-state/unused_state.sol", "0.4.25"),
    Test(all_detectors.UnusedStateVars, "tests/detectors/unused-state/unused_state.sol", "0.5.1"),
    Test(all_detectors.LockedEther, "tests/detectors/locked-ether/locked_ether.sol", "0.4.25"),
    Test(all_detectors.LockedEther, "tests/detectors/locked-ether/locked_ether-0.5.1.sol", "0.5.1"),
    Test(
        all_detectors.ArbitrarySend, "tests/detectors/arbitrary-send/arbitrary_send.sol", "0.4.25"
    ),
    Test(
        all_detectors.ArbitrarySend,
        "tests/detectors/arbitrary-send/arbitrary_send-0.5.1.sol",
        "0.5.1",
    ),
    Test(all_detectors.Assembly, "tests/detectors/assembly/inline_assembly_contract.sol", "0.4.25"),
    Test(all_detectors.Assembly, "tests/detectors/assembly/inline_assembly_library.sol", "0.4.25"),
    Test(
        all_detectors.Assembly,
        "tests/detectors/assembly/inline_assembly_contract-0.5.1.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.Assembly,
        "tests/detectors/assembly/inline_assembly_library-0.5.1.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.LowLevelCalls, "tests/detectors/low-level-calls/low_level_calls.sol", "0.4.25"
    ),
    Test(
        all_detectors.LowLevelCalls, "tests/detectors/low-level-calls/low_level_calls.sol", "0.5.1"
    ),
    Test(
        all_detectors.ConstCandidateStateVars,
        "tests/detectors/constable-states/const_state_variables.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ConstCandidateStateVars,
        "tests/detectors/constable-states/const_state_variables.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/external_function.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/external_function_2.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/external_function.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.ExternalFunction,
        "tests/detectors/external-function/external_function_2.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.NamingConvention,
        "tests/detectors/naming-convention/naming_convention.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.NamingConvention,
        "tests/detectors/naming-convention/naming_convention.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.ControlledDelegateCall,
        "tests/detectors/controlled-delegatecall/controlled_delegatecall.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ControlledDelegateCall,
        "tests/detectors/controlled-delegatecall/controlled_delegatecall.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.UninitializedLocalVars,
        "tests/detectors/uninitialized-local/uninitialized_local_variable.sol",
        "0.4.25",
    ),
    Test(all_detectors.ConstantFunctionsAsm, "tests/detectors/constant/constant.sol", "0.4.25"),
    Test(all_detectors.ConstantFunctionsState, "tests/detectors/constant/constant.sol", "0.4.25"),
    Test(
        all_detectors.ConstantFunctionsAsm, "tests/detectors/constant/constant-0.5.1.sol", "0.5.1"
    ),
    Test(
        all_detectors.ConstantFunctionsState, "tests/detectors/constant/constant-0.5.1.sol", "0.5.1"
    ),
    Test(
        all_detectors.UnusedReturnValues,
        "tests/detectors/unused-return/unused_return.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnusedReturnValues, "tests/detectors/unused-return/unused_return.sol", "0.5.1"
    ),
    Test(
        all_detectors.UnusedReturnValues,
        "tests/detectors/unused-return/unused_return-sol7.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.UnusedReturnValuesTransfers,
        "tests/detectors/unused-return-transfers/unused_return_transfers.sol",
        "0.7.6",
    ),
    Test(
        all_detectors.ShadowingAbstractDetection,
        "tests/detectors/shadowing-abstract/shadowing_abstract.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.StateShadowing,
        "tests/detectors/shadowing-state/shadowing_state_variable.sol",
        "0.4.25",
    ),
    Test(all_detectors.Timestamp, "tests/detectors/timestamp/timestamp.sol", "0.4.25"),
    Test(all_detectors.Timestamp, "tests/detectors/timestamp/timestamp.sol", "0.5.1"),
    Test(
        all_detectors.MultipleCallsInLoop,
        "tests/detectors/calls-loop/multiple_calls_in_loop.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.BuiltinSymbolShadowing,
        "tests/detectors/shadowing-builtin/shadowing_builtin_symbols.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.LocalShadowing,
        "tests/detectors/shadowing-local/shadowing_local_variable.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.RightToLeftOverride,
        "tests/detectors/rtlo/right_to_left_override.sol",
        "0.4.25",
    ),
    Test(all_detectors.VoidConstructor, "tests/detectors/void-cst/void-cst.sol", "0.5.1"),
    Test(
        all_detectors.UncheckedSend,
        "tests/detectors/unchecked-send/unchecked_send-0.5.1.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.ReentrancyEvent,
        "tests/detectors/reentrancy-events/reentrancy-0.5.1-events.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.IncorrectStrictEquality,
        "tests/detectors/incorrect-equality/incorrect_equality.sol",
        "0.5.1",
    ),
    Test(
        all_detectors.TooManyDigits, "tests/detectors/too-many-digits/too_many_digits.sol", "0.5.1"
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "tests/detectors/unprotected-upgrade/Buggy.sol",
        "0.6.12",
    ),
    Test(
        all_detectors.UnprotectedUpgradeable,
        "tests/detectors/unprotected-upgrade/Fixed.sol",
        "0.6.12",
    ),
    Test(
        all_detectors.NamingConvention,
        "tests/detectors/naming-convention/naming_convention_ignore.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ABIEncoderV2Array,
        "tests/detectors/abiencoderv2-array/storage_ABIEncoderV2_array.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ArrayByReference,
        "tests/detectors/array-by-reference/array_by_reference.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.AssertStateChange,
        "tests/detectors/assert-state-change/assert_state_change.sol",
        "0.5.8",
    ),
    Test(
        all_detectors.ArrayLengthAssignment,
        "tests/detectors/controlled-array-length/array_length_assignment.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.CostlyOperationsInLoop,
        "tests/detectors/costly-loop/multiple_costly_operations_in_loop.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.FunctionInitializedState,
        "tests/detectors/function-init-state/function_init_state_variables.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MappingDeletionDetection,
        "tests/detectors/mapping-deletion/MappingDeletion.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "tests/detectors/missing-inheritance/unimplemented_interfaces.sol",
        "0.5.12",
    ),
    Test(
        all_detectors.PublicMappingNested,
        "tests/detectors/public-mappings-nested/public_mappings_nested.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.RedundantStatements,
        "tests/detectors/redundant-statements/redundant_statements.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.ReusedBaseConstructor,
        "tests/detectors/reused-constructor/reused_base_constructor.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.StorageSignedIntegerArray,
        "tests/detectors/storage-array/storage_signed_integer_array.sol",
        "0.5.8",
    ),
    Test(
        all_detectors.UnimplementedFunctionDetection,
        "tests/detectors/unimplemented-functions/unimplemented.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.UninitializedFunctionPtrsConstructor,
        "tests/detectors/uninitialized-fptr-cst/uninitialized_function_ptr_constructor.sol",
        "0.5.8",
    ),
    Test(all_detectors.BadPRNG, "tests/detectors/weak-prng/bad_prng.sol", "0.4.25"),
    Test(
        all_detectors.MissingEventsArithmetic,
        "tests/detectors/events-access/missing_events_access_control.sol",
        "0.5.12",
    ),
    Test(
        all_detectors.MissingEventsArithmetic,
        "tests/detectors/events-maths/missing_events_arithmetic.sol",
        "0.5.12",
    ),
    Test(
        all_detectors.ModifierDefaultDetection,
        "tests/detectors/incorrect-modifier/modifier_default.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.IncorrectUnaryExpressionDetection,
        "tests/detectors/incorrect-unary/invalid_unary_expression.sol",
        "0.4.25",
    ),
    Test(
        all_detectors.MissingZeroAddressValidation,
        "tests/detectors/missing-zero-check/missing_zero_address_validation.sol",
        "0.5.12",
    ),
    Test(
        all_detectors.PredeclarationUsageLocal,
        "tests/detectors/variable-scope/predeclaration_usage_local.sol",
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
