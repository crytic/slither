"""Binary operation handler dispatch."""

from typing import Optional, TYPE_CHECKING

from slither.slithir.operations.binary import Binary, BinaryType

from ..base import BaseOperationHandler

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node

from .arithmetic import ArithmeticBinaryHandler
from .comparison import ComparisonBinaryHandler


class BinaryHandler(BaseOperationHandler):
    """Dispatch binary operations to specialised handlers."""

    _ARITHMETIC_TYPES = {
        BinaryType.ADDITION,
        BinaryType.SUBTRACTION,
        BinaryType.MULTIPLICATION,
        BinaryType.DIVISION,
        BinaryType.MODULO,
        BinaryType.POWER,
        BinaryType.LEFT_SHIFT,
        BinaryType.RIGHT_SHIFT,
    }
    _COMPARISON_TYPES = {
        BinaryType.GREATER_EQUAL,
        BinaryType.GREATER,
        BinaryType.LESS_EQUAL,
        BinaryType.LESS,
        BinaryType.EQUAL,
        BinaryType.NOT_EQUAL,
        BinaryType.ANDAND,
        BinaryType.OROR,
    }

    def __init__(self, solver=None) -> None:
        super().__init__(solver)
        self._arithmetic_handler = ArithmeticBinaryHandler(solver)
        self._comparison_handler = ComparisonBinaryHandler(solver)

    def handle(
        self,
        operation: Optional[Binary],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if operation is None or not isinstance(operation, Binary):
            return

        if operation.type in self._ARITHMETIC_TYPES:
            self._arithmetic_handler.handle(operation, domain, node)
        elif operation.type in self._COMPARISON_TYPES:
            self._comparison_handler.handle(operation, domain, node)
