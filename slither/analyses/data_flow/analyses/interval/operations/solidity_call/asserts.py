from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.operations.solidity_call.base_assertion import (
    BaseAssertionHandler,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.solidity_call import SolidityCall


class AssertHandler(BaseAssertionHandler):
    """Handler for assert calls."""

    def __init__(self, solver=None, analysis=None):
        super().__init__(solver, analysis, assertion_type="assert")
