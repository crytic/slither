"""
    Node module
"""
import logging

from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.variable import Variable

from slither.visitors.expression.expression_printer import ExpressionPrinter
from slither.visitors.expression.read_var import ReadVar
from slither.visitors.expression.write_var import WriteVar

from slither.core.children.child_function import ChildFunction

from slither.core.declarations.solidity_variables import SolidityFunction

from slither.slithir.convert import convert_expression

logger = logging.getLogger("Node")

class NodeType:

    ENTRYPOINT = 0x0  # no expression

    # Node with expression

    EXPRESSION = 0x10  # normal case
    RETURN = 0x11      # RETURN may contain an expression
    IF = 0x12
    VARIABLE = 0x13    # Declaration of variable
    ASSEMBLY = 0x14
    IFLOOP = 0x15

    # Below the nodes have no expression
    # But are used to expression CFG structure

    # Absorbing node
    THROW = 0x20

    # Loop related nodes
    BREAK = 0x31
    CONTINUE = 0x32

    # Only modifier node
    PLACEHOLDER = 0x40

    # Merging nodes
    # Unclear if they will be necessary
    ENDIF = 0x50
    STARTLOOP = 0x51
    ENDLOOP = 0x52

#    @staticmethod
    def str(t):
        if t == 0x0:
            return 'ENTRY_POINT'
        if t == 0x10:
            return 'EXPRESSION'
        if t == 0x11:
            return 'RETURN'
        if t == 0x12:
            return 'IF'
        if t == 0x13:
            return 'NEW VARIABLE'
        if t == 0x14:
            return 'INLINE ASM'
        if t == 0x15:
            return 'IF_LOOP'
        if t == 0x20:
            return 'THROW'
        if t == 0x31:
            return 'BREAK'
        if t == 0x32:
            return 'CONTINUE'
        if t == 0x40:
            return '_'
        if t == 0x50:
            return 'END_IF'
        if t == 0x51:
            return 'BEGIN_LOOP'
        if t == 0x52:
            return 'END_LOOP'
        return 'Unknown type {}'.format(hex(t))

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
        self._internal_calls = []
        self._external_calls = []
        self._irs = []

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
        return list(self._vars_read)

    @property
    def state_variables_read(self):
        """
            list(StateVariable): State variables read
        """
        return list(self._state_vars_read)

    @property
    def solidity_variables_read(self):
        """
            list(SolidityVariable): State variables read
        """
        return list(self._solidity_vars_read)

    @property
    def variables_read_as_expression(self):
        return self._expression_vars_read

    @property
    def variables_written(self):
        """
            list(Variable): Variables written (local/state/solidity)
        """
        return list(self._vars_written)

    @property
    def state_variables_written(self):
        """
            list(StateVariable): State variables written
        """
        return list(self._state_vars_written)

    @property
    def variables_written_as_expression(self):
        return self._expression_vars_written

    @property
    def internal_calls(self):
        """
            list(Function or SolidityFunction): List of function calls (that does not create a transaction)
        """
        return list(self._internal_calls)

    @property
    def external_calls(self):
        """
            list(CallExpression): List of message calls (that creates a transaction)
        """
        return self._external_calls

    @property
    def calls_as_expression(self):
        return list(self._expression_calls)

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
        """
        Returns:
            LocalVariable
        """
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
        return self.internal_calls and\
                any(isinstance(c, SolidityFunction) and\
                (c.name in ['require(bool)', 'require(bool,string)', 'assert(bool)'])\
                for c in self.internal_calls)

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
            list(Node): list of fathers
        """
        return list(self._fathers)


    def remove_father(self, father):
        """ Remove the father node. Do nothing if the node is not a father

        Args:
            fathers: list of fathers to add
        """
        self._fathers = [x for x in self._fathers if x.node_id != father.node_id]

    def remove_son(self, son):
        """ Remove the son node. Do nothing if the node is not a son

        Args:
            fathers: list of fathers to add
        """
        self._sons = [x for x in self._sons if x.node_id != son.node_id]

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
            list(Node): list of sons
        """
        return list(self._sons)

    @property
    def irs(self):
        """ Returns the slithIR representation

        return
            list(slithIR.Operation)
        """
        return self._irs

    def slithir_generation(self):
        if self.expression:
            expression = self.expression
            self._irs = convert_expression(expression, self)
