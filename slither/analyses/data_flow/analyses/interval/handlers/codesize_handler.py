from decimal import Decimal
from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.codesize import CodeSize

# Maximum reasonable code size for contracts (10MB in bytes)
MAX_CODE_SIZE = Decimal("10485760")


class CodeSizeHandler:
    """Handler for CodeSize operations (e.g., address.code.size)."""

    def __init__(self):
        self.variable_info_manager = VariableInfoManager()

    def handle_codesize(self, node: Node, domain: IntervalDomain, operation: CodeSize) -> None:
        """Handle CodeSize operation: result = account.code.size"""
        if not operation.lvalue:
            logger.error("CodeSize operation has no lvalue")
            raise ValueError("CodeSize operation has no lvalue")

        # CodeSize operations return uint256 representing the code size
        result_type = ElementaryType("uint256")

        # Code size is typically a few KB to a few MB
        # We'll use a reasonable upper bound (same as codesize() SolidityCall)
        result_range = IntervalRange(
            lower_bound=Decimal("0"),
            upper_bound=MAX_CODE_SIZE,
        )

        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=result_type,
        )

        # Store the result in the domain state
        result_var_name = self.variable_info_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        # logger.debug(f"Handled codesize operation: {operation.value}.code.size -> {result_var_name} (uint256, range [0,{MAX_CODE_SIZE}])")
