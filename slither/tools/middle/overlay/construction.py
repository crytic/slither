from slither.tools.middle.overlay.ast.node import OverlayNode
from slither.tools.middle.overlay.ast.unwrap import OverlayUnwrap
from slither.core.cfg.node import NodeType
from slither.solc_parsing.cfg.node import NodeSolc


def construct_overlay(node: NodeSolc) -> OverlayNode:
    if node.type == NodeType.BREAK:
        return OverlayUnwrap(node)
    else:
        return OverlayNode(node.type, node)
