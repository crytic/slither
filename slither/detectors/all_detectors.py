# pylint: disable=unused-import,relative-beyond-top-level
from .examples.backdoor import Backdoor
from .variables.uninitialized_state_variables import UninitializedStateVarsDetection
from .variables.uninitialized_storage_variables import UninitializedStorageVars
from .variables.uninitialized_local_variables import UninitializedLocalVars
from .attributes.constant_pragma import ConstantPragma
from .attributes.incorrect_solc import IncorrectSolc
from .attributes.locked_ether import LockedEther
from .functions.arbitrary_send import ArbitrarySend
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
from .naming_convention.naming_convention import NamingConvention
from .functions.external_function import ExternalFunction
from .statements.controlled_delegatecall import ControlledDelegateCall
from .attributes.const_functions_asm import ConstantFunctionsAsm
from .attributes.const_functions_state import ConstantFunctionsState
from .shadowing.abstract import ShadowingAbstractDetection
from .shadowing.state import StateShadowing
from .shadowing.local import LocalShadowing
from .shadowing.builtin_symbols import BuiltinSymbolShadowing
from .operations.block_timestamp import Timestamp
from .statements.calls_in_loop import MultipleCallsInLoop
from .statements.incorrect_strict_equality import IncorrectStrictEquality
from .erc.incorrect_erc20_interface import IncorrectERC20InterfaceDetection
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
from .slither.name_reused import NameReused

#
#
