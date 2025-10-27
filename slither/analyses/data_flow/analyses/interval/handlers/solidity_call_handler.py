from typing import List
from decimal import Decimal

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
    IntervalRange,
)
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import (
    RangeVariable,
)
from slither.analyses.data_flow.analyses.interval.core.types.value_set import (
    ValueSet,
)
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.solidity_call import SolidityCall
from IPython import embed


class SolidityCallHandler:
    """Handler for Solidity call operations, specifically require/assert functions."""

    def __init__(self, constraint_storage: ConstraintManager = None):
        # Use provided constraint storage or create a new one
        if constraint_storage is not None:
            self.constraint_storage = constraint_storage
        else:
            self.constraint_storage = ConstraintManager()

    def handle_solidity_call(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle Solidity call operations including require/assert and calldataload"""

        logger.info(f"Handling solidity call: {operation.function.full_name}")
        require_assert_functions: List[str] = [
            "require(bool)",
            "assert(bool)",
            "require(bool,string)",
            "require(bool,error)",
        ]

        # Handle require/assert functions
        if operation.function.name in require_assert_functions:
            self._handle_require_assert(node, domain, operation)
            return

        # Handle calldataload function
        if operation.function.full_name == "calldataload(uint256)":
            self._handle_calldataload(node, domain, operation)
            return

        # Handle mload function
        if operation.function.full_name == "mload(uint256)":
            self._handle_mload(node, domain, operation)
            return

        # Handle revert function - mark branch as unreachable
        if "revert" in operation.function.full_name:
            self._handle_revert(node, domain, operation)
            return

        # Handle keccak256 hashing
        if operation.function.full_name == "keccak256(bytes)":
            self._handle_keccak256_bytes(node, domain, operation)
            return

        # Handle abi.encode / abi.encodePacked family -> returns bytes
        if operation.function.full_name in [
            "abi.encode()",
            "abi.encodePacked()",
            "abi.encodeWithSelector(bytes4)",
            "abi.encodeWithSignature(string)",
        ]:
            self._handle_abi_encode(node, domain, operation)
            return

        # Handle CREATE2 opcode exposed via solidity call wrappers
        if operation.function.full_name == "create2(uint256,uint256,uint256,uint256)":
            self._handle_create2(node, domain, operation)
            return

        # Handle byte() function
        if operation.function.full_name == "byte(uint256,uint256)":
            self._handle_byte(node, domain, operation)
            return

        # General handling for solidity's type(...) expressions.
        # Model any type(...) derived value as opaque bytes, since its content is not used numerically.
        if operation.function.full_name.startswith("type("):
            self._handle_type_code(node, domain, operation)
            return

        if "balance(address)" == operation.function.full_name:
            self._handle_balance(node, domain, operation)
            return

        # Handle gas-related functions
        if operation.function.full_name == "gas()":
            self._handle_gas(node, domain, operation)
            return

        # Handle returndatasize function
        if operation.function.full_name == "returndatasize()":
            self._handle_returndatasize(node, domain, operation)
            return

        # Handle call family functions - low-level calls to other contracts
        call_signatures = [
            # call variants (address is represented as uint256 in IR)
            "call(uint256,uint256,uint256,uint256,uint256,uint256,uint256)",  # Full call with 7 parameters
            "call(uint256,address,uint256,uint256,uint256,uint256,uint256)",  # Alternative signature
            "call(bytes)",  # Simple call with data
            "call(uint256,bytes)",  # Call with gas and data
            # delegatecall variants
            "delegatecall(bytes)",  # Simple delegatecall with data
            "delegatecall(uint256,bytes)",  # Delegatecall with gas and data
            "delegatecall(uint256,uint256,uint256,uint256,uint256,uint256)",  # Low-level delegatecall with 6 parameters
            # staticcall variants
            "staticcall(bytes)",  # Simple staticcall with data
            "staticcall(uint256,bytes)",  # Staticcall with gas and data
            "staticcall(uint256,uint256,uint256,uint256,uint256,uint256)",  # Low-level staticcall with 6 parameters
        ]
        if operation.function.full_name in call_signatures:
            self._handle_call(node, domain, operation)
            return

        if "ecrecover" in operation.function.full_name:
            self._handle_ecrecover(node, domain, operation)
            return

        if operation.function.full_name == "timestamp()":
            self._handle_timestamp(node, domain, operation)
            return

        if operation.function.full_name == "mulmod(uint256,uint256,uint256)":
            self._handle_mulmod(node, domain, operation)
            return

        if operation.function.full_name == "mstore(uint256,uint256)":
            self._handle_mstore(node, domain, operation)
            return

        if operation.function.full_name == "mstore8(uint256,uint256)":
            self._handle_mstore8(node, domain, operation)
            return

        if operation.function.full_name == "pop(uint256)":
            self._handle_pop(node, domain, operation)
            return

        if operation.function.full_name == "return(uint256,uint256)":
            self._handle_return(node, domain, operation)
            return

        if operation.function.full_name == "calldatacopy(uint256,uint256,uint256)":
            self._handle_calldatacopy(node, domain, operation)
            return

        if operation.function.full_name == "keccak256(uint256,uint256)":
            self._handle_keccak256_memory(node, domain, operation)
            return

        if operation.function.full_name == "returndatacopy(uint256,uint256,uint256)":
            self._handle_returndatacopy(node, domain, operation)
            return

        if (
            operation.function.full_name
            == "staticcall(uint256,uint256,uint256,uint256,uint256,uint256)"
        ):
            self._handle_staticcall(node, domain, operation)
            return

        # Handle ABI encoding/decoding functions
        if "abi.encode" in operation.function.full_name:
            self._handle_abi_encode(node, domain, operation)
            return

        if "abi.decode" in operation.function.full_name:
            self._handle_abi_decode(node, domain, operation)
            return

        if "abi.encodePacked" in operation.function.full_name:
            self._handle_abi_encode_packed(node, domain, operation)
            return

        if "abi.encodeWithSelector" in operation.function.full_name:
            self._handle_abi_encode_with_selector(node, domain, operation)
            return

        if "abi.encodeCall" in operation.function.full_name:
            self._handle_abi_encode_call(node, domain, operation)
            return

        if "abi.encodeWithSignature" in operation.function.full_name:
            self._handle_abi_encode_with_signature(node, domain, operation)
            return

        # Handle address members
        if "balance(address)" in operation.function.full_name:
            self._handle_address_balance(node, domain, operation)
            return

        if "code(address)" in operation.function.full_name:
            self._handle_address_code(node, domain, operation)
            return

        if "codehash(address)" in operation.function.full_name:
            self._handle_address_codehash(node, domain, operation)
            return

        if "call(address,bytes)" in operation.function.full_name:
            self._handle_address_call(node, domain, operation)
            return

        if "delegatecall(address,bytes)" in operation.function.full_name:
            self._handle_address_delegatecall(node, domain, operation)
            return

        if "staticcall(address,bytes)" in operation.function.full_name:
            self._handle_address_staticcall(node, domain, operation)
            return

        if "send(address,uint256)" in operation.function.full_name:
            self._handle_address_send(node, domain, operation)
            return

        if "transfer(address,uint256)" in operation.function.full_name:
            self._handle_address_transfer(node, domain, operation)
            return

        # Handle stop() function - identical to return(0, 0)
        if operation.function.full_name == "stop()":
            self._handle_stop(node, domain, operation)
            return


        # Handle storage operations
        if operation.function.full_name == "sload(uint256)":
            self._handle_sload(node, domain, operation)
            return

        if operation.function.full_name == "sstore(uint256,uint256)":
            self._handle_sstore(node, domain, operation)
            return

        if operation.function.full_name == "tload(uint256)":
            self._handle_tload(node, domain, operation)
            return

        if operation.function.full_name == "tstore(uint256,uint256)":
            self._handle_tstore(node, domain, operation)
            return

        # Handle memory operations
        if operation.function.full_name == "msize()":
            self._handle_msize(node, domain, operation)
            return

        if operation.function.full_name == "mcopy(uint256,uint256,uint256)":
            self._handle_mcopy(node, domain, operation)
            return

        # Handle context operations
        if operation.function.full_name == "address()":
            self._handle_address(node, domain, operation)
            return

        if operation.function.full_name == "selfbalance()":
            self._handle_selfbalance(node, domain, operation)
            return

        if operation.function.full_name == "caller()":
            self._handle_caller(node, domain, operation)
            return

        if operation.function.full_name == "callvalue()":
            self._handle_callvalue(node, domain, operation)
            return

        if operation.function.full_name == "calldatasize()":
            self._handle_calldatasize(node, domain, operation)
            return

        if operation.function.full_name == "codesize()":
            self._handle_codesize(node, domain, operation)
            return

        if operation.function.full_name == "codecopy(uint256,uint256,uint256)":
            self._handle_codecopy(node, domain, operation)
            return

        if operation.function.full_name == "extcodesize(uint256)":
            self._handle_extcodesize(node, domain, operation)
            return

        if operation.function.full_name == "extcodecopy(uint256,uint256,uint256,uint256)":
            self._handle_extcodecopy(node, domain, operation)
            return

        # Handle create operations
        if operation.function.full_name == "create(uint256,uint256,uint256)":
            self._handle_create(node, domain, operation)
            return

        # Handle callcode
        if operation.function.full_name == "callcode(uint256,uint256,uint256,uint256,uint256,uint256,uint256)":
            self._handle_callcode(node, domain, operation)
            return

        # Handle logging operations
        if operation.function.full_name == "log0(uint256,uint256)":
            self._handle_log0(node, domain, operation)
            return

        if operation.function.full_name == "log1(uint256,uint256,uint256)":
            self._handle_log1(node, domain, operation)
            return

        if operation.function.full_name == "log2(uint256,uint256,uint256,uint256)":
            self._handle_log2(node, domain, operation)
            return

        if operation.function.full_name == "log3(uint256,uint256,uint256,uint256,uint256)":
            self._handle_log3(node, domain, operation)
            return

        if operation.function.full_name == "log4(uint256,uint256,uint256,uint256,uint256,uint256)":
            self._handle_log4(node, domain, operation)
            return

        # Handle block context operations
        if operation.function.full_name == "chainid()":
            self._handle_chainid(node, domain, operation)
            return

        if operation.function.full_name == "basefee()":
            self._handle_basefee(node, domain, operation)
            return

        if operation.function.full_name == "blobbasefee()":
            self._handle_blobbasefee(node, domain, operation)
            return

        if operation.function.full_name == "origin()":
            self._handle_origin(node, domain, operation)
            return

        if operation.function.full_name == "gasprice()":
            self._handle_gasprice(node, domain, operation)
            return

        if operation.function.full_name == "blockhash(uint256)":
            self._handle_blockhash(node, domain, operation)
            return

        if operation.function.full_name == "blobhash(uint256)":
            self._handle_blobhash(node, domain, operation)
            return

        if operation.function.full_name == "coinbase()":
            self._handle_coinbase(node, domain, operation)
            return

        if operation.function.full_name == "number()":
            self._handle_number(node, domain, operation)
            return

        if operation.function.full_name == "difficulty()":
            self._handle_difficulty(node, domain, operation)
            return

        if operation.function.full_name == "prevrandao()":
            self._handle_prevrandao(node, domain, operation)
            return

        if operation.function.full_name == "gaslimit()":
            self._handle_gaslimit(node, domain, operation)
            return

        # Handle selfdestruct
        if operation.function.full_name == "selfdestruct(uint256)":
            self._handle_selfdestruct(node, domain, operation)
            return

        # Handle invalid
        if operation.function.full_name == "invalid()":
            self._handle_invalid(node, domain, operation)
            return

        # For other Solidity functions, log and continue without error
        logger.error(f"Unhandled Solidity function: {operation.function.name}")
        embed()
        raise ValueError(f"Unhandled Solidity function: {operation.function.name}")
        return

    def _handle_calldataload(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle calldataload operation by creating a variable with unknown range."""
        # calldataload returns 32 bytes of data from calldata, treat as uint256
        result_type = ElementaryType("uint256")
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )

        # Create range variable for the result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        if not operation.lvalue:
            logger.error("calldataload operation has no lvalue")
            raise ValueError("calldataload operation has no lvalue")

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        # logger.debug(f"Handled calldataload operation, created variable: {result_var_name}")

    def _handle_require_assert(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle require/assert functions by applying constraints from condition variables."""
        logger.info(f"Handling require/assert function: {operation.function.name}")
        if not operation.arguments:
            logger.error("Operation arguments are empty")
            raise ValueError("Operation arguments are empty")

        condition_variable = operation.arguments[0]

        # Try to apply constraint - the constraint applier will handle literals and variables
        try:
            self.constraint_storage.apply_constraint_from_variable(
                condition_variable, domain, operation
            )
        except ValueError as e:
            # If constraint cannot be applied (e.g., variable not found), set domain to TOP
            logger.warning(f"Could not apply constraint for require/assert: {e}")
            logger.info("Setting domain to TOP due to constraint application failure")
            domain.variant = DomainVariant.TOP
            return

        # Check if domain was set to TOP by the constraint applier (e.g., for assert(false))
        if domain.variant == DomainVariant.TOP:
            logger.info("Domain set to TOP by constraint applier")
            return

        # logger.debug(
        #     f"Require/assert function encountered: {operation.function.name} with condition: {condition_variable}"
        # )

    def _handle_mload(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle mload operation by creating a variable with appropriate range."""
        # mload returns 32 bytes of data from memory, treat as uint256
        result_type = ElementaryType("uint256")

        # For now, treat mload as having full uint256 range
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )

        # Create range variable for the result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        if not operation.lvalue:
            logger.error("mload operation has no lvalue")
            raise ValueError("mload operation has no lvalue")

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        # logger.debug(f"Handled mload operation, created variable: {result_var_name}")

    def _handle_byte(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle byte(n, x) operation - extracts the nth byte from x."""
        # byte(n, x) returns the nth byte of x, where the most significant byte is the 0th byte
        # The result is always a uint8 (0-255)

        if not operation.arguments or len(operation.arguments) != 2:
            logger.error(
                f"byte operation requires exactly 2 arguments, got {len(operation.arguments) if operation.arguments else 0}"
            )
            raise ValueError(f"byte operation requires exactly 2 arguments")

        if not operation.lvalue:
            logger.error("byte operation has no lvalue")
            raise ValueError("byte operation has no lvalue")

        # Get the arguments: n (byte index) and x (source value)
        byte_index_arg = operation.arguments[0]
        source_value_arg = operation.arguments[1]

        # Get the range information for the source value
        logger.info(f"Getting range information for source value: {source_value_arg}")
        source_range = RangeVariable.get_variable_info(domain, source_value_arg)

        # The result is always a uint8 (0-255)
        result_type = ElementaryType("uint8")
        result_range = IntervalRange(
            lower_bound=result_type.min,  # 0
            upper_bound=result_type.max,  # 255
        )

        # Create range variable for the result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)

        # logger.debug(f"Handled byte operation: byte({byte_index_arg}, {source_value_arg}) -> {result_var_name} (uint8)")

    def _handle_revert(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle revert operation by marking the branch as unreachable."""
        # Mark the domain as unreachable (TOP) to indicate this branch should not continue
        # to the final analysis
        domain.variant = DomainVariant.TOP

    def _handle_keccak256_bytes(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle keccak256(bytes memory) returning bytes32."""
        if not operation.lvalue:
            logger.error("keccak256(bytes) operation has no lvalue")
            raise ValueError("keccak256(bytes) operation has no lvalue")

        result_type = ElementaryType("bytes32")
        # Hash output is opaque; we model as unconstrained bytes32 (no numeric intervals)
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled keccak256(bytes) call, created variable: {result_var_name} (bytes32)")

    def _handle_abi_encode(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle abi.encode / abi.encodePacked returning bytes memory."""
        if not operation.lvalue:
            logger.error("abi.encode operation has no lvalue")
            raise ValueError("abi.encode operation has no lvalue")

        result_type = ElementaryType("bytes")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)

    #        logger.debug(f"Handled {operation.function.name} -> {result_var_name} (bytes)")

    def _handle_type_code(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle solidity type(...) expressions conservatively as bytes memory."""
        if not operation.lvalue:
            logger.error("type(...) operation has no lvalue")
            raise ValueError("type(...) operation has no lvalue")

        result_type = ElementaryType("bytes")
        # Treat as dynamic bytes with unknown contents/length
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)

    #        logger.debug(f"Handled {operation.function.name} -> {result_var_name} (bytes)")

    def _handle_create2(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle create2(v, p, n, s) operation: create new contract with code mem[p…(p+n)) at address keccak256(0xff . this . s . keccak256(mem[p…(p+n)))) and send v wei and return the new address; returns 0 on error."""
        logger.debug(f"Handling create2 operation: {operation}")

        if not operation.lvalue:
            logger.error("create2 operation has no lvalue")
            raise ValueError("create2 operation has no lvalue")

        # Validate argument count
        if not operation.arguments or len(operation.arguments) != 4:
            logger.warning(
                f"create2 operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        v_arg, p_arg, n_arg, s_arg = operation.arguments
        variable_manager = VariableInfoManager()
        v_name = variable_manager.get_variable_name(v_arg)
        p_name = variable_manager.get_variable_name(p_arg)
        n_name = variable_manager.get_variable_name(n_arg)
        s_name = variable_manager.get_variable_name(s_arg)
        result_var_name = variable_manager.get_variable_name(operation.lvalue)

        # create2 returns the new contract address or 0 on error
        # The exact address is computed as: keccak256(0xff . this . s . keccak256(mem[p…(p+n))))
        # Since this depends on runtime values we can't determine, we model it as:
        # - 0 on failure (address = 0)
        # - Any valid address on success
        result_type = ElementaryType("address")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(
            f"create2: create contract with {v_name} wei, code at mem[{p_name}...{p_name}+{n_name}], salt {s_name} -> {result_var_name} (address or 0)"
        )

    def _handle_balance(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle balance(address) operation returning uint256."""
        if not operation.lvalue:
            logger.error("balance(address) operation has no lvalue")
            raise ValueError("balance(address) operation has no lvalue")

        result_type = ElementaryType("uint256")

        # Get the full range for uint256 type
        variable_manager = VariableInfoManager()
        type_bounds = variable_manager.get_type_bounds(result_type)

        result_range_variable = RangeVariable(
            interval_ranges=[type_bounds],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled balance(address) call -> {result_var_name} (uint256)")

    def _handle_call(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle call, delegatecall, and staticcall operations.

        Supports:
        - call(g, a, v, in, insize, out, outsize) - low-level assembly call (7 args)
        - call(bytes) - high-level call with data (1 arg)
        - call(uint256, bytes) - high-level call with gas and data (2 args)
        - delegatecall(bytes) - delegatecall with data (1 arg)
        - delegatecall(uint256, bytes) - delegatecall with gas and data (2 args)
        - delegatecall(uint256, uint256, uint256, uint256, uint256, uint256) - low-level delegatecall (6 args)
        - staticcall(bytes) - staticcall with data (1 arg)
        - staticcall(uint256, bytes) - staticcall with gas and data (2 args)
        - staticcall(uint256, uint256, uint256, uint256, uint256, uint256) - low-level staticcall (6 args)

        All call family functions return:
        - 0 on error (e.g. out of gas, revert)
        - 1 on success
        """
        if not operation.lvalue:
            logger.error("call operation has no lvalue")
            raise ValueError("call operation has no lvalue")

        # Validate argument count based on the specific call signature
        arg_count = len(operation.arguments) if operation.arguments else 0
        valid_arg_counts = {
            1,
            2,
            6,
            7,
        }  # call(bytes), call(uint256,bytes), delegatecall/staticcall with 6 args, call with 7 args

        if arg_count not in valid_arg_counts:
            logger.error(f"call operation requires 1, 2, 6, or 7 arguments, got {arg_count}")
            raise ValueError(f"call operation requires 1, 2, 6, or 7 arguments, got {arg_count}")

        # The result is always 0 or 1 (failure or success)
        result_type = ElementaryType("uint256")

        # Create range variable with values [0, 1] for call success/failure
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("1"))],
            valid_values=ValueSet(
                {Decimal("0"), Decimal("1")}
            ),  # Explicitly model both possible values
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)

        # logger.debug(f"Handled {operation.function.name} -> {result_var_name} (uint256, range [0,1])")

    def _handle_gas(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle gas() operation returning remaining gas as uint256."""
        if not operation.lvalue:
            logger.error("gas() operation has no lvalue")
            raise ValueError("gas() operation has no lvalue")

        # gas() returns the remaining gas (0 to block gas limit)
        result_type = ElementaryType("uint256")

        # Create range variable for remaining gas (0 to reasonable gas limit)
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("50000000"))],  # 0 to 50M gas
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)

        # logger.debug(f"Handled gas() -> {result_var_name} (uint256, range [0,50000000])")

    def _handle_returndatasize(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle returndatasize() operation returning size of return data."""
        if not operation.lvalue:
            logger.error("returndatasize() operation has no lvalue")
            raise ValueError("returndatasize() operation has no lvalue")

        # returndatasize() returns the size of return data from last call (0 to reasonable size)
        result_type = ElementaryType("uint256")

        # Return data size is typically 0 to a few KB, but could theoretically be larger
        # We'll use a reasonable upper bound
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("1048576"))],  # 0 to 1MB
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)

        # logger.debug(f"Handled returndatasize() -> {result_var_name} (uint256, range [0,1048576])")

    def _handle_ecrecover(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle ecrecover(bytes32, uint8, bytes32, bytes32) returning address or zero on error."""
        if not operation.lvalue:
            logger.error("ecrecover operation has no lvalue")
            raise ValueError("ecrecover operation has no lvalue")

        arg_count = len(operation.arguments) if operation.arguments else 0
        if arg_count != 4:
            logger.error(f"ecrecover requires exactly 4 arguments, got {arg_count}")
            raise ValueError(f"ecrecover requires exactly 4 arguments, got {arg_count}")

        result_type = ElementaryType("address")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)

    def _handle_timestamp(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle timestamp() operation returning the current block timestamp as uint256."""
        if not operation.lvalue:
            logger.error("timestamp() operation has no lvalue")
            raise ValueError("timestamp() operation has no lvalue")

        from datetime import datetime

        now = datetime.now()
        timestamp = int(now.timestamp())

        result_type = ElementaryType("uint256")

        # We use current timestamp as a reasonable upper bound for analysis
        timestamp_range = IntervalRange(
            lower_bound=Decimal("0"),
            upper_bound=Decimal(str(timestamp)),
        )

        # Create range variable for the timestamp
        result_range_variable = RangeVariable(
            interval_ranges=[timestamp_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)

        # logger.debug(f"Handled timestamp() -> {result_var_name} (uint256, range [0,{timestamp}])")

    def _handle_mulmod(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle mulmod(x, y, m) operation: (x * y) % m with arbitrary precision arithmetic."""
        from decimal import Decimal
        from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
            IntervalRange,
        )

        if not operation.lvalue:
            logger.error("mulmod operation has no lvalue")
            raise ValueError("mulmod operation has no lvalue")

        # Validate argument count
        if not operation.arguments or len(operation.arguments) != 3:
            logger.error(
                f"mulmod operation requires 3 arguments, got {len(operation.arguments) if operation.arguments else 0}"
            )
            raise ValueError(
                f"mulmod operation requires 3 arguments, got {len(operation.arguments) if operation.arguments else 0}"
            )

        x_arg, y_arg, m_arg = operation.arguments
        result_type = ElementaryType("uint256")

        # Get variable names
        variable_manager = VariableInfoManager()
        x_name = variable_manager.get_variable_name(x_arg)
        y_name = variable_manager.get_variable_name(y_arg)
        m_name = variable_manager.get_variable_name(m_arg)
        result_var_name = variable_manager.get_variable_name(operation.lvalue)

        logger.debug(f"Handling mulmod({x_name}, {y_name}, {m_name})")

        # Check if all arguments exist in domain state
        if not (
            domain.state.has_range_variable(x_name)
            and domain.state.has_range_variable(y_name)
            and domain.state.has_range_variable(m_name)
        ):
            logger.warning(
                f"Some mulmod arguments not found in domain state, creating conservative result"
            )
            # Create conservative result (full uint256 range)
            result_range_variable = RangeVariable(
                interval_ranges=[IntervalRange(Decimal("0"), Decimal(str(result_type.max)))],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=result_type,
            )
            domain.state.set_range_variable(result_var_name, result_range_variable)
            return

        # Get argument range variables
        x_range_var = domain.state.get_range_variable(x_name)
        y_range_var = domain.state.get_range_variable(y_name)
        m_range_var = domain.state.get_range_variable(m_name)

        # Compute mulmod result
        result_range_var = self._compute_mulmod(x_range_var, y_range_var, m_range_var, result_type)

        # Store the result
        domain.state.set_range_variable(result_var_name, result_range_var)
        logger.debug(f"Computed mulmod result: {result_range_var}")

    def _compute_mulmod(
        self,
        x_range_var: RangeVariable,
        y_range_var: RangeVariable,
        m_range_var: RangeVariable,
        result_type: ElementaryType,
    ) -> RangeVariable:
        """Compute mulmod(x, y, m) = (x * y) % m with arbitrary precision arithmetic."""
        from decimal import Decimal
        from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
            IntervalRange,
        )

        result_valid_values = ValueSet(set())
        result_interval_ranges = []

        # Handle discrete values
        if (
            not x_range_var.valid_values.is_empty()
            and not y_range_var.valid_values.is_empty()
            and not m_range_var.valid_values.is_empty()
        ):

            for x_val in x_range_var.valid_values:
                for y_val in y_range_var.valid_values:
                    for m_val in m_range_var.valid_values:
                        if m_val == 0:
                            # mulmod returns 0 if m == 0
                            result_valid_values.add(Decimal("0"))
                        else:
                            # Compute (x * y) % m with arbitrary precision
                            product = x_val * y_val
                            result = product % m_val
                            result_valid_values.add(result)

        # Handle interval ranges (more complex)
        if (
            x_range_var.interval_ranges
            and y_range_var.interval_ranges
            and m_range_var.interval_ranges
        ):

            for x_interval in x_range_var.interval_ranges:
                for y_interval in y_range_var.interval_ranges:
                    for m_interval in m_range_var.interval_ranges:
                        # For interval ranges, we need to be conservative
                        # The result of mulmod with intervals is complex to compute exactly
                        # We'll use a conservative approximation

                        # If m can be 0, result can be 0
                        if m_interval.lower_bound <= 0:
                            # Result can be 0 when m == 0
                            result_interval_ranges.append(IntervalRange(Decimal("0"), Decimal("0")))

                        # If m > 0, result is in [0, m-1]
                        if m_interval.lower_bound > 0:
                            max_result = m_interval.upper_bound - 1
                            result_interval_ranges.append(IntervalRange(Decimal("0"), max_result))

        # If we have no specific constraints, use conservative bounds
        if result_valid_values.is_empty() and not result_interval_ranges:
            # Conservative: result is in [0, max_uint256] since we can't determine exact bounds
            result_interval_ranges.append(
                IntervalRange(Decimal("0"), Decimal(str(result_type.max)))
            )

        return RangeVariable(
            interval_ranges=result_interval_ranges,
            valid_values=result_valid_values,
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

    def _handle_mstore(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle mstore(p, v) operation: mem[p…(p+32)) := v."""
        logger.debug(f"Handling mstore operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 2:
            logger.warning(
                f"mstore operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        p_arg, v_arg = operation.arguments
        variable_manager = VariableInfoManager()
        p_name = variable_manager.get_variable_name(p_arg)
        v_name = variable_manager.get_variable_name(v_arg)

        # Track the memory operation by creating a range variable for the memory location
        # This helps with tracking what values are stored in memory
        memory_var_name = f"mem_{p_name}"

        # Get the value being stored
        if domain.state.has_range_variable(v_name):
            stored_value = domain.state.get_range_variable(v_name)
            # Create a copy of the stored value for the memory location
            memory_range_variable = stored_value.deep_copy()
        else:
            # If we don't know the value being stored, create a conservative range
            result_type = ElementaryType("uint256")
            result_range = IntervalRange(
                lower_bound=result_type.min,
                upper_bound=result_type.max,
            )
            memory_range_variable = RangeVariable(
                interval_ranges=[result_range],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=result_type,
            )

        # Store the memory location in domain state
        domain.state.set_range_variable(memory_var_name, memory_range_variable)
        logger.debug(
            f"mstore: stored value {v_name} at memory position {p_name} -> {memory_var_name}"
        )

    def _handle_mstore8(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle mstore8(p, v) operation: mem[p] := v & 0xff (only modifies a single byte)."""
        logger.debug(f"Handling mstore8 operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 2:
            logger.warning(
                f"mstore8 operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        p_arg, v_arg = operation.arguments
        variable_manager = VariableInfoManager()
        p_name = variable_manager.get_variable_name(p_arg)
        v_name = variable_manager.get_variable_name(v_arg)

        # Track the memory operation by creating a range variable for the memory location
        # This helps with tracking what values are stored in memory
        memory_var_name = f"mem8_{p_name}"

        # Get the value being stored (but only the low byte)
        if domain.state.has_range_variable(v_name):
            stored_value = domain.state.get_range_variable(v_name)
            # For mstore8, we need to mask to only the low byte (0-255)
            result_type = ElementaryType("uint8")
            result_range = IntervalRange(
                lower_bound=Decimal("0"),
                upper_bound=Decimal("255"),
            )
            memory_range_variable = RangeVariable(
                interval_ranges=[result_range],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=result_type,
            )
        else:
            # If we don't know the value being stored, create a conservative range for byte
            result_type = ElementaryType("uint8")
            result_range = IntervalRange(
                lower_bound=Decimal("0"),
                upper_bound=Decimal("255"),
            )
            memory_range_variable = RangeVariable(
                interval_ranges=[result_range],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=result_type,
            )

        # Store the memory location in domain state
        domain.state.set_range_variable(memory_var_name, memory_range_variable)
        logger.debug(
            f"mstore8: stored byte (value & 0xff) of {v_name} at memory position {p_name} -> {memory_var_name}"
        )

    def _handle_pop(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle pop(x) operation: discard value x."""
        logger.debug(f"Handling pop operation: {operation}")

        # pop doesn't return a value, it discards a value from the stack
        # We don't need to create a range variable for the result
        # Just log the operation for debugging purposes

        if operation.arguments and len(operation.arguments) == 1:
            x_arg = operation.arguments[0]
            variable_manager = VariableInfoManager()
            x_name = variable_manager.get_variable_name(x_arg)
            logger.debug(f"pop: discarding value {x_name}")
        else:
            logger.warning(
                f"pop operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )

    def _handle_return(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle return(p, s) operation: end execution, return data mem[p…(p+s))."""
        logger.debug(f"Handling return operation: {operation}")

        # return doesn't return a value, it ends execution and returns data from memory
        # We don't need to create a range variable for the result
        # Just log the operation for debugging purposes

        if operation.arguments and len(operation.arguments) == 2:
            p_arg, s_arg = operation.arguments
            variable_manager = VariableInfoManager()
            p_name = variable_manager.get_variable_name(p_arg)
            s_name = variable_manager.get_variable_name(s_arg)
            logger.debug(
                f"return: ending execution, returning data from memory[{p_name}...{p_name}+{s_name})"
            )
        else:
            logger.warning(
                f"return operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )

    def _handle_calldatacopy(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle calldatacopy(t, f, s) operation: copy s bytes from calldata at position f to mem at position t."""
        logger.debug(f"Handling calldatacopy operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 3:
            logger.warning(
                f"calldatacopy operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        t_arg, f_arg, s_arg = operation.arguments
        variable_manager = VariableInfoManager()
        t_name = variable_manager.get_variable_name(t_arg)
        f_name = variable_manager.get_variable_name(f_arg)
        s_name = variable_manager.get_variable_name(s_arg)

        # Track the memory operation by creating a range variable for the memory location
        # This helps with tracking what values are copied to memory
        memory_var_name = f"mem_copied_{t_name}"

        # For calldatacopy, we don't know the exact values being copied from calldata
        # So we create a conservative range for the copied data
        result_type = ElementaryType("uint256")
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )
        memory_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the memory location in domain state
        domain.state.set_range_variable(memory_var_name, memory_range_variable)
        logger.debug(
            f"calldatacopy: copied {s_name} bytes from calldata[{f_name}] to memory[{t_name}] -> {memory_var_name}"
        )

    def _handle_keccak256_memory(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle keccak256(p, n) operation: keccak(mem[p…(p+n))) returning uint256."""
        logger.debug(f"Handling keccak256(uint256,uint256) operation: {operation}")

        if not operation.lvalue:
            logger.error("keccak256(uint256,uint256) operation has no lvalue")
            raise ValueError("keccak256(uint256,uint256) operation has no lvalue")

        if not operation.arguments or len(operation.arguments) != 2:
            logger.warning(
                f"keccak256(uint256,uint256) operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        p_arg, n_arg = operation.arguments
        variable_manager = VariableInfoManager()
        p_name = variable_manager.get_variable_name(p_arg)
        n_name = variable_manager.get_variable_name(n_arg)
        result_var_name = variable_manager.get_variable_name(operation.lvalue)

        # keccak256 returns a 32-byte hash, treat as uint256
        result_type = ElementaryType("uint256")

        # For keccak256, we can't determine the exact hash value without knowing the input data
        # So we create a conservative range for the hash result
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )

        # Create range variable for the hash result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(
            f"keccak256(uint256,uint256): computed hash of memory[{p_name}...{p_name}+{n_name}] -> {result_var_name}"
        )

    def _handle_returndatacopy(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle returndatacopy(t, f, s) operation: copy s bytes from returndata at position f to mem at position t."""
        logger.debug(f"Handling returndatacopy operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 3:
            logger.warning(
                f"returndatacopy operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        t_arg, f_arg, s_arg = operation.arguments
        variable_manager = VariableInfoManager()
        t_name = variable_manager.get_variable_name(t_arg)
        f_name = variable_manager.get_variable_name(f_arg)
        s_name = variable_manager.get_variable_name(s_arg)

        # Track the memory operation by creating a range variable for the memory location
        # This helps with tracking what values are copied to memory
        memory_var_name = f"mem_returndata_{t_name}"

        # For returndatacopy, we don't know the exact values being copied from returndata
        # So we create a conservative range for the copied data
        result_type = ElementaryType("uint256")
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )
        memory_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the memory location in domain state
        domain.state.set_range_variable(memory_var_name, memory_range_variable)
        logger.debug(
            f"returndatacopy: copied {s_name} bytes from returndata[{f_name}] to memory[{t_name}] -> {memory_var_name}"
        )

    def _handle_staticcall(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle staticcall(g, a, in, insize, out, outsize) operation: static call to contract."""
        logger.debug(f"Handling staticcall operation: {operation}")

        if not operation.lvalue:
            logger.error("staticcall operation has no lvalue")
            raise ValueError("staticcall operation has no lvalue")

        if not operation.arguments or len(operation.arguments) != 6:
            logger.warning(
                f"staticcall operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        g_arg, a_arg, in_arg, insize_arg, out_arg, outsize_arg = operation.arguments
        variable_manager = VariableInfoManager()
        g_name = variable_manager.get_variable_name(g_arg)
        a_name = variable_manager.get_variable_name(a_arg)
        in_name = variable_manager.get_variable_name(in_arg)
        insize_name = variable_manager.get_variable_name(insize_arg)
        out_name = variable_manager.get_variable_name(out_arg)
        outsize_name = variable_manager.get_variable_name(outsize_arg)
        result_var_name = variable_manager.get_variable_name(operation.lvalue)

        # staticcall returns success (1) or failure (0)
        result_type = ElementaryType("uint256")

        # For staticcall, we can't determine the exact result without knowing the call outcome
        # So we create a conservative range for the success/failure result
        result_range = IntervalRange(
            lower_bound=Decimal("0"),  # 0 = failure
            upper_bound=Decimal("1"),  # 1 = success
        )

        # Create range variable for the call result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(
            f"staticcall: called contract {a_name} with gas {g_name}, input[{in_name}...{in_name}+{insize_name}], output[{out_name}...{out_name}+{outsize_name}] -> {result_var_name}"
        )

    def _handle_abi_encode(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle abi.encode(...) operation: ABI-encodes the given arguments."""
        logger.debug(f"Handling abi.encode operation: {operation}")

        if not operation.lvalue:
            logger.error("abi.encode operation has no lvalue")
            raise ValueError("abi.encode operation has no lvalue")

        # abi.encode returns bytes memory
        result_type = ElementaryType("bytes")

        # For abi.encode, we can't determine the exact encoded data without knowing the input values
        # So we create a conservative range for the encoded bytes
        result_range = IntervalRange(
            lower_bound=Decimal("0"),
            upper_bound=Decimal(str(2**256 - 1)),  # Conservative upper bound
        )

        # Create range variable for the encoded result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"abi.encode: encoded arguments -> {result_var_name}")

    def _handle_abi_decode(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle abi.decode(bytes memory encodedData, (...)) operation: ABI-decodes the provided data."""
        logger.debug(f"Handling abi.decode operation: {operation}")

        if not operation.lvalue:
            logger.error("abi.decode operation has no lvalue")
            raise ValueError("abi.decode operation has no lvalue")

        # abi.decode returns the decoded values (type depends on the decode types)
        # For simplicity, we'll use a conservative approach
        result_type = ElementaryType("uint256")

        # For abi.decode, we can't determine the exact decoded values without knowing the encoded data
        # So we create a conservative range
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )

        # Create range variable for the decoded result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"abi.decode: decoded data -> {result_var_name}")

    def _handle_abi_encode_packed(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle abi.encodePacked(...) operation: Performs packed encoding of the given arguments."""
        logger.debug(f"Handling abi.encodePacked operation: {operation}")

        if not operation.lvalue:
            logger.error("abi.encodePacked operation has no lvalue")
            raise ValueError("abi.encodePacked operation has no lvalue")

        # abi.encodePacked returns bytes memory
        result_type = ElementaryType("bytes")

        # For abi.encodePacked, we can't determine the exact encoded data without knowing the input values
        # So we create a conservative range for the encoded bytes
        result_range = IntervalRange(
            lower_bound=Decimal("0"),
            upper_bound=Decimal(str(2**256 - 1)),  # Conservative upper bound
        )

        # Create range variable for the encoded result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"abi.encodePacked: packed encoded arguments -> {result_var_name}")

    def _handle_abi_encode_with_selector(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle abi.encodeWithSelector(bytes4 selector, ...) operation: ABI-encodes with selector."""
        logger.debug(f"Handling abi.encodeWithSelector operation: {operation}")

        if not operation.lvalue:
            logger.error("abi.encodeWithSelector operation has no lvalue")
            raise ValueError("abi.encodeWithSelector operation has no lvalue")

        # abi.encodeWithSelector returns bytes memory
        result_type = ElementaryType("bytes")

        # For abi.encodeWithSelector, we can't determine the exact encoded data without knowing the input values
        # So we create a conservative range for the encoded bytes
        result_range = IntervalRange(
            lower_bound=Decimal("0"),
            upper_bound=Decimal(str(2**256 - 1)),  # Conservative upper bound
        )

        # Create range variable for the encoded result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"abi.encodeWithSelector: encoded with selector -> {result_var_name}")

    def _handle_abi_encode_call(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle abi.encodeCall(function functionPointer, (...)) operation: ABI-encodes a call."""
        logger.debug(f"Handling abi.encodeCall operation: {operation}")

        if not operation.lvalue:
            logger.error("abi.encodeCall operation has no lvalue")
            raise ValueError("abi.encodeCall operation has no lvalue")

        # abi.encodeCall returns bytes memory
        result_type = ElementaryType("bytes")

        # For abi.encodeCall, we can't determine the exact encoded data without knowing the input values
        # So we create a conservative range for the encoded bytes
        result_range = IntervalRange(
            lower_bound=Decimal("0"),
            upper_bound=Decimal(str(2**256 - 1)),  # Conservative upper bound
        )

        # Create range variable for the encoded result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"abi.encodeCall: encoded call -> {result_var_name}")

    def _handle_abi_encode_with_signature(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle abi.encodeWithSignature(string memory signature, ...) operation: ABI-encodes with signature."""
        logger.debug(f"Handling abi.encodeWithSignature operation: {operation}")

        if not operation.lvalue:
            logger.error("abi.encodeWithSignature operation has no lvalue")
            raise ValueError("abi.encodeWithSignature operation has no lvalue")

        # abi.encodeWithSignature returns bytes memory
        result_type = ElementaryType("bytes")

        # For abi.encodeWithSignature, we can't determine the exact encoded data without knowing the input values
        # So we create a conservative range for the encoded bytes
        result_range = IntervalRange(
            lower_bound=Decimal("0"),
            upper_bound=Decimal(str(2**256 - 1)),  # Conservative upper bound
        )

        # Create range variable for the encoded result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"abi.encodeWithSignature: encoded with signature -> {result_var_name}")

    def _handle_address_balance(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle address.balance operation: balance of the Address in Wei."""
        logger.debug(f"Handling address.balance operation: {operation}")

        if not operation.lvalue:
            logger.error("address.balance operation has no lvalue")
            raise ValueError("address.balance operation has no lvalue")

        # address.balance returns uint256
        result_type = ElementaryType("uint256")

        # For address.balance, we can't determine the exact balance without knowing the address
        # So we create a conservative range
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )

        # Create range variable for the balance result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"address.balance: retrieved balance -> {result_var_name}")

    def _handle_address_code(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle address.code operation: code at the Address (can be empty)."""
        logger.debug(f"Handling address.code operation: {operation}")

        if not operation.lvalue:
            logger.error("address.code operation has no lvalue")
            raise ValueError("address.code operation has no lvalue")

        # address.code returns bytes memory
        result_type = ElementaryType("bytes")

        # For address.code, we can't determine the exact code without knowing the address
        # So we create a conservative range
        result_range = IntervalRange(
            lower_bound=Decimal("0"),
            upper_bound=Decimal(str(2**256 - 1)),  # Conservative upper bound
        )

        # Create range variable for the code result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"address.code: retrieved code -> {result_var_name}")

    def _handle_address_codehash(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle address.codehash operation: the codehash of the Address."""
        logger.debug(f"Handling address.codehash operation: {operation}")

        if not operation.lvalue:
            logger.error("address.codehash operation has no lvalue")
            raise ValueError("address.codehash operation has no lvalue")

        # address.codehash returns bytes32
        result_type = ElementaryType("bytes32")

        # For address.codehash, we can't determine the exact codehash without knowing the address
        # So we create a conservative range
        result_range = IntervalRange(
            lower_bound=Decimal("0"),
            upper_bound=Decimal(str(2**256 - 1)),  # Conservative upper bound
        )

        # Create range variable for the codehash result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"address.codehash: retrieved codehash -> {result_var_name}")

    def _handle_address_call(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle address.call(bytes memory) operation: issue low-level CALL."""
        logger.debug(f"Handling address.call operation: {operation}")

        if not operation.lvalue:
            logger.error("address.call operation has no lvalue")
            raise ValueError("address.call operation has no lvalue")

        # address.call returns (bool, bytes memory)
        # For simplicity, we'll handle the bool return value
        result_type = ElementaryType("bool")

        # For address.call, we can't determine the exact result without knowing the call outcome
        # So we create a conservative range for success/failure
        result_range = IntervalRange(
            lower_bound=Decimal("0"),  # false
            upper_bound=Decimal("1"),  # true
        )

        # Create range variable for the call result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"address.call: made call -> {result_var_name}")

    def _handle_address_delegatecall(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle address.delegatecall(bytes memory) operation: issue low-level DELEGATECALL."""
        logger.debug(f"Handling address.delegatecall operation: {operation}")

        if not operation.lvalue:
            logger.error("address.delegatecall operation has no lvalue")
            raise ValueError("address.delegatecall operation has no lvalue")

        # address.delegatecall returns (bool, bytes memory)
        # For simplicity, we'll handle the bool return value
        result_type = ElementaryType("bool")

        # For address.delegatecall, we can't determine the exact result without knowing the call outcome
        # So we create a conservative range for success/failure
        result_range = IntervalRange(
            lower_bound=Decimal("0"),  # false
            upper_bound=Decimal("1"),  # true
        )

        # Create range variable for the delegatecall result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"address.delegatecall: made delegatecall -> {result_var_name}")

    def _handle_address_staticcall(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle address.staticcall(bytes memory) operation: issue low-level STATICCALL."""
        logger.debug(f"Handling address.staticcall operation: {operation}")

        if not operation.lvalue:
            logger.error("address.staticcall operation has no lvalue")
            raise ValueError("address.staticcall operation has no lvalue")

        # address.staticcall returns (bool, bytes memory)
        # For simplicity, we'll handle the bool return value
        result_type = ElementaryType("bool")

        # For address.staticcall, we can't determine the exact result without knowing the call outcome
        # So we create a conservative range for success/failure
        result_range = IntervalRange(
            lower_bound=Decimal("0"),  # false
            upper_bound=Decimal("1"),  # true
        )

        # Create range variable for the staticcall result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"address.staticcall: made staticcall -> {result_var_name}")

    def _handle_address_send(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle address.send(uint256 amount) operation: send given amount of Wei to Address."""
        logger.debug(f"Handling address.send operation: {operation}")

        if not operation.lvalue:
            logger.error("address.send operation has no lvalue")
            raise ValueError("address.send operation has no lvalue")

        # address.send returns bool
        result_type = ElementaryType("bool")

        # For address.send, we can't determine the exact result without knowing the send outcome
        # So we create a conservative range for success/failure
        result_range = IntervalRange(
            lower_bound=Decimal("0"),  # false
            upper_bound=Decimal("1"),  # true
        )

        # Create range variable for the send result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"address.send: sent amount -> {result_var_name}")

    def _handle_address_transfer(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle address.transfer(uint256 amount) operation: send given amount of Wei to Address."""
        logger.debug(f"Handling address.transfer operation: {operation}")

        # address.transfer doesn't return a value, it throws on failure
        # We don't need to create a range variable for the result
        # Just log the operation for debugging purposes
        logger.debug(f"address.transfer: transferred amount (throws on failure)")

    def _handle_stop(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle stop() operation - identical to return(0, 0)."""
        logger.debug(f"Handling stop operation: {operation}")
        # stop() doesn't return a value, it ends execution
        # Just log the operation for debugging purposes
        logger.debug("stop: ending execution (identical to return(0, 0))")

    def _handle_sload(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle sload(p) operation: storage[p]."""
        logger.debug(f"Handling sload operation: {operation}")

        if not operation.lvalue:
            logger.error("sload operation has no lvalue")
            raise ValueError("sload operation has no lvalue")

        # sload returns 32 bytes from storage, treat as uint256
        result_type = ElementaryType("uint256")
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )

        # Create range variable for the result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled sload operation, created variable: {result_var_name}")

    def _handle_sstore(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle sstore(p, v) operation: storage[p] := v."""
        logger.debug(f"Handling sstore operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 2:
            logger.warning(
                f"sstore operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        p_arg, v_arg = operation.arguments
        variable_manager = VariableInfoManager()
        p_name = variable_manager.get_variable_name(p_arg)
        v_name = variable_manager.get_variable_name(v_arg)

        # Track the storage operation by creating a range variable for the storage location
        storage_var_name = f"storage_{p_name}"

        # Get the value being stored
        if domain.state.has_range_variable(v_name):
            stored_value = domain.state.get_range_variable(v_name)
            # Create a copy of the stored value for the storage location
            storage_range_variable = stored_value.deep_copy()
        else:
            # If we don't know the value being stored, create a conservative range
            result_type = ElementaryType("uint256")
            result_range = IntervalRange(
                lower_bound=result_type.min,
                upper_bound=result_type.max,
            )
            storage_range_variable = RangeVariable(
                interval_ranges=[result_range],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=result_type,
            )

        # Store the storage location in domain state
        domain.state.set_range_variable(storage_var_name, storage_range_variable)
        logger.debug(f"sstore: stored value {v_name} at storage position {p_name} -> {storage_var_name}")

    def _handle_tload(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle tload(p) operation: transientStorage[p]."""
        logger.debug(f"Handling tload operation: {operation}")

        if not operation.lvalue:
            logger.error("tload operation has no lvalue")
            raise ValueError("tload operation has no lvalue")

        # tload returns 32 bytes from transient storage, treat as uint256
        result_type = ElementaryType("uint256")
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )

        # Create range variable for the result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled tload operation, created variable: {result_var_name}")

    def _handle_tstore(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle tstore(p, v) operation: transientStorage[p] := v."""
        logger.debug(f"Handling tstore operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 2:
            logger.warning(
                f"tstore operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        p_arg, v_arg = operation.arguments
        variable_manager = VariableInfoManager()
        p_name = variable_manager.get_variable_name(p_arg)
        v_name = variable_manager.get_variable_name(v_arg)

        # Track the transient storage operation by creating a range variable for the storage location
        tstorage_var_name = f"tstorage_{p_name}"

        # Get the value being stored
        if domain.state.has_range_variable(v_name):
            stored_value = domain.state.get_range_variable(v_name)
            # Create a copy of the stored value for the transient storage location
            tstorage_range_variable = stored_value.deep_copy()
        else:
            # If we don't know the value being stored, create a conservative range
            result_type = ElementaryType("uint256")
            result_range = IntervalRange(
                lower_bound=result_type.min,
                upper_bound=result_type.max,
            )
            tstorage_range_variable = RangeVariable(
                interval_ranges=[result_range],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=result_type,
            )

        # Store the transient storage location in domain state
        domain.state.set_range_variable(tstorage_var_name, tstorage_range_variable)
        logger.debug(f"tstore: stored value {v_name} at transient storage position {p_name} -> {tstorage_var_name}")

    def _handle_msize(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle msize() operation: size of memory, i.e. largest accessed memory index."""
        logger.debug(f"Handling msize operation: {operation}")

        if not operation.lvalue:
            logger.error("msize operation has no lvalue")
            raise ValueError("msize operation has no lvalue")

        # msize() returns the size of memory in bytes
        result_type = ElementaryType("uint256")

        # Memory size is typically 0 to a few KB, but could theoretically be larger
        # We'll use a reasonable upper bound
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("1048576"))],  # 0 to 1MB
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled msize() -> {result_var_name} (uint256, range [0,1048576])")

    def _handle_mcopy(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle mcopy(t, f, s) operation: copy s bytes from mem at position f to mem at position t."""
        logger.debug(f"Handling mcopy operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 3:
            logger.warning(
                f"mcopy operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        t_arg, f_arg, s_arg = operation.arguments
        variable_manager = VariableInfoManager()
        t_name = variable_manager.get_variable_name(t_arg)
        f_name = variable_manager.get_variable_name(f_arg)
        s_name = variable_manager.get_variable_name(s_arg)

        # Track the memory operation by creating a range variable for the memory location
        # This helps with tracking what values are copied to memory
        memory_var_name = f"mem_copied_{t_name}"

        # For mcopy, we don't know the exact values being copied from memory
        # So we create a conservative range for the copied data
        result_type = ElementaryType("uint256")
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )
        memory_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the memory location in domain state
        domain.state.set_range_variable(memory_var_name, memory_range_variable)
        logger.debug(
            f"mcopy: copied {s_name} bytes from memory[{f_name}] to memory[{t_name}] -> {memory_var_name}"
        )

    def _handle_address(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle address() operation: address of the current contract / execution context."""
        logger.debug(f"Handling address operation: {operation}")

        if not operation.lvalue:
            logger.error("address operation has no lvalue")
            raise ValueError("address operation has no lvalue")

        # address() returns the current contract address
        result_type = ElementaryType("address")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled address() -> {result_var_name} (address)")

    def _handle_selfbalance(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle selfbalance() operation: equivalent to balance(address()), but cheaper."""
        logger.debug(f"Handling selfbalance operation: {operation}")

        if not operation.lvalue:
            logger.error("selfbalance operation has no lvalue")
            raise ValueError("selfbalance operation has no lvalue")

        # selfbalance() returns the balance of the current contract
        result_type = ElementaryType("uint256")

        # Get the full range for uint256 type
        variable_manager = VariableInfoManager()
        type_bounds = variable_manager.get_type_bounds(result_type)

        result_range_variable = RangeVariable(
            interval_ranges=[type_bounds],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled selfbalance() -> {result_var_name} (uint256)")

    def _handle_caller(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle caller() operation: call sender (excluding delegatecall)."""
        logger.debug(f"Handling caller operation: {operation}")

        if not operation.lvalue:
            logger.error("caller operation has no lvalue")
            raise ValueError("caller operation has no lvalue")

        # caller() returns the address that called this contract
        result_type = ElementaryType("address")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled caller() -> {result_var_name} (address)")

    def _handle_callvalue(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle callvalue() operation: wei sent together with the current call."""
        logger.debug(f"Handling callvalue operation: {operation}")

        if not operation.lvalue:
            logger.error("callvalue operation has no lvalue")
            raise ValueError("callvalue operation has no lvalue")

        # callvalue() returns the amount of wei sent with the call
        result_type = ElementaryType("uint256")

        # Get the full range for uint256 type
        variable_manager = VariableInfoManager()
        type_bounds = variable_manager.get_type_bounds(result_type)

        result_range_variable = RangeVariable(
            interval_ranges=[type_bounds],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled callvalue() -> {result_var_name} (uint256)")

    def _handle_calldatasize(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle calldatasize() operation: size of call data in bytes."""
        logger.debug(f"Handling calldatasize operation: {operation}")

        if not operation.lvalue:
            logger.error("calldatasize operation has no lvalue")
            raise ValueError("calldatasize operation has no lvalue")

        # calldatasize() returns the size of call data
        result_type = ElementaryType("uint256")

        # Call data size is typically 0 to a few KB, but could theoretically be larger
        # We'll use a reasonable upper bound
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("1048576"))],  # 0 to 1MB
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled calldatasize() -> {result_var_name} (uint256, range [0,1048576])")

    def _handle_codesize(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle codesize() operation: size of the code of the current contract / execution context."""
        logger.debug(f"Handling codesize operation: {operation}")

        if not operation.lvalue:
            logger.error("codesize operation has no lvalue")
            raise ValueError("codesize operation has no lvalue")

        # codesize() returns the size of the current contract's code
        result_type = ElementaryType("uint256")

        # Code size is typically a few KB to a few MB
        # We'll use a reasonable upper bound
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("10485760"))],  # 0 to 10MB
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled codesize() -> {result_var_name} (uint256, range [0,10485760])")

    def _handle_codecopy(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle codecopy(t, f, s) operation: copy s bytes from code at position f to mem at position t."""
        logger.debug(f"Handling codecopy operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 3:
            logger.warning(
                f"codecopy operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        t_arg, f_arg, s_arg = operation.arguments
        variable_manager = VariableInfoManager()
        t_name = variable_manager.get_variable_name(t_arg)
        f_name = variable_manager.get_variable_name(f_arg)
        s_name = variable_manager.get_variable_name(s_arg)

        # Track the memory operation by creating a range variable for the memory location
        # This helps with tracking what values are copied to memory
        memory_var_name = f"mem_code_{t_name}"

        # For codecopy, we don't know the exact values being copied from code
        # So we create a conservative range for the copied data
        result_type = ElementaryType("uint256")
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )
        memory_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the memory location in domain state
        domain.state.set_range_variable(memory_var_name, memory_range_variable)
        logger.debug(
            f"codecopy: copied {s_name} bytes from code[{f_name}] to memory[{t_name}] -> {memory_var_name}"
        )

    def _handle_extcodesize(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle extcodesize(a) operation: size of the code at address a."""
        logger.debug(f"Handling extcodesize operation: {operation}")

        if not operation.lvalue:
            logger.error("extcodesize operation has no lvalue")
            raise ValueError("extcodesize operation has no lvalue")

        # extcodesize() returns the size of code at the given address
        result_type = ElementaryType("uint256")

        # Code size is typically 0 (EOA) to a few MB
        # We'll use a reasonable upper bound
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("10485760"))],  # 0 to 10MB
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled extcodesize() -> {result_var_name} (uint256, range [0,10485760])")

    def _handle_extcodecopy(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle extcodecopy(a, t, f, s) operation: like codecopy(t, f, s) but take code at address a."""
        logger.debug(f"Handling extcodecopy operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 4:
            logger.warning(
                f"extcodecopy operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        a_arg, t_arg, f_arg, s_arg = operation.arguments
        variable_manager = VariableInfoManager()
        a_name = variable_manager.get_variable_name(a_arg)
        t_name = variable_manager.get_variable_name(t_arg)
        f_name = variable_manager.get_variable_name(f_arg)
        s_name = variable_manager.get_variable_name(s_arg)

        # Track the memory operation by creating a range variable for the memory location
        # This helps with tracking what values are copied to memory
        memory_var_name = f"mem_extcode_{t_name}"

        # For extcodecopy, we don't know the exact values being copied from external code
        # So we create a conservative range for the copied data
        result_type = ElementaryType("uint256")
        result_range = IntervalRange(
            lower_bound=result_type.min,
            upper_bound=result_type.max,
        )
        memory_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the memory location in domain state
        domain.state.set_range_variable(memory_var_name, memory_range_variable)
        logger.debug(
            f"extcodecopy: copied {s_name} bytes from code at address {a_name}[{f_name}] to memory[{t_name}] -> {memory_var_name}"
        )

    def _handle_create(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle create(v, p, n) operation: create new contract with code mem[p…(p+n)) and send v wei and return the new address; returns 0 on error."""
        logger.debug(f"Handling create operation: {operation}")

        if not operation.lvalue:
            logger.error("create operation has no lvalue")
            raise ValueError("create operation has no lvalue")

        # create returns the new contract address or 0 on error
        result_type = ElementaryType("address")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled create call -> {result_var_name} (address)")

    def _handle_callcode(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle callcode(g, a, v, in, insize, out, outsize) operation: identical to call but only use the code from a and stay in the context of the current contract otherwise."""
        logger.debug(f"Handling callcode operation: {operation}")

        if not operation.lvalue:
            logger.error("callcode operation has no lvalue")
            raise ValueError("callcode operation has no lvalue")

        if not operation.arguments or len(operation.arguments) != 7:
            logger.warning(
                f"callcode operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        g_arg, a_arg, v_arg, in_arg, insize_arg, out_arg, outsize_arg = operation.arguments
        variable_manager = VariableInfoManager()
        g_name = variable_manager.get_variable_name(g_arg)
        a_name = variable_manager.get_variable_name(a_arg)
        v_name = variable_manager.get_variable_name(v_arg)
        in_name = variable_manager.get_variable_name(in_arg)
        insize_name = variable_manager.get_variable_name(insize_arg)
        out_name = variable_manager.get_variable_name(out_arg)
        outsize_name = variable_manager.get_variable_name(outsize_arg)
        result_var_name = variable_manager.get_variable_name(operation.lvalue)

        # callcode returns success (1) or failure (0)
        result_type = ElementaryType("uint256")

        # For callcode, we can't determine the exact result without knowing the call outcome
        # So we create a conservative range for the success/failure result
        result_range = IntervalRange(
            lower_bound=Decimal("0"),  # 0 = failure
            upper_bound=Decimal("1"),  # 1 = success
        )

        # Create range variable for the call result
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(
            f"callcode: called contract {a_name} with gas {g_name}, value {v_name}, input[{in_name}...{in_name}+{insize_name}], output[{out_name}...{out_name}+{outsize_name}] -> {result_var_name}"
        )

    def _handle_log0(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle log0(p, s) operation: log data mem[p…(p+s))."""
        logger.debug(f"Handling log0 operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 2:
            logger.warning(
                f"log0 operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        p_arg, s_arg = operation.arguments
        variable_manager = VariableInfoManager()
        p_name = variable_manager.get_variable_name(p_arg)
        s_name = variable_manager.get_variable_name(s_arg)

        # log0 doesn't return a value, it logs data
        # Just log the operation for debugging purposes
        logger.debug(f"log0: logged {s_name} bytes from memory[{p_name}...{p_name}+{s_name})")

    def _handle_log1(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle log1(p, s, t1) operation: log data mem[p…(p+s)) with topic t1."""
        logger.debug(f"Handling log1 operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 3:
            logger.warning(
                f"log1 operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        p_arg, s_arg, t1_arg = operation.arguments
        variable_manager = VariableInfoManager()
        p_name = variable_manager.get_variable_name(p_arg)
        s_name = variable_manager.get_variable_name(s_arg)
        t1_name = variable_manager.get_variable_name(t1_arg)

        # log1 doesn't return a value, it logs data
        # Just log the operation for debugging purposes
        logger.debug(f"log1: logged {s_name} bytes from memory[{p_name}...{p_name}+{s_name}) with topic {t1_name}")

    def _handle_log2(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle log2(p, s, t1, t2) operation: log data mem[p…(p+s)) with topics t1, t2."""
        logger.debug(f"Handling log2 operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 4:
            logger.warning(
                f"log2 operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        p_arg, s_arg, t1_arg, t2_arg = operation.arguments
        variable_manager = VariableInfoManager()
        p_name = variable_manager.get_variable_name(p_arg)
        s_name = variable_manager.get_variable_name(s_arg)
        t1_name = variable_manager.get_variable_name(t1_arg)
        t2_name = variable_manager.get_variable_name(t2_arg)

        # log2 doesn't return a value, it logs data
        # Just log the operation for debugging purposes
        logger.debug(f"log2: logged {s_name} bytes from memory[{p_name}...{p_name}+{s_name}) with topics {t1_name}, {t2_name}")

    def _handle_log3(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle log3(p, s, t1, t2, t3) operation: log data mem[p…(p+s)) with topics t1, t2, t3."""
        logger.debug(f"Handling log3 operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 5:
            logger.warning(
                f"log3 operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        p_arg, s_arg, t1_arg, t2_arg, t3_arg = operation.arguments
        variable_manager = VariableInfoManager()
        p_name = variable_manager.get_variable_name(p_arg)
        s_name = variable_manager.get_variable_name(s_arg)
        t1_name = variable_manager.get_variable_name(t1_arg)
        t2_name = variable_manager.get_variable_name(t2_arg)
        t3_name = variable_manager.get_variable_name(t3_arg)

        # log3 doesn't return a value, it logs data
        # Just log the operation for debugging purposes
        logger.debug(f"log3: logged {s_name} bytes from memory[{p_name}...{p_name}+{s_name}) with topics {t1_name}, {t2_name}, {t3_name}")

    def _handle_log4(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle log4(p, s, t1, t2, t3, t4) operation: log data mem[p…(p+s)) with topics t1, t2, t3, t4."""
        logger.debug(f"Handling log4 operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 6:
            logger.warning(
                f"log4 operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        p_arg, s_arg, t1_arg, t2_arg, t3_arg, t4_arg = operation.arguments
        variable_manager = VariableInfoManager()
        p_name = variable_manager.get_variable_name(p_arg)
        s_name = variable_manager.get_variable_name(s_arg)
        t1_name = variable_manager.get_variable_name(t1_arg)
        t2_name = variable_manager.get_variable_name(t2_arg)
        t3_name = variable_manager.get_variable_name(t3_arg)
        t4_name = variable_manager.get_variable_name(t4_arg)

        # log4 doesn't return a value, it logs data
        # Just log the operation for debugging purposes
        logger.debug(f"log4: logged {s_name} bytes from memory[{p_name}...{p_name}+{s_name}) with topics {t1_name}, {t2_name}, {t3_name}, {t4_name}")

    def _handle_chainid(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle chainid() operation: ID of the executing chain (EIP-1344)."""
        logger.debug(f"Handling chainid operation: {operation}")

        if not operation.lvalue:
            logger.error("chainid operation has no lvalue")
            raise ValueError("chainid operation has no lvalue")

        # chainid() returns the chain ID
        result_type = ElementaryType("uint256")

        # Chain ID is typically a small positive integer
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("1"), Decimal("1000000"))],  # Reasonable range for chain IDs
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled chainid() -> {result_var_name} (uint256, range [1,1000000])")

    def _handle_basefee(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle basefee() operation: current block's base fee (EIP-3198 and EIP-1559)."""
        logger.debug(f"Handling basefee operation: {operation}")

        if not operation.lvalue:
            logger.error("basefee operation has no lvalue")
            raise ValueError("basefee operation has no lvalue")

        # basefee() returns the base fee
        result_type = ElementaryType("uint256")

        # Base fee is typically a small positive integer (in wei)
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("1000000000000000000"))],  # 0 to 1 ETH in wei
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled basefee() -> {result_var_name} (uint256, range [0,1000000000000000000])")

    def _handle_blobbasefee(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle blobbasefee() operation: current block's blob base fee (EIP-7516 and EIP-4844)."""
        logger.debug(f"Handling blobbasefee operation: {operation}")

        if not operation.lvalue:
            logger.error("blobbasefee operation has no lvalue")
            raise ValueError("blobbasefee operation has no lvalue")

        # blobbasefee() returns the blob base fee
        result_type = ElementaryType("uint256")

        # Blob base fee is typically a small positive integer (in wei)
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("1000000000000000000"))],  # 0 to 1 ETH in wei
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled blobbasefee() -> {result_var_name} (uint256, range [0,1000000000000000000])")

    def _handle_origin(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle origin() operation: transaction sender."""
        logger.debug(f"Handling origin operation: {operation}")

        if not operation.lvalue:
            logger.error("origin operation has no lvalue")
            raise ValueError("origin operation has no lvalue")

        # origin() returns the transaction sender address
        result_type = ElementaryType("address")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled origin() -> {result_var_name} (address)")

    def _handle_gasprice(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle gasprice() operation: gas price of the transaction."""
        logger.debug(f"Handling gasprice operation: {operation}")

        if not operation.lvalue:
            logger.error("gasprice operation has no lvalue")
            raise ValueError("gasprice operation has no lvalue")

        # gasprice() returns the gas price
        result_type = ElementaryType("uint256")

        # Gas price is typically a small positive integer (in wei)
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("1000000000000000000"))],  # 0 to 1 ETH in wei
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled gasprice() -> {result_var_name} (uint256, range [0,1000000000000000000])")

    def _handle_blockhash(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle blockhash(b) operation: hash of block nr b - only for last 256 blocks excluding current."""
        logger.debug(f"Handling blockhash operation: {operation}")

        if not operation.lvalue:
            logger.error("blockhash operation has no lvalue")
            raise ValueError("blockhash operation has no lvalue")

        # blockhash() returns a 32-byte hash
        result_type = ElementaryType("bytes32")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled blockhash() -> {result_var_name} (bytes32)")

    def _handle_blobhash(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle blobhash(i) operation: versioned hash of transaction's i-th blob, 0 if blob does not exist."""
        logger.debug(f"Handling blobhash operation: {operation}")

        if not operation.lvalue:
            logger.error("blobhash operation has no lvalue")
            raise ValueError("blobhash operation has no lvalue")

        # blobhash() returns a 32-byte hash
        result_type = ElementaryType("bytes32")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled blobhash() -> {result_var_name} (bytes32)")

    def _handle_coinbase(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle coinbase() operation: current mining beneficiary."""
        logger.debug(f"Handling coinbase operation: {operation}")

        if not operation.lvalue:
            logger.error("coinbase operation has no lvalue")
            raise ValueError("coinbase operation has no lvalue")

        # coinbase() returns the miner's address
        result_type = ElementaryType("address")
        result_range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled coinbase() -> {result_var_name} (address)")

    def _handle_number(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle number() operation: current block number."""
        logger.debug(f"Handling number operation: {operation}")

        if not operation.lvalue:
            logger.error("number operation has no lvalue")
            raise ValueError("number operation has no lvalue")

        # number() returns the current block number
        result_type = ElementaryType("uint256")

        # Block number is typically a large positive integer
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("100000000"))],  # 0 to 100M blocks
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled number() -> {result_var_name} (uint256, range [0,100000000])")

    def _handle_difficulty(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle difficulty() operation: difficulty of the current block (see note below)."""
        logger.debug(f"Handling difficulty operation: {operation}")

        if not operation.lvalue:
            logger.error("difficulty operation has no lvalue")
            raise ValueError("difficulty operation has no lvalue")

        # difficulty() returns the block difficulty
        result_type = ElementaryType("uint256")

        # Difficulty is typically a large positive integer
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("1000000000000000000000000000000"))],  # Large range for difficulty
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled difficulty() -> {result_var_name} (uint256)")

    def _handle_prevrandao(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle prevrandao() operation: randomness provided by the beacon chain (see note below)."""
        logger.debug(f"Handling prevrandao operation: {operation}")

        if not operation.lvalue:
            logger.error("prevrandao operation has no lvalue")
            raise ValueError("prevrandao operation has no lvalue")

        # prevrandao() returns randomness from the beacon chain
        result_type = ElementaryType("uint256")

        # Randomness is typically a large positive integer
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal(str(2**256 - 1)))],  # Full uint256 range
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled prevrandao() -> {result_var_name} (uint256)")

    def _handle_gaslimit(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle gaslimit() operation: block gas limit of the current block."""
        logger.debug(f"Handling gaslimit operation: {operation}")

        if not operation.lvalue:
            logger.error("gaslimit operation has no lvalue")
            raise ValueError("gaslimit operation has no lvalue")

        # gaslimit() returns the block gas limit
        result_type = ElementaryType("uint256")

        # Gas limit is typically a large positive integer
        result_range_variable = RangeVariable(
            interval_ranges=[IntervalRange(Decimal("0"), Decimal("100000000"))],  # 0 to 100M gas
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        variable_manager = VariableInfoManager()
        result_var_name = variable_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Handled gaslimit() -> {result_var_name} (uint256, range [0,100000000])")

    def _handle_selfdestruct(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle selfdestruct(a) operation: end execution, destroy current contract and send funds to a (deprecated)."""
        logger.debug(f"Handling selfdestruct operation: {operation}")

        if not operation.arguments or len(operation.arguments) != 1:
            logger.warning(
                f"selfdestruct operation has unexpected argument count: {len(operation.arguments) if operation.arguments else 0}"
            )
            return

        a_arg = operation.arguments[0]
        variable_manager = VariableInfoManager()
        a_name = variable_manager.get_variable_name(a_arg)

        # selfdestruct doesn't return a value, it destroys the contract
        # Just log the operation for debugging purposes
        logger.debug(f"selfdestruct: destroying contract and sending funds to {a_name}")

    def _handle_invalid(self, node: Node, domain: IntervalDomain, operation: SolidityCall) -> None:
        """Handle invalid() operation: end execution with invalid instruction."""
        logger.debug(f"Handling invalid operation: {operation}")

        # invalid() doesn't return a value, it ends execution with an invalid instruction
        # Just log the operation for debugging purposes
        logger.debug("invalid: ending execution with invalid instruction")
