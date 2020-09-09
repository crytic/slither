from slither.tools.middle.overlay.ast.node import OverlayNode
from slither.core.cfg.node import NodeType
from slither.solc_parsing.cfg.node import NodeSolc


class OverlayUnwrap(OverlayNode):
    """
    The semantics of this node is it replaces a break statement in original
    control flow. Since the overlay graph relies a lot on function calls, the
    break statement doesn't fit natively into the overlay abstraction. The
    unwrap node will unwind the call stack until it finds a loop enter call.
    This is semantically equivalent to exiting a loop early.
    """
    def __init__(self, node: NodeSolc):
        if node.type != NodeType.BREAK:
            print('Error: invalid construction of OverlayUnwrap')
            exit(-1)
        super().__init__(node.type, node)

    def __str__(self):
        return "UNWRAP"