import html
from typing import List
import string
from collections import deque
from itertools import count

from slither.tools.middle.overlay.ast.node import OverlayNode
from slither import Slither
from slither.tools.middle.overlay.ast.function import OverlayFunction
from slither.core.cfg.node import NodeType

from slither.solc_parsing.declarations.function import FunctionSolc
from slither.tools.middle.imports.graphivz import Digraph


class OverlayGraph:
    slither: Slither
    functions: List[OverlayFunction]

    counter = count()

    def __init__(self, slither: Slither):
        # Overlay graph can only be constructed from a valid slither instance
        self.slither = slither
        self.functions = []

        # Create overlay functions
        for func in slither.functions:
            self.functions.append(OverlayFunction(func.contract, func))

        # Another pass to add correctly identify the neighbors (both the
        # previous and the next) of each node
        for function in self.functions:
            for statement in function.statements:
                for father in statement.node.fathers:
                    statement.prev.add(self.find_overlay_node(father))
                for son in statement.node.sons:
                    statement.succ.add(self.find_overlay_node(son))

    def find_overlay_node(self, concrete):
        """
        Search the entire graph to find the overlay node associated with a
        certain concrete node.
        """
        for function in self.functions:
            for statement in function.statements:
                if statement.node == concrete:
                    return statement
        return None

    def find_overlay_function(self, concrete: FunctionSolc):
        """
        Search the entire graph to find the overlay function associated with a
        certain concrete node.
        """
        for function in self.functions:
            if function.func == concrete:
                return function
        return None

    def find_overlay_function_by_name(self, name: str):
        """
        Search the entire graph to find the function with a certain name.
        """
        for function in self.functions:
            if function.name == name:
                return function
        return None

    def get_digraph(self):
        """
        Returns the text representation (dot-file) of the graph.
        """
        g = Digraph('Overlay CFG')
        for function in self.functions:
            with g.subgraph(name='cluster_{}'.format(function.__hash__())) as c:
                c.attr('node', shape='record')
                c.attr(label=function.name)
                for statement in function.statements:
                    # Construct the label
                    newline = '<br align="left"/>'
                    label = '<B>' + custom_html_escape(str(statement)).replace('\n', newline) + '</B>' \
                            + newline + newline + newline
                    for ir in statement.ir:
                        label += custom_html_escape(str(ir)) + newline
                    label = '<' + label + '>'

                    current = str(statement.__hash__())
                    c.node(current, label)
                    # Only take care of successors to avoid double counting
                    for succ in statement.succ:
                        c.edge(current, str(succ.__hash__()))
        return g

    def view_digraph(self):
        self.get_digraph().view()

    def save_digraph(self):
        g = self.get_digraph()
        g.render(filename='save{}'.format(next(self.counter)))
        g.view()

    def get_bfs_ordering(self, function: OverlayFunction) -> List[OverlayNode]:
        """
        Returns the visit order of a BFS traversal starting at the ENTRY POINT
        """
        start = list(filter(lambda x: x.type == NodeType.ENTRYPOINT, function.statements))
        q = deque(start)
        visited = set()
        ordering = []
        while len(q) != 0:
            current = q.popleft()
            if current not in visited:
                ordering.append(current)
            visited.add(current)
            for succ in current.succ:
                if succ not in visited:
                    q.append(succ)
        return ordering

    def to_text_repr(self) -> str:
        """
        Print a consistent text representation of the shape of the graph. It is
        important to do some sort of sorting on the statements here so that this
        text representation can be used for tests.
        """
        ret = ""
        self.functions.sort(key=lambda x: x.name)

        for function in self.functions:
            topological_ordering = function.get_topological_ordering()

            # Print statements in accordance with the topological ordering. We
            # also need to get rid of any number identifiers on the end of our
            # overlay functions because they interact badly with pytest.
            cleaned_name = function.name.rstrip(string.digits)
            ret += '{}\n'.format(cleaned_name)
            for statement in topological_ordering:
                ret += '    {}\n'.format(NodeType.str(statement.type))

        return ret


def custom_html_escape(s: str) -> str:
    s = html.escape(s)

    # OR symbol
    s = s.replace('||', 'OR')

    return s
