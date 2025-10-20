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
        if operation.function.full_name == "revert()":
            self._handle_revert(node, domain, operation)
            return

        # Handle keccak256 hashing
        if operation.function.full_name == "keccak256(bytes)":
            self._handle_keccak256(node, domain, operation)
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
        if operation.function.full_name == "create2(uint256,uint256,uint256,bytes32)":
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
            # staticcall variants
            "staticcall(bytes)",  # Simple staticcall with data
            "staticcall(uint256,bytes)",  # Staticcall with gas and data
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

        # For other Solidity functions, log and continue without error
        # logger.debug(f"Unhandled Solidity function: {operation.function.name} - skipping")
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

    def _handle_keccak256(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle keccak256(...) returning bytes32."""
        if not operation.lvalue:
            logger.error("keccak256 operation has no lvalue")
            raise ValueError("keccak256 operation has no lvalue")

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
        # logger.debug(f"Handled keccak256 call, created variable: {result_var_name} (bytes32)")

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
        """Handle create2(v, p, n, s) returning the new contract address or 0 on error."""
        if not operation.lvalue:
            logger.error("create2 operation has no lvalue")
            raise ValueError("create2 operation has no lvalue")

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

    #        logger.debug(f"Handled create2 call -> {result_var_name} (address)")

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
        - staticcall(bytes) - staticcall with data (1 arg)
        - staticcall(uint256, bytes) - staticcall with gas and data (2 args)

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
            7,
        }  # call(bytes), call(uint256,bytes), call(g,a,v,in,insize,out,outsize)

        if arg_count not in valid_arg_counts:
            logger.error(f"call operation requires 1, 2, or 7 arguments, got {arg_count}")
            raise ValueError(f"call operation requires 1, 2, or 7 arguments, got {arg_count}")

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
