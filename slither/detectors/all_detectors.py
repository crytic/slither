# pylint: disable=unused-import,relative-beyond-top-level
from .examples.backdoor import Backdoor
from .variables.uninitialized_state_variables import UninitializedStateVarsDetection
from .variables.uninitialized_storage_variables import UninitializedStorageVars
from .variables.uninitialized_local_variables import UninitializedLocalVars
from .attributes.constant_pragma import ConstantPragma
from .attributes.incorrect_solc import IncorrectSolc
from .attributes.locked_ether import LockedEther
from .functions.arbitrary_send_eth import ArbitrarySendEth
from .erc.erc20.arbitrary_send_erc20_no_permit import ArbitrarySendErc20NoPermit
from .erc.erc20.arbitrary_send_erc20_permit import ArbitrarySendErc20Permit
from .functions.suicidal import Suicidal

# from .functions.complex_function import ComplexFunction
from .reentrancy.reentrancy_benign import ReentrancyBenign
from .reentrancy.reentrancy_read_before_write import ReentrancyReadBeforeWritten
from .reentrancy.reentrancy_eth import ReentrancyEth
from .reentrancy.reentrancy_no_gas import ReentrancyNoGas
from .reentrancy.reentrancy_events import ReentrancyEvent
from .variables.unused_state_variables import UnusedStateVars
from .variables.possible_const_state_variables import ConstCandidateStateVars
from .statements.tx_origin import TxOrigin
from .statements.assembly import Assembly
from .operations.low_level_calls import LowLevelCalls
from .operations.unused_return_values import UnusedReturnValues
from .operations.unchecked_transfer import UncheckedTransfer
from .naming_convention.naming_convention import NamingConvention
from .functions.external_function import ExternalFunction
from .statements.controlled_delegatecall import ControlledDelegateCall
from .attributes.const_functions_asm import ConstantFunctionsAsm
from .attributes.const_functions_state import ConstantFunctionsState
from .shadowing.abstract import ShadowingAbstractDetection
from .shadowing.state import StateShadowing
from .shadowing.local import LocalShadowing
from .shadowing.return_local import ReturnShadowsLocal
from .shadowing.builtin_symbols import BuiltinSymbolShadowing
from .operations.block_timestamp import Timestamp
from .statements.calls_in_loop import MultipleCallsInLoop
from .statements.incorrect_strict_equality import IncorrectStrictEquality
from .erc.erc20.incorrect_erc20_interface import IncorrectERC20InterfaceDetection
from .erc.incorrect_erc721_interface import IncorrectERC721InterfaceDetection
from .erc.unindexed_event_parameters import UnindexedERC20EventParameters
from .statements.deprecated_calls import DeprecatedStandards
from .source.rtlo import RightToLeftOverride
from .statements.too_many_digits import TooManyDigits
from .operations.unchecked_low_level_return_values import UncheckedLowLevel
from .operations.unchecked_send_return_value import UncheckedSend
from .operations.void_constructor import VoidConstructor
from .statements.type_based_tautology import TypeBasedTautology
from .statements.boolean_constant_equality import BooleanEquality
from .statements.boolean_constant_misuse import BooleanConstantMisuse
from .statements.divide_before_multiply import DivideBeforeMultiply
from .statements.unprotected_upgradeable import UnprotectedUpgradeable
from .slither.name_reused import NameReused

from .functions.unimplemented import UnimplementedFunctionDetection
from .statements.mapping_deletion import MappingDeletionDetection
from .statements.array_length_assignment import ArrayLengthAssignment
from .variables.similar_variables import SimilarVarsDetection
from .variables.function_init_state_variables import FunctionInitializedState
from .statements.redundant_statements import RedundantStatements
from .operations.bad_prng import BadPRNG
from .statements.costly_operations_in_loop import CostlyOperationsInLoop
from .statements.assert_state_change import AssertStateChange
from .attributes.unimplemented_interface import MissingInheritance
from .assembly.shift_parameter_mixup import ShiftParameterMixup
from .compiler_bugs.storage_signed_integer_array import StorageSignedIntegerArray
from .compiler_bugs.uninitialized_function_ptr_in_constructor import (
    UninitializedFunctionPtrsConstructor,
)
from .compiler_bugs.storage_ABIEncoderV2_array import ABIEncoderV2Array
from .compiler_bugs.array_by_reference import ArrayByReference
from .compiler_bugs.enum_conversion import EnumConversion
from .compiler_bugs.multiple_constructor_schemes import MultipleConstructorSchemes
from .compiler_bugs.public_mapping_nested import PublicMappingNested
from .compiler_bugs.reused_base_constructor import ReusedBaseConstructor
from .operations.missing_events_access_control import MissingEventsAccessControl
from .operations.missing_events_arithmetic import MissingEventsArithmetic
from .functions.modifier import ModifierDefaultDetection
from .variables.predeclaration_usage_local import PredeclarationUsageLocal
from .statements.unary import IncorrectUnaryExpressionDetection
from .operations.missing_zero_address_validation import MissingZeroAddressValidation
from .functions.dead_code import DeadCode
from .statements.write_after_write import WriteAfterWrite
from .statements.msg_value_in_loop import MsgValueInLoop
from .statements.delegatecall_in_loop import DelegatecallInLoop
from .functions.protected_variable import ProtectedVariables
