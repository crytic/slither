from slither.analyses.data_flow.analyses.interval.operations.solidity_call.base_assertion import (
    BaseAssertionHandler,
)


class AssertHandler(BaseAssertionHandler):
    """Handler for assert calls."""

    def __init__(self, solver=None, analysis=None):
        super().__init__(solver, analysis, assertion_type="assert")
