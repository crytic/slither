"""
    Node module
"""
import logging

from slither.core.children.child_function import ChildFunction
from slither.core.declarations import Contract
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.core.solidity_types import ElementaryType
from slither.slithir.convert import convert_expression
from slither.slithir.operations import (Balance, HighLevelCall, Index,
                                        InternalCall, Length, LibraryCall,
                                        LowLevelCall, Member,
                                        OperationWithLValue, Phi, PhiCallback,
                                        SolidityCall, Return)
from slither.slithir.variables import (Constant, LocalIRVariable,
                                       ReferenceVariable, StateIRVariable,
                                       TemporaryVariable, TupleVariable)
from slither.all_exceptions import SlitherException

logger = logging.getLogger("Node")

###################################################################################
###################################################################################
# region NodeType
###################################################################################
###################################################################################

class NodeType:

    ENTRYPOINT = 0x0  # no expression

    # Node with expression

    EXPRESSION = 0x10  # normal case
    RETURN = 0x11      # RETURN may contain an expression
    IF = 0x12
    VARIABLE = 0x13    # Declaration of variable
    ASSEMBLY = 0x14
    IFLOOP = 0x15

    # Merging nodes
    # Can have phi IR operation
    ENDIF = 0x50     # ENDIF node source mapping points to the if/else body
    STARTLOOP = 0x51 # STARTLOOP node source mapping points to the entire loop body
    ENDLOOP = 0x52   # ENDLOOP node source mapping points to the entire loop body

    # Below the nodes have no expression
    # But are used to expression CFG structure

    # Absorbing node
    THROW = 0x20

    # Loop related nodes
    BREAK = 0x31
    CONTINUE = 0x32

    # Only modifier node
    PLACEHOLDER = 0x40

    # Node not related to the CFG
    # Use for state variable declaration, or modifier calls
    OTHER_ENTRYPOINT = 0x50


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


# endregion
###################################################################################
###################################################################################
# region Utils
###################################################################################
###################################################################################

def link_nodes(n1, n2):
    n1.add_son(n2)
    n2.add_father(n1)

def recheable(node):
    '''
    Return the set of nodes reacheable from the node
    :param node:
    :return: set(Node)
    '''
    nodes = node.sons
    visited = set()
    while nodes:
        next = nodes[0]
        nodes = nodes[1:]
        if not next in visited:
            visited.add(next)
            for son in next.sons:
                if not son in visited:
                    nodes.append(son)
    return visited


# endregion

class Node(SourceMapping, ChildFunction):
    """
    Node class

    """

    def __init__(self, node_type, node_id):
        super(Node, self).__init__()
        self._node_type = node_type

        # TODO: rename to explicit CFG 
        self._sons = []
        self._fathers = []

        ## Dominators info
        # Dominators nodes
        self._dominators = set()
        self._immediate_dominator = None
        ## Nodes of the dominators tree
        #self._dom_predecessors = set()
        self._dom_successors = set()
        # Dominance frontier
        self._dominance_frontier = set()
        # Phi origin
        # key are variable name
        # values are list of Node
        self._phi_origins_state_variables = {}
        self._phi_origins_local_variables = {}

        self._expression = None
        self._variable_declaration = None
        self._node_id = node_id

        self._vars_written = []
        self._vars_read = []

        self._ssa_vars_written = []
        self._ssa_vars_read = []

        self._internal_calls = []
        self._solidity_calls = []
        self._high_level_calls = [] # contains library calls
        self._library_calls = []
        self._low_level_calls = []
        self._external_calls_as_expressions = []
        self._internal_calls_as_expressions = []
        self._irs = []
        self._irs_ssa = []

        self._state_vars_written = []
        self._state_vars_read = []
        self._solidity_vars_read = []

        self._ssa_state_vars_written = []
        self._ssa_state_vars_read = []

        self._local_vars_read = []
        self._local_vars_written = []

        self._slithir_vars = set() # non SSA

        self._ssa_local_vars_read = []
        self._ssa_local_vars_written = []

        self._expression_vars_written = []
        self._expression_vars_read = []
        self._expression_calls = []

    ###################################################################################
    ###################################################################################
    # region General's properties
    ###################################################################################
    ###################################################################################

    @property
    def slither(self):
        return self.function.slither

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

    @type.setter
    def type(self, t):
        self._node_type = t

    # endregion
    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################

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
    def local_variables_read(self):
        """
            list(LocalVariable): Local variables read
        """
        return list(self._local_vars_read)

    @property
    def solidity_variables_read(self):
        """
            list(SolidityVariable): State variables read
        """
        return list(self._solidity_vars_read)

    @property
    def ssa_variables_read(self):
        """
            list(Variable): Variables read (local/state/solidity)
        """
        return list(self._ssa_vars_read)

    @property
    def ssa_state_variables_read(self):
        """
            list(StateVariable): State variables read
        """
        return list(self._ssa_state_vars_read)

    @property
    def ssa_local_variables_read(self):
        """
            list(LocalVariable): Local variables read
        """
        return list(self._ssa_local_vars_read)

    @property
    def variables_read_as_expression(self):
        return self._expression_vars_read

    @property
    def slithir_variables(self):
        return list(self._slithir_vars)

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
    def local_variables_written(self):
        """
            list(LocalVariable): Local variables written
        """
        return list(self._local_vars_written)

    @property
    def ssa_variables_written(self):
        """
            list(Variable): Variables written (local/state/solidity)
        """
        return list(self._ssa_vars_written)

    @property
    def ssa_state_variables_written(self):
        """
            list(StateVariable): State variables written
        """
        return list(self._ssa_state_vars_written)

    @property
    def ssa_local_variables_written(self):
        """
            list(LocalVariable): Local variables written
        """
        return list(self._ssa_local_vars_written)

    @property
    def variables_written_as_expression(self):
        return self._expression_vars_written

    # endregion
    ###################################################################################
    ###################################################################################
    # region Calls
    ###################################################################################
    ###################################################################################

    @property
    def internal_calls(self):
        """
            list(Function or SolidityFunction): List of internal/soldiity function calls
        """
        return list(self._internal_calls)

    @property
    def solidity_calls(self):
        """
            list(SolidityFunction): List of Soldity calls
        """
        return list(self._internal_calls)

    @property
    def high_level_calls(self):
        """
            list((Contract, Function|Variable)):
            List of high level calls (external calls).
            A variable is called in case of call to a public state variable
            Include library calls
        """
        return list(self._high_level_calls)

    @property
    def library_calls(self):
        """
            list((Contract, Function)):
            Include library calls
        """
        return list(self._library_calls)
    @property
    def low_level_calls(self):
        """
            list((Variable|SolidityVariable, str)): List of low_level call
            A low level call is defined by
            - the variable called
            - the name of the function (call/delegatecall/codecall)
        """
        return list(self._low_level_calls)

    @property
    def external_calls_as_expressions(self):
        """
            list(CallExpression): List of message calls (that creates a transaction)
        """
        return self._external_calls_as_expressions

    @property
    def internal_calls_as_expressions(self):
        """
            list(CallExpression): List of internal calls (that dont create a transaction)
        """
        return self._internal_calls_as_expressions

    @property
    def calls_as_expression(self):
        return list(self._expression_calls)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Expressions
    ###################################################################################
    ###################################################################################

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
            self._local_vars_written += [var]

    @property
    def variable_declaration(self):
        """
        Returns:
            LocalVariable
        """
        return self._variable_declaration

    # endregion
    ###################################################################################
    ###################################################################################
    # region Summary information
    ###################################################################################
    ###################################################################################

    def contains_require_or_assert(self):
        """
            Check if the node has a require or assert call
        Returns:
            bool: True if the node has a require or assert call
        """
        return any(c.name in ['require(bool)', 'require(bool,string)', 'assert(bool)'] for c in self.internal_calls)

    def contains_if(self, include_loop=True):
        """
            Check if the node is a IF node
        Returns:
            bool: True if the node is a conditional node (IF or IFLOOP)
        """
        if include_loop:
            return self.type in [NodeType.IF, NodeType.IFLOOP]
        return self.type == NodeType.IF

    def is_conditional(self, include_loop=True):
        """
            Check if the node is a conditional node
            A conditional node is either a IF or a require/assert or a RETURN bool
        Returns:
            bool: True if the node is a conditional node
        """
        if self.contains_if(include_loop) or self.contains_require_or_assert():
            return True
        if self.irs:
            last_ir = self.irs[-1]
            if last_ir:
                if isinstance(last_ir, Return):
                    for r in last_ir.read:
                        if r.type == ElementaryType('bool'):
                            return True
        return False



    # endregion
    ###################################################################################
    ###################################################################################
    # region Graph
    ###################################################################################
    ###################################################################################

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

    # endregion
    ###################################################################################
    ###################################################################################
    # region SlithIR
    ###################################################################################
    ###################################################################################

    @property
    def irs(self):
        """ Returns the slithIR representation

        return
            list(slithIR.Operation)
        """
        return self._irs

    @property
    def irs_ssa(self):
        """ Returns the slithIR representation with SSA

        return
            list(slithIR.Operation)
        """
        return self._irs_ssa

    @irs_ssa.setter
    def irs_ssa(self, irs):
       self._irs_ssa = irs

    def add_ssa_ir(self, ir):
        '''
            Use to place phi operation
        '''
        self._irs_ssa.append(ir)

    def slithir_generation(self):
        if self.expression:
            expression = self.expression
            self._irs = convert_expression(expression, self)

        self._find_read_write_call()

    @staticmethod
    def _is_non_slithir_var(var):
        return not isinstance(var, (Constant, ReferenceVariable, TemporaryVariable, TupleVariable))

    @staticmethod
    def _is_valid_slithir_var(var):
        return isinstance(var, (ReferenceVariable, TemporaryVariable, TupleVariable))

    # endregion
    ###################################################################################
    ###################################################################################
    # region Dominators
    ###################################################################################
    ###################################################################################

    @property
    def dominators(self):
        '''
            Returns:
                set(Node)
        '''
        return self._dominators

    @property
    def immediate_dominator(self):
        '''
            Returns:
                Node or None
        '''
        return self._immediate_dominator

    @property
    def dominance_frontier(self):
        '''
            Returns:
                set(Node)
        '''
        return self._dominance_frontier

    @property
    def dominator_successors(self):
        return self._dom_successors

    @dominators.setter
    def dominators(self, dom):
        self._dominators = dom

    @immediate_dominator.setter
    def immediate_dominator(self, idom):
        self._immediate_dominator = idom

    @dominance_frontier.setter
    def dominance_frontier(self, dom):
        self._dominance_frontier = dom

    # endregion
    ###################################################################################
    ###################################################################################
    # region Phi operation
    ###################################################################################
    ###################################################################################

    @property
    def phi_origins_local_variables(self):
        return self._phi_origins_local_variables

    @property
    def phi_origins_state_variables(self):
        return self._phi_origins_state_variables

    def add_phi_origin_local_variable(self, variable, node):
        if variable.name not in self._phi_origins_local_variables:
            self._phi_origins_local_variables[variable.name] = (variable, set())
        (v, nodes) = self._phi_origins_local_variables[variable.name]
        assert v == variable
        nodes.add(node)

    def add_phi_origin_state_variable(self, variable, node):
        if variable.canonical_name not in self._phi_origins_state_variables:
            self._phi_origins_state_variables[variable.canonical_name] = (variable, set())
        (v, nodes) = self._phi_origins_state_variables[variable.canonical_name]
        assert v == variable
        nodes.add(node)




    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyses
    ###################################################################################
    ###################################################################################

    def _find_read_write_call(self):

        for ir in self.irs:

            self._slithir_vars |= set([v for v in ir.read if self._is_valid_slithir_var(v)])
            if isinstance(ir, OperationWithLValue):
                var = ir.lvalue
                if var and self._is_valid_slithir_var(var):
                    self._slithir_vars.add(var)

            if not isinstance(ir, (Phi, Index, Member)):
                self._vars_read += [v for v in ir.read if self._is_non_slithir_var(v)]
                for var in ir.read:
                    if isinstance(var, (ReferenceVariable)):
                        self._vars_read.append(var.points_to_origin)
            elif isinstance(ir, (Member, Index)):
                var = ir.variable_left if isinstance(ir, Member) else ir.variable_right
                if self._is_non_slithir_var(var):
                    self._vars_read.append(var)
                if isinstance(var, (ReferenceVariable)):
                    origin = var.points_to_origin
                    if self._is_non_slithir_var(origin):
                        self._vars_read.append(origin)

            if isinstance(ir, OperationWithLValue):
                if isinstance(ir, (Index, Member, Length, Balance)):
                    continue  # Don't consider Member and Index operations -> ReferenceVariable
                var = ir.lvalue
                if isinstance(var, (ReferenceVariable)):
                    var = var.points_to_origin
                if var and self._is_non_slithir_var(var):
                        self._vars_written.append(var)

            if isinstance(ir, InternalCall):
                self._internal_calls.append(ir.function)
            if isinstance(ir, SolidityCall):
                # TODO: consider removing dependancy of solidity_call to internal_call
                self._solidity_calls.append(ir.function)
                self._internal_calls.append(ir.function)
            if isinstance(ir, LowLevelCall):
                assert isinstance(ir.destination, (Variable, SolidityVariable))
                self._low_level_calls.append((ir.destination, ir.function_name.value))
            elif isinstance(ir, (HighLevelCall)) and not isinstance(ir, LibraryCall):
                if isinstance(ir.destination.type, Contract):
                    self._high_level_calls.append((ir.destination.type, ir.function))
                elif ir.destination == SolidityVariable('this'):
                    self._high_level_calls.append((self.function.contract, ir.function))
                else:
                    try:
                        self._high_level_calls.append((ir.destination.type.type, ir.function))
                    except AttributeError:
                        raise SlitherException(f'Function not found on {ir}. Please try compiling with a recent Solidity version.')
            elif isinstance(ir, LibraryCall):
                assert isinstance(ir.destination, Contract)
                self._high_level_calls.append((ir.destination, ir.function))
                self._library_calls.append((ir.destination, ir.function))

        self._vars_read = list(set(self._vars_read))
        self._state_vars_read = [v for v in self._vars_read if isinstance(v, StateVariable)]
        self._local_vars_read = [v for v in self._vars_read if isinstance(v, LocalVariable)]
        self._solidity_vars_read = [v for v in self._vars_read if isinstance(v, SolidityVariable)]
        self._vars_written = list(set(self._vars_written))
        self._state_vars_written = [v for v in self._vars_written if isinstance(v, StateVariable)]
        self._local_vars_written = [v for v in self._vars_written if isinstance(v, LocalVariable)]
        self._internal_calls = list(set(self._internal_calls))
        self._solidity_calls = list(set(self._solidity_calls))
        self._high_level_calls = list(set(self._high_level_calls))
        self._library_calls = list(set(self._library_calls))
        self._low_level_calls = list(set(self._low_level_calls))

    @staticmethod
    def _convert_ssa(v):
        if isinstance(v, StateIRVariable):
            contract = v.contract
            non_ssa_var = contract.get_state_variable_from_name(v.name)
            return non_ssa_var
        assert isinstance(v, LocalIRVariable)
        function = v.function
        non_ssa_var = function.get_local_variable_from_name(v.name)
        return non_ssa_var

    def update_read_write_using_ssa(self):
        if not self.expression:
            return
        for ir in self.irs_ssa:
            if isinstance(ir, (PhiCallback)):
                continue
            if not isinstance(ir, (Phi, Index, Member)):
                self._ssa_vars_read += [v for v in ir.read if isinstance(v,
                                                                         (StateIRVariable,
                                                                          LocalIRVariable))]
                for var in ir.read:
                    if isinstance(var, (ReferenceVariable)):
                        origin = var.points_to_origin
                        if isinstance(origin, (StateIRVariable, LocalIRVariable)):
                            self._ssa_vars_read.append(origin)

            elif isinstance(ir, (Member, Index)):
                if isinstance(ir.variable_right, (StateIRVariable, LocalIRVariable)):
                    self._ssa_vars_read.append(ir.variable_right)
                if isinstance(ir.variable_right, (ReferenceVariable)):
                    origin = ir.variable_right.points_to_origin
                    if isinstance(origin, (StateIRVariable, LocalIRVariable)):
                        self._ssa_vars_read.append(origin)

            if isinstance(ir, OperationWithLValue):
                if isinstance(ir, (Index, Member, Length, Balance)):
                    continue  # Don't consider Member and Index operations -> ReferenceVariable
                var = ir.lvalue
                if isinstance(var, (ReferenceVariable)):
                    var = var.points_to_origin
                # Only store non-slithIR variables
                if var and isinstance(var, (StateIRVariable, LocalIRVariable)):
                    if isinstance(ir, (PhiCallback)):
                        continue
                    self._ssa_vars_written.append(var)
        self._ssa_vars_read = list(set(self._ssa_vars_read))
        self._ssa_state_vars_read = [v for v in self._ssa_vars_read if isinstance(v, StateVariable)]
        self._ssa_local_vars_read = [v for v in self._ssa_vars_read if isinstance(v, LocalVariable)]
        self._ssa_vars_written = list(set(self._ssa_vars_written))
        self._ssa_state_vars_written = [v for v in self._ssa_vars_written if isinstance(v, StateVariable)]
        self._ssa_local_vars_written = [v for v in self._ssa_vars_written if isinstance(v, LocalVariable)]

        vars_read = [self._convert_ssa(x) for x in self._ssa_vars_read]
        vars_written = [self._convert_ssa(x) for x in self._ssa_vars_written]


        self._vars_read += [v for v in vars_read if v not in self._vars_read]
        self._state_vars_read = [v for v in self._vars_read if isinstance(v, StateVariable)]
        self._local_vars_read = [v for v in self._vars_read if isinstance(v, LocalVariable)]

        self._vars_written += [v for v in vars_written if v not in self._vars_written]
        self._state_vars_written = [v for v in self._vars_written if isinstance(v, StateVariable)]
        self._local_vars_written = [v for v in self._vars_written if isinstance(v, LocalVariable)]


    # endregion
    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __str__(self):
        txt = NodeType.str(self._node_type) + ' '+ str(self.expression)
        return txt

    # endregion
