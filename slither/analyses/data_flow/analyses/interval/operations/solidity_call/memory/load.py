"""Handler for memory loads (mload)."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.solidity_call.memory.base import (
    MemoryBaseHandler,
)
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class MemoryLoadHandler(MemoryBaseHandler):
    """Handle `mload` memory reads."""

    # The EVM free memory pointer slot
    FREE_MEMORY_POINTER_SLOT = 0x40

    def handle(
        self,
        operation: Optional[SolidityCall],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        # Guard: only process SolidityCall operations.
        if operation is None or not isinstance(operation, SolidityCall):
            return

        # Guard: solver is required to build constraints.
        if self.solver is None:
            return

        # Guard: skip non-concrete states.
        if domain.variant != DomainVariant.STATE:
            return

        # Guard: need an offset argument to model the load.
        if not operation.arguments:
            return

        lvalue = operation.lvalue
        # Guard: memory loads without lvalues are irrelevant for tracking.
        if lvalue is None:
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        # Guard: skip if we cannot resolve a stable name for the destination.
        if lvalue_name is None:
            return

        # Check if this is loading the free memory pointer (mload(0x40))
        offset_arg = operation.arguments[0]
        is_free_memory_pointer_load = False
        if isinstance(offset_arg, Constant) and isinstance(offset_arg.value, int):
            if offset_arg.value == self.FREE_MEMORY_POINTER_SLOT:
                is_free_memory_pointer_load = True

        return_type: Optional[ElementaryType] = None
        type_call = getattr(operation, "type_call", None)
        # Branch: prefer explicit return type information from the call.
        if isinstance(type_call, list) and type_call:
            return_type = IntervalSMTUtils.resolve_elementary_type(type_call[0])

        # Branch: fall back to the lvalue type when explicit info is absent.
        if return_type is None and hasattr(lvalue, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(lvalue.type)

        # Branch: default to a full word when the type remains unknown.
        if return_type is None:
            return_type = self._memory_elementary_type(32)

        # Guard: ensure we can represent the return type.
        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            return

        tracked_lvalue = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked_lvalue is None:
            tracked_lvalue = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, return_type
            )
            # Guard: creation may fail for unsupported types.
            if tracked_lvalue is None:
                return
            domain.state.set_range_variable(lvalue_name, tracked_lvalue)

        slot_name = self._resolve_memory_slot_name(operation.arguments[0], domain)
        # Branch: link with a previously stored memory slot when available.
        if slot_name is not None:
            memory_var = IntervalSMTUtils.get_tracked_variable(domain, slot_name)
            if memory_var is not None:
                memory_term = memory_var.term
                lvalue_width = self.solver.bv_size(tracked_lvalue.term)
                memory_width = self.solver.bv_size(memory_term)

                # Branch: extend or truncate memory value to match lvalue width.
                if memory_width < lvalue_width:
                    is_signed = bool(memory_var.base.metadata.get("is_signed", False))
                    memory_term = IntervalSMTUtils.extend_to_width(
                        self.solver, memory_term, lvalue_width, is_signed
                    )
                elif memory_width > lvalue_width:
                    memory_term = IntervalSMTUtils.truncate_to_width(
                        self.solver, memory_term, lvalue_width
                    )

                self.solver.assert_constraint(tracked_lvalue.term == memory_term)
                tracked_lvalue.assert_no_overflow(self.solver)
                domain.state.set_range_variable(lvalue_name, tracked_lvalue)
                return

        # Check if we're loading from a bytes memory constant
        # Pattern: mload(ptr) where ptr = data + 0x20 (data is bytes memory constant)
        concrete_value = self._try_load_from_bytes_memory_constant(
            offset_arg, domain, return_type
        )
        if concrete_value is not None:
            # Constrain the loaded value to the concrete bytes
            const_term = IntervalSMTUtils.create_constant_term(
                self.solver, concrete_value, return_type
            )
            self.solver.assert_constraint(tracked_lvalue.term == const_term)
            tracked_lvalue.assert_no_overflow(self.solver)
            domain.state.set_range_variable(lvalue_name, tracked_lvalue)
            self.logger.debug(
                "Constrained mload from bytes memory constant: {name} = {value}",
                name=lvalue_name,
                value=hex(concrete_value),
            )
            return

        # Fallback: model as unconstrained within type bounds.
        tracked_lvalue.assert_no_overflow(self.solver)
        domain.state.set_range_variable(lvalue_name, tracked_lvalue)

        # Track this variable as a free memory pointer for safety analysis
        if is_free_memory_pointer_load and self.analysis is not None:
            self.analysis.safety_context.free_memory_pointers.add(lvalue_name)
            self.logger.debug(
                "Tracking free memory pointer variable: {var_name}",
                var_name=lvalue_name,
            )

    def _try_load_from_bytes_memory_constant(
        self,
        offset_arg: object,
        domain: "IntervalDomain",
        return_type: Optional[ElementaryType],
    ) -> Optional[int]:
        """
        Try to extract a concrete value from a bytes memory constant.
        
        Pattern: mload(ptr) where ptr = data + offset, and data is a bytes memory constant.
        Returns the concrete uint256 value at that memory location, or None if not applicable.
        """
        if self.solver is None:
            return None

        # Check if offset is a constant - direct load from known location
        if isinstance(offset_arg, Constant) and isinstance(offset_arg.value, int):
            # This is a direct constant offset, not useful for bytes memory constants
            # (bytes memory constants are accessed via variable + 0x20)
            return None

        # Check if offset is a variable that might be computed as base + constant
        offset_name = IntervalSMTUtils.resolve_variable_name(offset_arg)
        if offset_name is None:
            return None

        # Look for binary operations that computed this offset
        # Pattern: offset = base_var + constant_offset
        binary_op = domain.state.get_binary_operation(offset_name)
        if binary_op is None or binary_op.type.value != "+":
            return None

        # Check if left operand is a bytes memory constant variable
        left_name = IntervalSMTUtils.resolve_variable_name(binary_op.variable_left)
        if left_name is None:
            return None

        # Check if this variable has stored bytes memory constant content
        # Try exact match first
        byte_content = domain.state.get_bytes_memory_constant(left_name)
        
        # If not found, try matching base name (without SSA version)
        # e.g., if left_name is "data" but stored as "MemoryLoad.g().data|data_1"
        if byte_content is None and "|" in left_name:
            base_name = left_name.split("|")[0]
            # Try to find any SSA version of this variable
            for stored_name in domain.state.get_bytes_memory_constants().keys():
                if stored_name.startswith(base_name + "|") or stored_name == base_name:
                    byte_content = domain.state.get_bytes_memory_constant(stored_name)
                    if byte_content is not None:
                        break
        
        # Also try reverse: if stored name has SSA but left_name doesn't
        if byte_content is None and "|" not in left_name:
            for stored_name in domain.state.get_bytes_memory_constants().keys():
                if stored_name.startswith(left_name + "|") or stored_name == left_name:
                    byte_content = domain.state.get_bytes_memory_constant(stored_name)
                    if byte_content is not None:
                        break
        
        if byte_content is None:
            return None

        # Check if right operand is a constant offset (typically 0x20 to skip length field)
        right_operand = binary_op.variable_right
        if not isinstance(right_operand, Constant):
            return None

        offset_value = right_operand.value
        if not isinstance(offset_value, int):
            return None

        # For bytes memory, the layout is:
        # - data (pointer): points to memory location
        # - data + 0x00: length (32 bytes)
        # - data + 0x20: actual bytes content
        # We're loading from data + offset_value, so we need offset_value >= 0x20

        if offset_value < 0x20:
            # Loading from length field or before - not the bytes content
            return None

        # Calculate byte offset into the actual content
        byte_offset = offset_value - 0x20

        # Check if we have enough bytes
        if byte_offset >= len(byte_content):
            # Out of bounds - return None (let fallback handle it)
            return None

        # Extract 32 bytes (one word) starting at byte_offset
        # Pad with zeros if needed
        bytes_to_extract = byte_content[byte_offset : byte_offset + 32]
        if len(bytes_to_extract) < 32:
            # Pad with zeros to make 32 bytes
            bytes_to_extract = bytes_to_extract + b"\x00" * (32 - len(bytes_to_extract))

        # Convert to uint256 (big-endian)
        concrete_value = int.from_bytes(bytes_to_extract, byteorder="big")

        return concrete_value
