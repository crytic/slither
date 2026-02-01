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

    FREE_MEMORY_POINTER_SLOT = 0x40

    def handle(
        self,
        operation: Optional[SolidityCall],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Handle mload operation."""
        if not self._validate_operation(operation, domain):
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(operation.lvalue)
        if lvalue_name is None:
            return

        return_type = self._resolve_return_type(operation)
        if return_type is None:
            return

        tracked_lvalue = self._get_or_create_lvalue_var(lvalue_name, return_type, domain)
        if tracked_lvalue is None:
            return

        offset_arg = operation.arguments[0]
        if self._try_link_memory_slot(offset_arg, tracked_lvalue, lvalue_name, domain):
            return

        if self._try_load_bytes_constant(offset_arg, tracked_lvalue, lvalue_name, domain):
            return

        self._handle_unconstrained(tracked_lvalue, lvalue_name, offset_arg, domain)

    def _validate_operation(
        self, operation: Optional[SolidityCall], domain: "IntervalDomain"
    ) -> bool:
        """Validate the operation can be processed."""
        if operation is None or not isinstance(operation, SolidityCall):
            return False
        if self.solver is None:
            return False
        if domain.variant != DomainVariant.STATE:
            return False
        if not operation.arguments:
            return False
        if operation.lvalue is None:
            return False
        return True

    def _resolve_return_type(
        self, operation: SolidityCall
    ) -> Optional[ElementaryType]:
        """Resolve the return type for the mload."""
        return_type: Optional[ElementaryType] = None
        type_call = getattr(operation, "type_call", None)
        if isinstance(type_call, list) and type_call:
            return_type = IntervalSMTUtils.resolve_elementary_type(type_call[0])

        if return_type is None and hasattr(operation.lvalue, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(operation.lvalue.type)

        if return_type is None:
            return_type = self._memory_elementary_type(32)

        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            return None
        return return_type

    def _get_or_create_lvalue_var(
        self, lvalue_name: str, return_type: ElementaryType, domain: "IntervalDomain"
    ):
        """Get or create tracked variable for lvalue."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is not None:
            return tracked

        tracked = IntervalSMTUtils.create_tracked_variable(
            self.solver, lvalue_name, return_type
        )
        if tracked is None:
            return None

        domain.state.set_range_variable(lvalue_name, tracked)
        return tracked

    def _try_link_memory_slot(
        self, offset_arg, tracked_lvalue, lvalue_name: str, domain: "IntervalDomain"
    ) -> bool:
        """Try to link with a previously stored memory slot. Returns True if linked."""
        slot_name = self._resolve_memory_slot_name(offset_arg, domain)
        if slot_name is None:
            return False

        memory_var = IntervalSMTUtils.get_tracked_variable(domain, slot_name)
        if memory_var is None:
            return False

        memory_term = self._adjust_memory_width(memory_var, tracked_lvalue)
        self.solver.assert_constraint(tracked_lvalue.term == memory_term)
        tracked_lvalue.assert_no_overflow(self.solver)
        domain.state.set_range_variable(lvalue_name, tracked_lvalue)
        return True

    def _adjust_memory_width(self, memory_var, tracked_lvalue):
        """Adjust memory term width to match lvalue."""
        memory_term = memory_var.term
        lvalue_width = self.solver.bv_size(tracked_lvalue.term)
        memory_width = self.solver.bv_size(memory_term)

        if memory_width < lvalue_width:
            is_signed = bool(memory_var.base.metadata.get("is_signed", False))
            return IntervalSMTUtils.extend_to_width(
                self.solver, memory_term, lvalue_width, is_signed
            )
        if memory_width > lvalue_width:
            return IntervalSMTUtils.truncate_to_width(
                self.solver, memory_term, lvalue_width
            )
        return memory_term

    def _try_load_bytes_constant(
        self, offset_arg, tracked_lvalue, lvalue_name: str, domain: "IntervalDomain"
    ) -> bool:
        """Try loading from a bytes memory constant. Returns True if loaded."""
        concrete_value = self._try_load_from_bytes_memory_constant(offset_arg, domain)
        if concrete_value is None:
            return False

        const_term = self.solver.create_constant(concrete_value, tracked_lvalue.sort)
        self.solver.assert_constraint(tracked_lvalue.term == const_term)
        tracked_lvalue.assert_no_overflow(self.solver)
        domain.state.set_range_variable(lvalue_name, tracked_lvalue)
        self.logger.debug(
            "Constrained mload from bytes memory constant: {name} = {value}",
            name=lvalue_name,
            value=hex(concrete_value),
        )
        return True

    def _handle_unconstrained(
        self, tracked_lvalue, lvalue_name: str, offset_arg, domain: "IntervalDomain"
    ) -> None:
        """Handle unconstrained load (fallback)."""
        tracked_lvalue.assert_no_overflow(self.solver)
        domain.state.set_range_variable(lvalue_name, tracked_lvalue)

        is_fmp = self._is_free_memory_pointer_load(offset_arg)
        if is_fmp and self.analysis is not None:
            self.analysis.safety_context.free_memory_pointers.add(lvalue_name)
            self.logger.debug(
                "Tracking free memory pointer variable: {var_name}", var_name=lvalue_name
            )

    def _is_free_memory_pointer_load(self, offset_arg) -> bool:
        """Check if loading the free memory pointer (mload(0x40))."""
        if isinstance(offset_arg, Constant) and isinstance(offset_arg.value, int):
            return offset_arg.value == self.FREE_MEMORY_POINTER_SLOT
        return False

    def _try_load_from_bytes_memory_constant(
        self, offset_arg: object, domain: "IntervalDomain"
    ) -> Optional[int]:
        """Try to extract a concrete value from a bytes memory constant."""
        if self.solver is None:
            return None
        if isinstance(offset_arg, Constant) and isinstance(offset_arg.value, int):
            return None

        binary_op = self._find_binary_add_operation(offset_arg, domain)
        if binary_op is None:
            return None

        left_name = IntervalSMTUtils.resolve_variable_name(binary_op.variable_left)
        if left_name is None:
            return None

        byte_content = self._find_bytes_content(left_name, domain)
        if byte_content is None:
            return None

        offset_value = self._get_constant_offset(binary_op.variable_right)
        if offset_value is None or offset_value < 0x20:
            return None

        return self._extract_word_at_offset(byte_content, offset_value - 0x20)

    def _find_binary_add_operation(self, offset_arg: object, domain: "IntervalDomain"):
        """Find the binary add operation that computed the offset."""
        offset_name = IntervalSMTUtils.resolve_variable_name(offset_arg)
        if offset_name is None:
            return None

        binary_op = domain.state.get_binary_operation(offset_name)
        if binary_op is None or binary_op.type.value != "+":
            return None
        return binary_op

    def _find_bytes_content(
        self, var_name: str, domain: "IntervalDomain"
    ) -> Optional[bytes]:
        """Find bytes memory constant content by variable name."""
        content = domain.state.get_bytes_memory_constant(var_name)
        if content is not None:
            return content

        if "|" in var_name:
            content = self._search_by_base_name(var_name.split("|")[0], domain)
            if content is not None:
                return content
        else:
            content = self._search_by_prefix(var_name, domain)
            if content is not None:
                return content

        return None

    def _search_by_base_name(
        self, base_name: str, domain: "IntervalDomain"
    ) -> Optional[bytes]:
        """Search for bytes content by base name prefix."""
        for stored_name in domain.state.get_bytes_memory_constants().keys():
            if stored_name.startswith(base_name + "|") or stored_name == base_name:
                content = domain.state.get_bytes_memory_constant(stored_name)
                if content is not None:
                    return content
        return None

    def _search_by_prefix(
        self, prefix: str, domain: "IntervalDomain"
    ) -> Optional[bytes]:
        """Search for bytes content where stored name starts with prefix."""
        for stored_name in domain.state.get_bytes_memory_constants().keys():
            if stored_name.startswith(prefix + "|") or stored_name == prefix:
                content = domain.state.get_bytes_memory_constant(stored_name)
                if content is not None:
                    return content
        return None

    def _get_constant_offset(self, operand) -> Optional[int]:
        """Get constant integer value from operand."""
        if not isinstance(operand, Constant):
            return None
        if not isinstance(operand.value, int):
            return None
        return operand.value

    def _extract_word_at_offset(
        self, byte_content: bytes, byte_offset: int
    ) -> Optional[int]:
        """Extract a 32-byte word at the given offset, pad if needed."""
        if byte_offset >= len(byte_content):
            return None

        bytes_to_extract = byte_content[byte_offset : byte_offset + 32]
        if len(bytes_to_extract) < 32:
            bytes_to_extract = bytes_to_extract + b"\x00" * (32 - len(bytes_to_extract))

        return int.from_bytes(bytes_to_extract, byteorder="big")
