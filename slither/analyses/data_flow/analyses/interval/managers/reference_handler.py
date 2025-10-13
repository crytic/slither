from typing import Optional

from loguru import logger

from slither.slithir.operations.member import Member
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)


class ReferenceHandler:
    """Handles reference-to-target mappings for constraint propagation across different operation types."""

    def __init__(self) -> None:
        self._variable_info_manager = VariableInfoManager()
        # Track reference-to-target mappings for constraint propagation
        self._reference_mappings: dict[str, str] = {}

    def track_member_reference(self, operation: Member, result_var_name: str) -> None:
        """Track reference-to-target mapping for Member operations."""
        if not operation.variable_left or not operation.variable_right:
            raise ValueError("Member operation missing left or right variable")

        # Get the target field variable name
        base_var_name = self._variable_info_manager.get_variable_name(operation.variable_left)
        field_name = (
            operation.variable_right.value
            if hasattr(operation.variable_right, "value")
            else str(operation.variable_right)
        )
        target_field_name = f"{base_var_name}.{field_name}"

        # Store the mapping: reference -> target
        self._reference_mappings[result_var_name] = target_field_name
        logger.debug(f"Tracked member reference mapping: {result_var_name} -> {target_field_name}")

    def track_reference(self, reference_var_name: str, target_var_name: str) -> None:
        """Track a general reference-to-target mapping."""
        self._reference_mappings[reference_var_name] = target_var_name
        logger.debug(f"Tracked reference mapping: {reference_var_name} -> {target_var_name}")

    def get_target_for_reference(self, ref_var_name: str) -> Optional[str]:
        """Get the target variable name for a reference variable."""
        return self._reference_mappings.get(ref_var_name)

    def has_reference(self, ref_var_name: str) -> bool:
        """Check if a variable is a reference."""
        return ref_var_name in self._reference_mappings

    def clear_references(self) -> None:
        """Clear all reference mappings."""
        self._reference_mappings.clear()
        logger.debug("Cleared all reference mappings")

    def get_all_references(self) -> dict[str, str]:
        """Get all reference mappings."""
        return self._reference_mappings.copy()

    def remove_reference(self, ref_var_name: str) -> None:
        """Remove a specific reference mapping."""
        if ref_var_name in self._reference_mappings:
            del self._reference_mappings[ref_var_name]
            logger.debug(f"Removed reference mapping for {ref_var_name}")
