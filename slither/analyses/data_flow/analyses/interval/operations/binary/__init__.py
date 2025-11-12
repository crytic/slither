"""Binary operation handler dispatch."""

from typing import Optional, TYPE_CHECKING

from slither.slithir.operations.binary import Binary, BinaryType

from ..base import BaseOperationHandler

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node

from .arithmetic import ArithmeticBinaryHandler


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

    def handle(
        self,
        operation: Optional[Binary],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if operation is None or not isinstance(operation, Binary):
            return

        if operation.type in self._ARITHMETIC_TYPES:
            ArithmeticBinaryHandler(self.solver).handle(operation, domain, node)
