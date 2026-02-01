from slither.analyses.data_flow.analyses.interval.operations.solidity_call.base_assertion import (
    BaseAssertionHandler,
)


class RequireHandler(BaseAssertionHandler):
    """Handler for require calls."""

    def __init__(self, solver=None, analysis=None):
        super().__init__(solver, analysis, assertion_type="require")
