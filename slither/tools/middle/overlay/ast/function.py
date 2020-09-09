from collections import deque

from slither.tools.middle.overlay.ast.call import OverlayCall
from slither.tools.middle.overlay.ast.ite import OverlayITE
from slither.tools.middle.overlay.ast.node import OverlayNode
from slither.tools.middle.overlay.construction import construct_overlay
from slither.core.cfg.node import NodeType
from slither.solc_parsing.declarations.function import FunctionSolc
from typing import Set, List
from itertools import count


class OverlayFunction:
    func: FunctionSolc
    name: str
    statements: Set[OverlayNode]
    counter = count()

    def __init__(self, contract, func=None):
        # Some functions may be created an do not have a concrete counterpart
        self.contract = contract
        self.func = func
        self.statements = set()
        self.entry_point = None

        if func is not None:
            self.name = func.name
        else:
            self.name = 'OVERLAY_FUNCTION_{}'.format(self.counter.__next__())

        # Try to construct overlays for all the statements in the function
        if func:
            for node in func.nodes:
                self.statements.add(construct_overlay(node))

    def get_source_code(self) -> str:
        """
        Gets the source code associated with this function.
        """
        source_mapping_lines = set()
        filename = None

        if self.func is not None:
            filename = self.func.source_mapping['filename_absolute']
            source_mapping_lines.update(self.func.source_mapping['lines'])
        else:
            for stmt in self.statements:
                if stmt.node is None:
                    continue
                if stmt.node.type == NodeType.ENTRYPOINT:
                    # Entry points have a bunch of source mappings for some reason.
                    continue
                if filename is None:
                    filename = stmt.node.source_mapping['filename_absolute']
                source_mapping_lines.update(stmt.node.source_mapping['lines'])

        lines = None
        with open(filename, 'r') as f:
            lines = f.readlines()
        min_line, max_line = min(source_mapping_lines) - 1, max(source_mapping_lines)
        lines = lines[min_line:max_line]
        return ''.join(lines)

    def get_ir(self) -> str:
        lines = []
        for stmt in self.get_topological_ordering():
            if isinstance(stmt, OverlayCall):
                lines.append(str(stmt).strip())
            if isinstance(stmt, OverlayITE):
                lines.append(str(stmt).strip())
            for ir in stmt.ir:
                lines.append(str(ir).strip())
        return '\n'.join(lines)

    def get_topological_ordering(self) -> List[OverlayNode]:
        indegree = {stmt: 0 for stmt in self.statements}
        for stmt in self.statements:
            for succ in stmt.succ:
                indegree[succ] += 1

        nodes_with_no_incoming = deque()
        for node in self.statements:
            if indegree[node] == 0:
                nodes_with_no_incoming.append(node)

        topological_ordering = []

        while len(nodes_with_no_incoming):
            stmt = nodes_with_no_incoming.popleft()
            topological_ordering.append(stmt)
            for succ in stmt.succ:
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    nodes_with_no_incoming.append(succ)

        return topological_ordering


def overlay_function_from_basic_block(bb: List[OverlayNode], contract):
    ret = OverlayFunction(contract)
    ret.statements = set(bb)
    return ret
