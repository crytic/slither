"""
    Function module
"""
import logging
from itertools import groupby

from slither.core.children.child_contract import ChildContract
from slither.core.declarations.solidity_variables import (SolidityFunction,
                                                          SolidityVariable,
                                                          SolidityVariableComposed)
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.index_access import IndexAccess
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.unary_operation import UnaryOperation
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.state_variable import StateVariable

logger = logging.getLogger("Function")

class Function(ChildContract, SourceMapping):
    """
        Function class
    """

    def __init__(self):
        super(Function, self).__init__()
        self._name = None
        self._view = None
        self._pure = None
        self._payable = None
        self._visibility = None
        self._is_constructor = None
        self._is_implemented = None
        self._is_empty = None
        self._entry_point = None
        self._nodes = []
        self._variables = {}
        self._parameters = []
        self._returns = []
        self._vars_read = []
        self._vars_written = []
        self._state_vars_read = []
        self._vars_read_or_written = []
        self._solidity_vars_read = []
        self._state_vars_written = []
        self._internal_calls = []
        self._solidity_calls = []
        self._low_level_calls = []
        self._high_level_calls = []
        self._external_calls_as_expressions = []
        self._expression_vars_read = []
        self._expression_vars_written = []
        self._expression_calls = []
        self._expression_modifiers = []
        self._modifiers = []
        self._payable = False
        self._contains_assembly = False

    @property
    def contains_assembly(self):
        return self._contains_assembly

    @property
    def return_type(self):
        """
            Return the list of return type 
            If no return, return None
        """
        returns = self.returns
        if returns:
            return [r.type for r in returns]
        return None

    @property
    def name(self):
        """
            str: function name
        """
        if self._name == '':
            if self.is_constructor:
                return 'constructor'
            else:
                return 'fallback'
        return self._name

    @property
    def nodes(self):
        """
            list(Node): List of the nodes
        """
        return list(self._nodes)

    @property
    def entry_point(self):
        """
            Node: Entry point of the function
        """
        return self._entry_point

    @property
    def visibility(self):
        """
            str: Function visibility
        """
        return self._visibility

    @property
    def payable(self):
        """
            bool: True if the function is payable
        """
        return self._payable

    @property
    def is_constructor(self):
        """
            bool: True if the function is the constructor
        """
        return self._is_constructor or self._name == self.contract.name

    @property
    def view(self):
        """
            bool: True if the function is declared as view
        """
        return self._view

    @property
    def pure(self):
        """
            bool: True if the function is declared as pure
        """
        return self._pure

    @property
    def is_implemented(self):
        """
            bool: True if the function is implemented
        """
        return self._is_implemented

    @property
    def is_empty(self):
        """
            bool: True if the function is empty, None if the function is an interface
        """
        return self._is_empty

    @property
    def parameters(self):
        """
            list(LocalVariable): List of the parameters
        """
        return list(self._parameters)

    @property
    def returns(self):
        """
            list(LocalVariable): List of the return variables
        """
        return list(self._returns)

    @property
    def modifiers(self):
        """
            list(Modifier): List of the modifiers
        """
        return list(self._modifiers)

    def __str__(self):
        return self._name

    @property
    def variables(self):
        """
            Return all local variables
            Include paramters and return values
        """
        return list(self._variables.values())

    @property
    def local_variables(self):
        """
            Return all local variables (dont include paramters and return values)
        """
        return list(set(self.variables) - set(self.returns) - set(self.parameters))

    def variables_as_dict(self):
        return self._variables

    @property
    def variables_read(self):
        """
            list(Variable): Variables read (local/state/solidity)
        """
        return list(self._vars_read)

    @property
    def variables_written(self):
        """
            list(Variable): Variables written (local/state/solidity)
        """
        return list(self._vars_written)

    @property
    def state_variables_read(self):
        """
            list(StateVariable): State variables read
        """
        return list(self._state_vars_read)

    @property
    def solidity_variables_read(self):
        """
            list(SolidityVariable): Solidity variables read
        """
        return list(self._solidity_vars_read)

    @property
    def state_variables_written(self):
        """
            list(StateVariable): State variables written
        """
        return list(self._state_vars_written)

    @property
    def variables_read_or_written(self):
        """
            list(Variable): Variables read or written (local/state/solidity)
        """
        return list(self._vars_read_or_written)

    @property
    def variables_read_as_expression(self):
        return self._expression_vars_read

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
            list(ExpressionCall): List of message calls (that creates a transaction)
        """
        return list(self._external_calls_as_expressions)

    @property
    def calls_as_expressions(self):
        return self._expression_calls

    @property
    def expressions(self):
        """
            list(Expression): List of the expressions
        """
        expressions = [n.expression for n in self.nodes]
        expressions = [e for e in expressions if e]
        return expressions

    @property
    def signature(self):
        """
            (str, list(str), list(str)): Function signature as
            (name, list parameters type, list return values type)
        """
        return self.name, [str(x.type) for x in self.parameters], [str(x.type) for x in self.returns]

    @property
    def signature_str(self):
        """
            str: func_name(type1,type2) returns (type3)
            Return the function signature as a str (contains the return values)
        """
        name, parameters, returnVars = self.signature
        return name+'('+','.join(parameters)+') returns('+','.join(returnVars)+')'

    @property
    def full_name(self):
        """
            str: func_name(type1,type2)
            Return the function signature without the return values
        """
        name, parameters, _ = self.signature
        return name+'('+','.join(parameters)+')'


    @property
    def slither(self):
        return self.contract.slither

    def _filter_state_variables_written(self, expressions):
        ret = []
        for expression in expressions:
            if isinstance(expression, Identifier):
                ret.append(expression)
            if isinstance(expression, UnaryOperation):
                ret.append(expression.expression)
            if isinstance(expression, MemberAccess):
                ret.append(expression.expression)
            if isinstance(expression, IndexAccess):
                ret.append(expression.expression_left)
        return ret

    def _analyze_read_write(self):
        """ Compute variables read/written/...

        """
        write_var = [x.variables_written_as_expression for x in self.nodes]
        write_var = [x for x in write_var if x]
        write_var = [item for sublist in write_var for item in sublist]
        write_var = list(set(write_var))
        # Remove dupplicate if they share the same string representation
        write_var = [next(obj) for i, obj in groupby(sorted(write_var, key=lambda x: str(x)), lambda x: str(x))]
        self._expression_vars_written =  write_var

        write_var = [x.variables_written for x in self.nodes]
        write_var = [x for x in write_var if x]
        write_var = [item for sublist in write_var for item in sublist]
        write_var = list(set(write_var))
        # Remove dupplicate if they share the same string representation
        write_var = [next(obj) for i, obj in\
                    groupby(sorted(write_var, key=lambda x: str(x)), lambda x: str(x))]
        self._vars_written = write_var

        read_var = [x.variables_read_as_expression for x in self.nodes]
        read_var = [x for x in read_var if x]
        read_var = [item for sublist in read_var for item in sublist]
        # Remove dupplicate if they share the same string representation
        read_var = [next(obj) for i, obj in\
                    groupby(sorted(read_var, key=lambda x: str(x)), lambda x: str(x))]
        self._expression_vars_read = read_var

        read_var = [x.variables_read for x in self.nodes]
        read_var = [x for x in read_var if x]
        read_var = [item for sublist in read_var for item in sublist]
        # Remove dupplicate if they share the same string representation
        read_var = [next(obj) for i, obj in\
                    groupby(sorted(read_var, key=lambda x: str(x)), lambda x: str(x))]
        self._vars_read = read_var

        self._state_vars_written = [x for x in self.variables_written if\
                                    isinstance(x, StateVariable)]
        self._state_vars_read = [x for x in self.variables_read if\
                                    isinstance(x, (StateVariable))]
        self._solidity_vars_read = [x for x in self.variables_read if\
                                    isinstance(x, (SolidityVariable))]

        self._vars_read_or_written = self._vars_written + self._vars_read

    def _analyze_calls(self):
        calls = [x.calls_as_expression for x in self.nodes]
        calls = [x for x in calls if x]
        calls = [item for sublist in calls for item in sublist]
        # Remove dupplicate if they share the same string representation
        # TODO: check if groupby is still necessary here
        calls = [next(obj) for i, obj in\
                 groupby(sorted(calls, key=lambda x: str(x)), lambda x: str(x))]
        self._expression_calls = calls

        internal_calls = [x.internal_calls for x in self.nodes]
        internal_calls = [x for x in internal_calls if x]
        internal_calls = [item for sublist in internal_calls for item in sublist]
        internal_calls = [next(obj) for i, obj in
                          groupby(sorted(internal_calls, key=lambda x: str(x)), lambda x: str(x))]
        self._internal_calls = internal_calls

        self._solidity_calls = [c for c in internal_calls if isinstance(c, SolidityFunction)]

        low_level_calls = [x.low_level_calls for x in self.nodes]
        low_level_calls = [x for x in low_level_calls if x]
        low_level_calls = [item for sublist in low_level_calls for item in sublist]
        low_level_calls = [next(obj) for i, obj in
                          groupby(sorted(low_level_calls, key=lambda x: str(x)), lambda x: str(x))]

        self._low_level_calls = low_level_calls

        high_level_calls = [x.high_level_calls for x in self.nodes]
        high_level_calls = [x for x in high_level_calls if x]
        high_level_calls = [item for sublist in high_level_calls for item in sublist]
        high_level_calls = [next(obj) for i, obj in
                          groupby(sorted(high_level_calls, key=lambda x: str(x)), lambda x: str(x))]

        self._high_level_calls = high_level_calls

        external_calls_as_expressions = [x.external_calls_as_expressions for x in self.nodes]
        external_calls_as_expressions = [x for x in external_calls_as_expressions if x]
        external_calls_as_expressions = [item for sublist in external_calls_as_expressions for item in sublist]
        external_calls_as_expressions = [next(obj) for i, obj in
                          groupby(sorted(external_calls_as_expressions, key=lambda x: str(x)), lambda x: str(x))]
        self._external_calls_as_expressions = external_calls_as_expressions


    def _explore_functions(self, f_new_values):
        values = f_new_values(self)
        explored = [self]
        to_explore = [c for c in self.internal_calls if
                      isinstance(c, Function) and c not in explored]
        to_explore += [m for m in self.modifiers if m not in explored]

        while to_explore:
            f = to_explore[0]
            to_explore = to_explore[1:]
            if f in explored:
                continue
            explored.append(f)

            values += f_new_values(f)

            to_explore += [c for c in f.internal_calls if\
                           isinstance(c, Function) and c not in explored and c not in to_explore]
            to_explore += [m for m in f.modifiers if m not in explored and m not in to_explore]

        return list(set(values))

    def all_state_variables_read(self):
        """ recursive version of variables_read
        """
        return self._explore_functions(lambda x: x.state_variables_read)

    def all_solidity_variables_read(self):
        """ recursive version of solidity_read
        """
        return self._explore_functions(lambda x: x.solidity_variables_read)

    def all_expressions(self):
        """ recursive version of variables_read
        """
        return self._explore_functions(lambda x: x.expressions)

    def all_state_variables_written(self):
        """ recursive version of variables_written
        """
        return self._explore_functions(lambda x: x.state_variables_written)

    def all_internal_calls(self):
        """ recursive version of internal_calls
        """
        return self._explore_functions(lambda x: x.internal_calls)

    def all_conditional_state_variables_read(self):
        """
            Return the state variable used in a condition

            Over approximate and also return index access
            It won't work if the variable is assigned to a temp variable
        """
        def _explore_func(func):
            ret = [n.state_variables_read for n in func.nodes if n.is_conditional()]
            return [item for sublist in ret for item in sublist]
        return self._explore_functions(lambda x: _explore_func(x))

    def all_conditional_solidity_variables_read(self):
        """
            Return the Soldiity variables directly used in a condtion

            Use of the IR to filter index access
            Assumption: the solidity vars are used directly in the conditional node
            It won't work if the variable is assigned to a temp variable
        """
        from slither.slithir.operations.binary import Binary
        def _solidity_variable_in_node(node):
            ret = []
            for ir in node.irs:
                if isinstance(ir, Binary):
                    ret += ir.read
            return [var for var in ret if isinstance(var, SolidityVariable)]
        def _explore_func(func, f):
            ret = [f(n) for n in func.nodes if n.is_conditional()]
            return [item for sublist in ret for item in sublist]
        return self._explore_functions(lambda x: _explore_func(x, _solidity_variable_in_node))

    def all_solidity_variables_used_as_args(self):
        """
            Return the Soldiity variables directly used in a call

            Use of the IR to filter index access
            Used to catch check(msg.sender)
        """
        from slither.slithir.operations.internal_call import InternalCall
        def _solidity_variable_in_node(node):
            ret = []
            for ir in node.irs:
                if isinstance(ir, InternalCall):
                    ret += ir.read
            return [var for var in ret if isinstance(var, SolidityVariable)]
        def _explore_func(func, f):
            ret = [f(n) for n in func.nodes]
            return [item for sublist in ret for item in sublist]
        return self._explore_functions(lambda x: _explore_func(x, _solidity_variable_in_node))

    def is_reading(self, variable):
        """
            Check if the function reads the variable
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is read
        """
        return variable in self.variables_read

    def is_reading_in_conditional_node(self, variable):
        """
            Check if the function reads the variable in a IF node
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is read
        """
        variables_read = [n.variables_read for n in self.nodes if n.contains_if()]
        variables_read = [item for sublist in variables_read for item in sublist]
        return variable in variables_read

    def is_reading_in_require_or_assert(self, variable):
        """
            Check if the function reads the variable in an require or assert
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is read
        """
        variables_read = [n.variables_read for n in self.nodes if n.contains_require_or_assert()]
        variables_read = [item for sublist in variables_read for item in sublist]
        return variable in variables_read

    def is_writing(self, variable):
        """
            Check if the function writes the variable
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is written
        """
        return variable in self.variables_written

    def apply_visitor(self, Visitor):
        """
            Apply a visitor to all the function expressions
        Args:
            Visitor: slither.visitors
        Returns
            list(): results of the visit
        """
        expressions = self.expressions
        v = [Visitor(e).result() for e in expressions]
        return [item for sublist in v for item in sublist]


    def cfg_to_dot(self, filename):
        """
            Export the function to a dot file
        Args:
            filename (str)
        """
        with open(filename, 'w') as f:
            f.write('digraph{\n')
            for node in self.nodes:
                f.write('{}[label="{}"];\n'.format(node.node_id, str(node)))
                for son in node.sons:
                    f.write('{}->{};\n'.format(node.node_id, son.node_id))

            f.write("}\n")

    def slithir_cfg_to_dot(self, filename):
        """
            Export the function to a dot file
        Args:
            filename (str)
        """
        from slither.core.cfg.node import NodeType
        with open(filename, 'w') as f:
            f.write('digraph{\n')
            for node in self.nodes:
                label = 'Node Type: {}\n'.format(NodeType.str(node.type))
                if node.expression:
                    label += '\nEXPRESSION:\n{}\n'.format(node.expression)
                    label += '\nIRs:\n' + '\n'.join([str(ir) for ir in node.irs])
                f.write('{}[label="{}"];\n'.format(node.node_id, label))
                for son in node.sons:
                    f.write('{}->{};\n'.format(node.node_id, son.node_id))

            f.write("}\n")

    def get_summary(self):
        """
            Return the function summary
        Returns:
            (str, str, str, list(str), list(str), listr(str), list(str), list(str);
            contract_name, name, visibility, modifiers, vars read, vars written, internal_calls, external_calls_as_expressions
        """
        return (self.contract.name, self.full_name, self.visibility,
                [str(x) for x in self.modifiers],
                [str(x) for x in self.state_variables_read + self.solidity_variables_read],
                [str(x) for x in self.state_variables_written],
                [str(x) for x in self.internal_calls],
                [str(x) for x in self.external_calls_as_expressions])

    def is_protected(self):
        """
            Determine if the function is protected using a check on msg.sender

            Only detects if msg.sender is directly used in a condition
            For example, it wont work for:
                address a = msg.sender
                require(a == owner)
        Returns
            (bool)
        """

        if self.is_constructor:
            return True
        conditional_vars = self.all_conditional_solidity_variables_read()
        args_vars = self.all_solidity_variables_used_as_args()
        return SolidityVariableComposed('msg.sender') in conditional_vars + args_vars
