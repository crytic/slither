from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.analysis.domain import \
    IntervalDomain
from slither.analyses.data_flow.analyses.interval.handlers.internal_call_handler import \
    InternalCallHandler
from slither.core.cfg.node import Node
from slither.slithir.operations.library_call import LibraryCall

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import \
        IntervalAnalysis


class LibraryCallHandler:
    """Handler for library calls that delegates to InternalCallHandler since they share the same logic."""
    
    def __init__(self, constraint_manager=None):
        # Reuse the internal call handler since library calls and internal calls
        # have identical constraint propagation logic
        self.internal_call_handler = InternalCallHandler(constraint_manager)

    def handle_library_call(
        self,
        node: Node,
        domain: IntervalDomain,
        library_call_operation: LibraryCall,
        analysis_instance: "IntervalAnalysis",
    ) -> None:
        """Handle library function calls by delegating to InternalCallHandler."""
        # Library calls and internal calls have the same constraint propagation logic,
        # so we can reuse the internal call handler
        self.internal_call_handler.handle_internal_call(
            node, domain, library_call_operation, analysis_instance
        )
