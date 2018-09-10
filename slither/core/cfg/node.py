"""
    Node module
"""
import logging

from slither.core.sourceMapping.sourceMapping import SourceMapping
from slither.core.cfg.nodeType import NodeType
from slither.core.variables.variable import Variable

from slither.visitors.expression.expressionPrinter import ExpressionPrinter
from slither.visitors.expression.readVar import ReadVar
from slither.visitors.expression.writeVar import WriteVar

from slither.core.children.childFunction import ChildFunction

from slither.core.declarations.solidityVariables import SolidityFunction
logger = logging.getLogger("Node")

def link_nodes(n1, n2):
    n1.add_son(n2)
    n2.add_father(n1)

class Node(SourceMapping, ChildFunction):
    """
    Node class

    """

    def __init__(self, node_type, node_id):
        super(Node, self).__init__()
        self._node_type = node_type
        self._sons = []
        self._fathers = []
        self._expression = None
        self._variable_declaration = None
        self._node_id = node_id
        self._vars_written = []
        self._vars_read = []
        self._calls = []

        self._state_vars_written = []
        self._state_vars_read = []
        self._solidity_vars_read = []

        self._expression_vars_written = []
        self._expression_vars_read = []
        self._expression_calls = []

    @property
    def node_id(self):
        """Unique node id."""
        return self._node_id

    @property
    def type(self):
        """
            NodeType: type of the node
        """
        return self._node_type

    @property
    def variables_read(self):
        """
            list(Variable): Variables read (local/state/solidity)
        """
        return self._vars_read

    @property
    def state_variables_read(self):
        """
            list(StateVariable): State variables read
        """
        return self._state_vars_read

    @property
    def solidity_variables_read(self):
        """
            list(SolidityVariable): State variables read
        """
        return self._solidity_vars_read

    @property
    def variables_read_as_expression(self):
        return self._expression_vars_read

    @property
    def variables_written(self):
        """
            list(Variable): Variables written (local/state/solidity)
        """
        return self._vars_written

    @property
    def state_variables_written(self):
        """
            list(StateVariable): State variables written
        """
        return self._state_vars_written

    @property
    def variables_written_as_expression(self):
        return self._expression_vars_written

    @property
    def calls(self):
        """
            list(Function or SolidityFunction): List of calls
        """
        return self._calls

    @property
    def calls_as_expression(self):
        return self._expression_calls

    @property
    def expression(self):
        """
            Expression: Expression of the node
        """
        return self._expression

    def add_expression(self, expression):
        assert self._expression is None
        self._expression = expression

    def add_variable_declaration(self, var):
        assert self._variable_declaration is None
        self._variable_declaration = var
        if var.expression:
            self._vars_written += [var]

    @property
    def variable_declaration(self):
        return self._variable_declaration

    def __str__(self):
        txt = NodeType.str(self._node_type) + ' '+ str(self.expression)
        return txt

    def contains_require_or_assert(self):
        """
            Check if the node has a require or assert call
        Returns:
            bool: True if the node has a require or assert call
        """
        return self.calls and\
                any(isinstance(c, SolidityFunction) and\
                (c.name in ['require(bool)', 'require(bool,string)', 'assert(bool)'])\
                for c in self.calls)

    def contains_if(self):
        """
            Check if the node is a conditional node
        Returns:
            bool: True if the node is a conditional node (IF or IFLOOP)
        """
        return self.type in [NodeType.IF, NodeType.IFLOOP]

    def add_father(self, father):
        """ Add a father node

        Args:
            father: father to add
        """
        self._fathers.append(father)

    def set_fathers(self, fathers):
        """ Set the father nodes

        Args:
            fathers: list of fathers to add
        """
        self._fathers = fathers

    @property
    def fathers(self):
        """ Returns the father nodes

        Returns:
            fathers: list of fathers
        """
        return self._fathers

    def remove_father(self, father):
        """ Remove the father node. Do nothing if the node is not a father

        Args:
            fathers: list of fathers to add
        """
        self._fathers = [x for x in self._fathers if x.node_id != father.node_id]


    def add_son(self, son):
        """ Add a son node

        Args:
            son: son to add
        """
        self._sons.append(son)

    def set_sons(self, sons):
        """ Set the son nodes

        Args:
            sons: list of fathers to add
        """
        self._sons = sons

    @property
    def sons(self):
        """ Returns the son nodes

        Returns:
            sons: list of sons
        """
        return self._sons

