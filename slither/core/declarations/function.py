"""
    Function module
"""
import logging
from abc import abstractmethod, ABCMeta
from collections import namedtuple
from enum import Enum
from itertools import groupby
from typing import Dict, TYPE_CHECKING, List, Optional, Set, Union, Callable, Tuple

from slither.core.cfg.scope import Scope
from slither.core.declarations.solidity_variables import (
    SolidityFunction,
    SolidityVariable,
    SolidityVariableComposed,
)
from slither.core.expressions import (
    Identifier,
    IndexAccess,
    MemberAccess,
    UnaryOperation,
)
from slither.core.solidity_types.type import Type
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.utils.type import convert_type_for_solidity_signature_to_string
from slither.utils.utils import unroll

# pylint: disable=import-outside-toplevel,too-many-instance-attributes,too-many-statements,too-many-lines

if TYPE_CHECKING:
    from slither.utils.type_helpers import (
        InternalCallType,
        LowLevelCallType,
        HighLevelCallType,
        LibraryCallType,
    )
    from slither.core.declarations import Contract
    from slither.core.cfg.node import Node, NodeType
    from slither.core.variables.variable import Variable
    from slither.slithir.variables.variable import SlithIRVariable
    from slither.slithir.variables import LocalIRVariable
    from slither.core.expressions.expression import Expression
    from slither.slithir.operations import Operation
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.core.scope.scope import FileScope

LOGGER = logging.getLogger("Function")
ReacheableNode = namedtuple("ReacheableNode", ["node", "ir"])


class ModifierStatements:
    def __init__(
        self,
        modifier: Union["Contract", "Function"],
        entry_point: "Node",
        nodes: List["Node"],
    ):
        self._modifier = modifier
        self._entry_point = entry_point
        self._nodes = nodes

    @property
    def modifier(self) -> Union["Contract", "Function"]:
        return self._modifier

    @property
    def entry_point(self) -> "Node":
        return self._entry_point

    @entry_point.setter
    def entry_point(self, entry_point: "Node"):
        self._entry_point = entry_point

    @property
    def nodes(self) -> List["Node"]:
        return self._nodes

    @nodes.setter
    def nodes(self, nodes: List["Node"]):
        self._nodes = nodes


class FunctionType(Enum):
    NORMAL = 0
    CONSTRUCTOR = 1
    FALLBACK = 2
    RECEIVE = 3
    CONSTRUCTOR_VARIABLES = 10  # Fake function to hold variable declaration statements
    CONSTRUCTOR_CONSTANT_VARIABLES = 11  # Fake function to hold variable declaration statements


def _filter_state_variables_written(expressions: List["Expression"]):
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


class FunctionLanguage(Enum):
    Solidity = 0
    Yul = 1
    Vyper = 2


class Function(SourceMapping, metaclass=ABCMeta):  # pylint: disable=too-many-public-methods
    """
    Function class
    """

    def __init__(self, compilation_unit: "SlitherCompilationUnit"):
        super().__init__()
        self._internal_scope: List[str] = []
        self._name: Optional[str] = None
        self._view: bool = False
        self._pure: bool = False
        self._payable: bool = False
        self._visibility: Optional[str] = None

        self._is_implemented: Optional[bool] = None
        self._is_empty: Optional[bool] = None
        self._entry_point: Optional["Node"] = None
        self._nodes: List["Node"] = []
        self._variables: Dict[str, "LocalVariable"] = {}
        # slithir Temporary and references variables (but not SSA)
        self._slithir_variables: Set["SlithIRVariable"] = set()
        self._parameters: List["LocalVariable"] = []
        self._parameters_ssa: List["LocalIRVariable"] = []
        self._parameters_src: SourceMapping = SourceMapping()
        self._returns: List["LocalVariable"] = []
        self._returns_ssa: List["LocalIRVariable"] = []
        self._returns_src: SourceMapping = SourceMapping()
        self._return_values: Optional[List["SlithIRVariable"]] = None
        self._return_values_ssa: Optional[List["SlithIRVariable"]] = None
        self._vars_read: List["Variable"] = []
        self._vars_written: List["Variable"] = []
        self._state_vars_read: List["StateVariable"] = []
        self._vars_read_or_written: List["Variable"] = []
        self._solidity_vars_read: List["SolidityVariable"] = []
        self._state_vars_written: List["StateVariable"] = []
        self._internal_calls: List["InternalCallType"] = []
        self._solidity_calls: List["SolidityFunction"] = []
        self._low_level_calls: List["LowLevelCallType"] = []
        self._high_level_calls: List["HighLevelCallType"] = []
        self._library_calls: List["LibraryCallType"] = []
        self._external_calls_as_expressions: List["Expression"] = []
        self._expression_vars_read: List["Expression"] = []
        self._expression_vars_written: List["Expression"] = []
        self._expression_calls: List["Expression"] = []
        # self._expression_modifiers: List["Expression"] = []
        self._modifiers: List[ModifierStatements] = []
        self._explicit_base_constructor_calls: List[ModifierStatements] = []
        self._contains_assembly: bool = False

        self._expressions: Optional[List["Expression"]] = None
        self._slithir_operations: Optional[List["Operation"]] = None
        self._slithir_ssa_operations: Optional[List["Operation"]] = None

        self._all_expressions: Optional[List["Expression"]] = None
        self._all_slithir_operations: Optional[List["Operation"]] = None
        self._all_internals_calls: Optional[List["InternalCallType"]] = None
        self._all_high_level_calls: Optional[List["HighLevelCallType"]] = None
        self._all_library_calls: Optional[List["LibraryCallType"]] = None
        self._all_low_level_calls: Optional[List["LowLevelCallType"]] = None
        self._all_solidity_calls: Optional[List["SolidityFunction"]] = None
        self._all_state_variables_read: Optional[List["StateVariable"]] = None
        self._all_solidity_variables_read: Optional[List["SolidityVariable"]] = None
        self._all_state_variables_written: Optional[List["StateVariable"]] = None
        self._all_slithir_variables: Optional[List["SlithIRVariable"]] = None
        self._all_nodes: Optional[List["Node"]] = None
        self._all_conditional_state_variables_read: Optional[List["StateVariable"]] = None
        self._all_conditional_state_variables_read_with_loop: Optional[List["StateVariable"]] = None
        self._all_conditional_solidity_variables_read: Optional[List["SolidityVariable"]] = None
        self._all_conditional_solidity_variables_read_with_loop: Optional[
            List["SolidityVariable"]
        ] = None
        self._all_solidity_variables_used_as_args: Optional[List["SolidityVariable"]] = None

        self._is_shadowed: bool = False
        self._shadows: bool = False

        # set(ReacheableNode)
        self._reachable_from_nodes: Set[ReacheableNode] = set()
        self._reachable_from_functions: Set[ReacheableNode] = set()

        # Constructor, fallback, State variable constructor
        self._function_type: Optional[FunctionType] = None
        self._is_constructor: Optional[bool] = None

        # Computed on the fly, can be True of False
        self._can_reenter: Optional[bool] = None
        self._can_send_eth: Optional[bool] = None

        self._nodes_ordered_dominators: Optional[List["Node"]] = None

        self._counter_nodes = 0

        # Memoize parameters:
        # TODO: identify all the memoize parameters and add a way to undo the memoization
        self._full_name: Optional[str] = None
        self._signature: Optional[Tuple[str, List[str], List[str]]] = None
        self._solidity_signature: Optional[str] = None
        self._signature_str: Optional[str] = None
        self._canonical_name: Optional[str] = None
        self._is_protected: Optional[bool] = None

        self.compilation_unit: "SlitherCompilationUnit" = compilation_unit

        # Assume we are analyzing Solidty by default
        self.function_language: FunctionLanguage = FunctionLanguage.Solidity

        self._id: Optional[str] = None

    ###################################################################################
    ###################################################################################
    # region General properties
    ###################################################################################
    ###################################################################################

    @property
    def name(self) -> str:
        """
        str: function name
        """
        if self._name == "" and self._function_type == FunctionType.CONSTRUCTOR:
            return "constructor"
        if self._function_type == FunctionType.FALLBACK:
            return "fallback"
        if self._function_type == FunctionType.RECEIVE:
            return "receive"
        if self._function_type == FunctionType.CONSTRUCTOR_VARIABLES:
            return "slitherConstructorVariables"
        if self._function_type == FunctionType.CONSTRUCTOR_CONSTANT_VARIABLES:
            return "slitherConstructorConstantVariables"
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._name = new_name

    @property
    def internal_scope(self) -> List[str]:
        """
        Return a list of name representing the scope of the function
        This is used to model nested functions declared in YUL

        :return:
        """
        return self._internal_scope

    @internal_scope.setter
    def internal_scope(self, new_scope: List[str]):
        self._internal_scope = new_scope

    @property
    def full_name(self) -> str:
        """
        str: func_name(type1,type2)
        Return the function signature without the return values
        The difference between this function and solidity_function is that full_name does not translate the underlying
        type (ex: structure, contract to address, ...)
        """
        if self._full_name is None:
            name, parameters, _ = self.signature
            full_name = ".".join(self._internal_scope + [name]) + "(" + ",".join(parameters) + ")"
            self._full_name = full_name
        return self._full_name

    @property
    @abstractmethod
    def canonical_name(self) -> str:
        """
        str: contract.func_name(type1,type2)
        Return the function signature without the return values
        """
        return ""

    @property
    def contains_assembly(self) -> bool:
        return self._contains_assembly

    @contains_assembly.setter
    def contains_assembly(self, c: bool):
        self._contains_assembly = c

    def can_reenter(self, callstack=None) -> bool:
        """
        Check if the function can re-enter
        Follow internal calls.
        Do not consider CREATE as potential re-enter, but check if the
        destination's constructor can contain a call (recurs. follow nested CREATE)
        For Solidity > 0.5, filter access to public variables and constant/pure/view
        For call to this. check if the destination can re-enter
        Do not consider Send/Transfer as there is not enough gas
        :param callstack: used internally to check for recursion
        :return bool:
        """
        from slither.slithir.operations import Call

        if self._can_reenter is None:
            self._can_reenter = False
            for ir in self.all_slithir_operations():
                if isinstance(ir, Call) and ir.can_reenter(callstack):
                    self._can_reenter = True
                    return True
        return self._can_reenter

    def can_send_eth(self) -> bool:
        """
        Check if the function or any internal (not external) functions called by it can send eth
        :return bool:
        """
        from slither.slithir.operations import Call

        if self._can_send_eth is None:
            self._can_send_eth = False
            for ir in self.all_slithir_operations():
                if isinstance(ir, Call) and ir.can_send_eth():
                    self._can_send_eth = True
                    return True
        return self._can_send_eth

    @property
    def is_checked(self) -> bool:
        """
        Return true if the overflow are enabled by default


        :return:
        """

        return self.compilation_unit.solc_version >= "0.8.0"

    @property
    def id(self) -> Optional[str]:
        """
        Return the ID of the funciton. For Solidity with compact-AST the ID is the reference ID
        For other, the ID is None

        :return:
        :rtype:
        """
        return self._id

    @id.setter
    def id(self, new_id: str):
        self._id = new_id

    @property
    @abstractmethod
    def file_scope(self) -> "FileScope":
        pass

    # endregion
    ###################################################################################
    ###################################################################################
    # region Type (FunctionType)
    ###################################################################################
    ###################################################################################

    def set_function_type(self, t: FunctionType):
        assert isinstance(t, FunctionType)
        self._function_type = t

    @property
    def function_type(self) -> Optional[FunctionType]:
        return self._function_type

    @function_type.setter
    def function_type(self, t: FunctionType):
        self._function_type = t

    @property
    def is_constructor(self) -> bool:
        """
        bool: True if the function is the constructor
        """
        return self._function_type == FunctionType.CONSTRUCTOR

    @property
    def is_constructor_variables(self) -> bool:
        """
        bool: True if the function is the constructor of the variables
        Slither has inbuilt functions to hold the state variables initialization
        """
        return self._function_type in [
            FunctionType.CONSTRUCTOR_VARIABLES,
            FunctionType.CONSTRUCTOR_CONSTANT_VARIABLES,
        ]

    @property
    def is_fallback(self) -> bool:
        """
            Determine if the function is the fallback function for the contract
        Returns
            (bool)
        """
        return self._function_type == FunctionType.FALLBACK

    @property
    def is_receive(self) -> bool:
        """
            Determine if the function is the receive function for the contract
        Returns
            (bool)
        """
        return self._function_type == FunctionType.RECEIVE

    # endregion
    ###################################################################################
    ###################################################################################
    # region Payable
    ###################################################################################
    ###################################################################################

    @property
    def payable(self) -> bool:
        """
        bool: True if the function is payable
        """
        return self._payable

    @payable.setter
    def payable(self, p: bool):
        self._payable = p

    # endregion
    ###################################################################################
    ###################################################################################
    # region Visibility
    ###################################################################################
    ###################################################################################

    @property
    def visibility(self) -> str:
        """
        str: Function visibility
        """
        assert self._visibility is not None
        return self._visibility

    @visibility.setter
    def visibility(self, v: str):
        self._visibility = v

    def set_visibility(self, v: str):
        self._visibility = v

    @property
    def view(self) -> bool:
        """
        bool: True if the function is declared as view
        """
        return self._view

    @view.setter
    def view(self, v: bool):
        self._view = v

    @property
    def pure(self) -> bool:
        """
        bool: True if the function is declared as pure
        """
        return self._pure

    @pure.setter
    def pure(self, p: bool):
        self._pure = p

    @property
    def is_shadowed(self) -> bool:
        return self._is_shadowed

    @is_shadowed.setter
    def is_shadowed(self, is_shadowed):
        self._is_shadowed = is_shadowed

    @property
    def shadows(self) -> bool:
        return self._shadows

    @shadows.setter
    def shadows(self, _shadows: bool):
        self._shadows = _shadows

    # endregion
    ###################################################################################
    ###################################################################################
    # region Function's body
    ###################################################################################
    ###################################################################################

    @property
    def is_implemented(self) -> bool:
        """
        bool: True if the function is implemented
        """
        return self._is_implemented

    @is_implemented.setter
    def is_implemented(self, is_impl: bool):
        self._is_implemented = is_impl

    @property
    def is_empty(self) -> bool:
        """
        bool: True if the function is empty, None if the function is an interface
        """
        return self._is_empty

    @is_empty.setter
    def is_empty(self, empty: bool):
        self._is_empty = empty

    # endregion
    ###################################################################################
    ###################################################################################
    # region Nodes
    ###################################################################################
    ###################################################################################

    @property
    def nodes(self) -> List["Node"]:
        """
        list(Node): List of the nodes
        """
        return list(self._nodes)

    @nodes.setter
    def nodes(self, nodes: List["Node"]):
        self._nodes = nodes

    @property
    def entry_point(self) -> Optional["Node"]:
        """
        Node: Entry point of the function
        """
        return self._entry_point

    @entry_point.setter
    def entry_point(self, node: "Node"):
        self._entry_point = node

    def add_node(self, node: "Node"):
        if not self._entry_point:
            self._entry_point = node
        self._nodes.append(node)

    @property
    def nodes_ordered_dominators(self) -> List["Node"]:
        # TODO: does not work properly; most likely due to modifier call
        # This will not work for modifier call that lead to multiple nodes
        # from slither.core.cfg.node import NodeType
        if self._nodes_ordered_dominators is None:
            self._nodes_ordered_dominators = []
            if self.entry_point:
                self._compute_nodes_ordered_dominators(self.entry_point)

            for node in self.nodes:
                # if node.type == NodeType.OTHER_ENTRYPOINT:
                if not node in self._nodes_ordered_dominators:
                    self._compute_nodes_ordered_dominators(node)

        return self._nodes_ordered_dominators

    def _compute_nodes_ordered_dominators(self, node: "Node"):
        assert self._nodes_ordered_dominators is not None
        if node in self._nodes_ordered_dominators:
            return
        self._nodes_ordered_dominators.append(node)
        for dom in node.dominance_exploration_ordered:
            self._compute_nodes_ordered_dominators(dom)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Parameters
    ###################################################################################
    ###################################################################################

    @property
    def parameters(self) -> List["LocalVariable"]:
        """
        list(LocalVariable): List of the parameters
        """
        return list(self._parameters)

    def add_parameters(self, p: "LocalVariable"):
        self._parameters.append(p)

    @property
    def parameters_ssa(self) -> List["LocalIRVariable"]:
        """
        list(LocalIRVariable): List of the parameters (SSA form)
        """
        return list(self._parameters_ssa)

    def add_parameter_ssa(self, var: "LocalIRVariable"):
        self._parameters_ssa.append(var)

    def parameters_src(self) -> SourceMapping:
        return self._parameters_src

    # endregion
    ###################################################################################
    ###################################################################################
    # region Return values
    ###################################################################################
    ###################################################################################

    @property
    def return_type(self) -> Optional[List[Type]]:
        """
        Return the list of return type
        If no return, return None
        """
        returns = self.returns
        if returns:
            return [r.type for r in returns]
        return None

    def returns_src(self) -> SourceMapping:
        return self._returns_src

    @property
    def type(self) -> Optional[List[Type]]:
        """
        Return the list of return type
        If no return, return None
        Alias of return_type
        """
        return self.return_type

    @property
    def returns(self) -> List["LocalVariable"]:
        """
        list(LocalVariable): List of the return variables
        """
        return list(self._returns)

    def add_return(self, r: "LocalVariable"):
        self._returns.append(r)

    @property
    def returns_ssa(self) -> List["LocalIRVariable"]:
        """
        list(LocalIRVariable): List of the return variables (SSA form)
        """
        return list(self._returns_ssa)

    def add_return_ssa(self, var: "LocalIRVariable"):
        self._returns_ssa.append(var)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Modifiers
    ###################################################################################
    ###################################################################################

    @property
    def modifiers(self) -> List[Union["Contract", "Function"]]:
        """
        list(Modifier): List of the modifiers
        Can be contract for constructor's calls

        """
        return [c.modifier for c in self._modifiers]

    def add_modifier(self, modif: "ModifierStatements"):
        self._modifiers.append(modif)

    @property
    def modifiers_statements(self) -> List[ModifierStatements]:
        """
        list(ModifierCall): List of the modifiers call (include expression and irs)
        """
        return list(self._modifiers)

    @property
    def explicit_base_constructor_calls(self) -> List["Function"]:
        """
        list(Function): List of the base constructors called explicitly by this presumed constructor definition.

                        Base constructors implicitly or explicitly called by the contract definition will not be
                        included.
        """
        # This is a list of contracts internally, so we convert it to a list of constructor functions.
        return [
            c.modifier.constructors_declared
            for c in self._explicit_base_constructor_calls
            if c.modifier.constructors_declared
        ]

    @property
    def explicit_base_constructor_calls_statements(self) -> List[ModifierStatements]:
        """
        list(ModifierCall): List of the base constructors called explicitly by this presumed constructor definition.

        """
        # This is a list of contracts internally, so we convert it to a list of constructor functions.
        return list(self._explicit_base_constructor_calls)

    def add_explicit_base_constructor_calls_statements(self, modif: ModifierStatements):
        self._explicit_base_constructor_calls.append(modif)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################

    @property
    def variables(self) -> List[LocalVariable]:
        """
        Return all local variables
        Include paramters and return values
        """
        return list(self._variables.values())

    @property
    def local_variables(self) -> List[LocalVariable]:
        """
        Return all local variables (dont include paramters and return values)
        """
        return list(set(self.variables) - set(self.returns) - set(self.parameters))

    @property
    def variables_as_dict(self) -> Dict[str, LocalVariable]:
        return self._variables

    @property
    def variables_read(self) -> List["Variable"]:
        """
        list(Variable): Variables read (local/state/solidity)
        """
        return list(self._vars_read)

    @property
    def variables_written(self) -> List["Variable"]:
        """
        list(Variable): Variables written (local/state/solidity)
        """
        return list(self._vars_written)

    @property
    def state_variables_read(self) -> List["StateVariable"]:
        """
        list(StateVariable): State variables read
        """
        return list(self._state_vars_read)

    @property
    def solidity_variables_read(self) -> List["SolidityVariable"]:
        """
        list(SolidityVariable): Solidity variables read
        """
        return list(self._solidity_vars_read)

    @property
    def state_variables_written(self) -> List["StateVariable"]:
        """
        list(StateVariable): State variables written
        """
        return list(self._state_vars_written)

    @property
    def variables_read_or_written(self) -> List["Variable"]:
        """
        list(Variable): Variables read or written (local/state/solidity)
        """
        return list(self._vars_read_or_written)

    @property
    def variables_read_as_expression(self) -> List["Expression"]:
        return self._expression_vars_read

    @property
    def variables_written_as_expression(self) -> List["Expression"]:
        return self._expression_vars_written

    @property
    def slithir_variables(self) -> List["SlithIRVariable"]:
        """
        Temporary and Reference Variables (not SSA form)
        """

        return list(self._slithir_variables)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Calls
    ###################################################################################
    ###################################################################################

    @property
    def internal_calls(self) -> List["InternalCallType"]:
        """
        list(Function or SolidityFunction): List of function calls (that does not create a transaction)
        """
        return list(self._internal_calls)

    @property
    def solidity_calls(self) -> List[SolidityFunction]:
        """
        list(SolidityFunction): List of Soldity calls
        """
        return list(self._solidity_calls)

    @property
    def high_level_calls(self) -> List["HighLevelCallType"]:
        """
        list((Contract, Function|Variable)):
        List of high level calls (external calls).
        A variable is called in case of call to a public state variable
        Include library calls
        """
        return list(self._high_level_calls)

    @property
    def library_calls(self) -> List["LibraryCallType"]:
        """
        list((Contract, Function)):
        """
        return list(self._library_calls)

    @property
    def low_level_calls(self) -> List["LowLevelCallType"]:
        """
        list((Variable|SolidityVariable, str)): List of low_level call
        A low level call is defined by
        - the variable called
        - the name of the function (call/delegatecall/codecall)
        """
        return list(self._low_level_calls)

    @property
    def external_calls_as_expressions(self) -> List["Expression"]:
        """
        list(ExpressionCall): List of message calls (that creates a transaction)
        """
        return list(self._external_calls_as_expressions)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Expressions
    ###################################################################################
    ###################################################################################

    @property
    def calls_as_expressions(self) -> List["Expression"]:
        return self._expression_calls

    @property
    def expressions(self) -> List["Expression"]:
        """
        list(Expression): List of the expressions
        """
        if self._expressions is None:
            expressionss = [n.expression for n in self.nodes]
            expressions = [e for e in expressionss if e]
            self._expressions = expressions
        return self._expressions

    @property
    def return_values(self) -> List["SlithIRVariable"]:
        """
        list(Return Values): List of the return values
        """
        from slither.core.cfg.node import NodeType
        from slither.slithir.operations import Return
        from slither.slithir.variables import Constant

        if self._return_values is None:
            return_values = []
            returns = [n for n in self.nodes if n.type == NodeType.RETURN]
            [  # pylint: disable=expression-not-assigned
                return_values.extend(ir.values)
                for node in returns
                for ir in node.irs
                if isinstance(ir, Return)
            ]
            self._return_values = list({x for x in return_values if not isinstance(x, Constant)})
        return self._return_values

    @property
    def return_values_ssa(self) -> List["SlithIRVariable"]:
        """
        list(Return Values in SSA form): List of the return values in ssa form
        """
        from slither.core.cfg.node import NodeType
        from slither.slithir.operations import Return
        from slither.slithir.variables import Constant

        if self._return_values_ssa is None:
            return_values_ssa = []
            returns = [n for n in self.nodes if n.type == NodeType.RETURN]
            [  # pylint: disable=expression-not-assigned
                return_values_ssa.extend(ir.values)
                for node in returns
                for ir in node.irs_ssa
                if isinstance(ir, Return)
            ]
            self._return_values_ssa = list(
                {x for x in return_values_ssa if not isinstance(x, Constant)}
            )
        return self._return_values_ssa

    # endregion
    ###################################################################################
    ###################################################################################
    # region SlithIR
    ###################################################################################
    ###################################################################################

    @property
    def slithir_operations(self) -> List["Operation"]:
        """
        list(Operation): List of the slithir operations
        """
        if self._slithir_operations is None:
            operationss = [n.irs for n in self.nodes]
            operations = [item for sublist in operationss for item in sublist if item]
            self._slithir_operations = operations
        return self._slithir_operations

    @property
    def slithir_ssa_operations(self) -> List["Operation"]:
        """
        list(Operation): List of the slithir operations (SSA)
        """
        if self._slithir_ssa_operations is None:
            operationss = [n.irs_ssa for n in self.nodes]
            operations = [item for sublist in operationss for item in sublist if item]
            self._slithir_ssa_operations = operations
        return self._slithir_ssa_operations

    # endregion
    ###################################################################################
    ###################################################################################
    # region Signature
    ###################################################################################
    ###################################################################################

    @property
    def solidity_signature(self) -> str:
        """
        Return a signature following the Solidity Standard
        Contract and converted into address

        It might still keep internal types (ex: structure name) for internal functions.
        The reason is that internal functions allows recursive structure definition, which
        can't be converted following the Solidity stand ard

        :return: the solidity signature
        """
        if self._solidity_signature is None:
            parameters = [
                convert_type_for_solidity_signature_to_string(x.type) for x in self.parameters
            ]
            self._solidity_signature = self.name + "(" + ",".join(parameters) + ")"
        return self._solidity_signature

    @property
    def signature(self) -> Tuple[str, List[str], List[str]]:
        """
        (str, list(str), list(str)): Function signature as
        (name, list parameters type, list return values type)
        """
        if self._signature is None:
            signature = (
                self.name,
                [str(x.type) for x in self.parameters],
                [str(x.type) for x in self.returns],
            )
            self._signature = signature
        return self._signature

    @property
    def signature_str(self) -> str:
        """
        str: func_name(type1,type2) returns (type3)
        Return the function signature as a str (contains the return values)
        """
        if self._signature_str is None:
            name, parameters, returnVars = self.signature
            self._signature_str = (
                name + "(" + ",".join(parameters) + ") returns(" + ",".join(returnVars) + ")"
            )
        return self._signature_str

    # endregion
    ###################################################################################
    ###################################################################################
    # region Functions
    ###################################################################################
    ###################################################################################

    @property
    @abstractmethod
    def functions_shadowed(self) -> List["Function"]:
        pass

    # endregion
    ###################################################################################
    ###################################################################################
    # region Reachable
    ###################################################################################
    ###################################################################################

    @property
    def reachable_from_nodes(self) -> Set[ReacheableNode]:
        """
        Return
            ReacheableNode
        """
        return self._reachable_from_nodes

    @property
    def reachable_from_functions(self) -> Set[ReacheableNode]:
        return self._reachable_from_functions

    def add_reachable_from_node(self, n: "Node", ir: "Operation"):
        self._reachable_from_nodes.add(ReacheableNode(n, ir))
        self._reachable_from_functions.add(n.function)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Recursive getters
    ###################################################################################
    ###################################################################################

    def _explore_functions(self, f_new_values: Callable[["Function"], List]):
        values = f_new_values(self)
        explored = [self]
        to_explore = [
            c for c in self.internal_calls if isinstance(c, Function) and c not in explored
        ]
        to_explore += [
            c for (_, c) in self.library_calls if isinstance(c, Function) and c not in explored
        ]
        to_explore += [m for m in self.modifiers if m not in explored]

        while to_explore:
            f = to_explore[0]
            to_explore = to_explore[1:]
            if f in explored:
                continue
            explored.append(f)

            values += f_new_values(f)

            to_explore += [
                c
                for c in f.internal_calls
                if isinstance(c, Function) and c not in explored and c not in to_explore
            ]
            to_explore += [
                c
                for (_, c) in f.library_calls
                if isinstance(c, Function) and c not in explored and c not in to_explore
            ]
            to_explore += [m for m in f.modifiers if m not in explored and m not in to_explore]

        return list(set(values))

    def all_state_variables_read(self) -> List["StateVariable"]:
        """recursive version of variables_read"""
        if self._all_state_variables_read is None:
            self._all_state_variables_read = self._explore_functions(
                lambda x: x.state_variables_read
            )
        return self._all_state_variables_read

    def all_solidity_variables_read(self) -> List[SolidityVariable]:
        """recursive version of solidity_read"""
        if self._all_solidity_variables_read is None:
            self._all_solidity_variables_read = self._explore_functions(
                lambda x: x.solidity_variables_read
            )
        return self._all_solidity_variables_read

    def all_slithir_variables(self) -> List["SlithIRVariable"]:
        """recursive version of slithir_variables"""
        if self._all_slithir_variables is None:
            self._all_slithir_variables = self._explore_functions(lambda x: x.slithir_variables)
        return self._all_slithir_variables

    def all_nodes(self) -> List["Node"]:
        """recursive version of nodes"""
        if self._all_nodes is None:
            self._all_nodes = self._explore_functions(lambda x: x.nodes)
        return self._all_nodes

    def all_expressions(self) -> List["Expression"]:
        """recursive version of variables_read"""
        if self._all_expressions is None:
            self._all_expressions = self._explore_functions(lambda x: x.expressions)
        return self._all_expressions

    def all_slithir_operations(self) -> List["Operation"]:
        if self._all_slithir_operations is None:
            self._all_slithir_operations = self._explore_functions(lambda x: x.slithir_operations)
        return self._all_slithir_operations

    def all_state_variables_written(self) -> List[StateVariable]:
        """recursive version of variables_written"""
        if self._all_state_variables_written is None:
            self._all_state_variables_written = self._explore_functions(
                lambda x: x.state_variables_written
            )
        return self._all_state_variables_written

    def all_internal_calls(self) -> List["InternalCallType"]:
        """recursive version of internal_calls"""
        if self._all_internals_calls is None:
            self._all_internals_calls = self._explore_functions(lambda x: x.internal_calls)
        return self._all_internals_calls

    def all_low_level_calls(self) -> List["LowLevelCallType"]:
        """recursive version of low_level calls"""
        if self._all_low_level_calls is None:
            self._all_low_level_calls = self._explore_functions(lambda x: x.low_level_calls)
        return self._all_low_level_calls

    def all_high_level_calls(self) -> List["HighLevelCallType"]:
        """recursive version of high_level calls"""
        if self._all_high_level_calls is None:
            self._all_high_level_calls = self._explore_functions(lambda x: x.high_level_calls)
        return self._all_high_level_calls

    def all_library_calls(self) -> List["LibraryCallType"]:
        """recursive version of library calls"""
        if self._all_library_calls is None:
            self._all_library_calls = self._explore_functions(lambda x: x.library_calls)
        return self._all_library_calls

    def all_solidity_calls(self) -> List[SolidityFunction]:
        """recursive version of solidity calls"""
        if self._all_solidity_calls is None:
            self._all_solidity_calls = self._explore_functions(lambda x: x.solidity_calls)
        return self._all_solidity_calls

    @staticmethod
    def _explore_func_cond_read(func: "Function", include_loop: bool) -> List["StateVariable"]:
        ret = [n.state_variables_read for n in func.nodes if n.is_conditional(include_loop)]
        return [item for sublist in ret for item in sublist]

    def all_conditional_state_variables_read(self, include_loop=True) -> List["StateVariable"]:
        """
        Return the state variable used in a condition

        Over approximate and also return index access
        It won't work if the variable is assigned to a temp variable
        """
        if include_loop:
            if self._all_conditional_state_variables_read_with_loop is None:
                self._all_conditional_state_variables_read_with_loop = self._explore_functions(
                    lambda x: self._explore_func_cond_read(x, include_loop)
                )
            return self._all_conditional_state_variables_read_with_loop
        if self._all_conditional_state_variables_read is None:
            self._all_conditional_state_variables_read = self._explore_functions(
                lambda x: self._explore_func_cond_read(x, include_loop)
            )
        return self._all_conditional_state_variables_read

    @staticmethod
    def _solidity_variable_in_binary(node: "Node") -> List[SolidityVariable]:
        from slither.slithir.operations.binary import Binary

        ret = []
        for ir in node.irs:
            if isinstance(ir, Binary):
                ret += ir.read
        return [var for var in ret if isinstance(var, SolidityVariable)]

    @staticmethod
    def _explore_func_conditional(
        func: "Function",
        f: Callable[["Node"], List[SolidityVariable]],
        include_loop: bool,
    ):
        ret = [f(n) for n in func.nodes if n.is_conditional(include_loop)]
        return [item for sublist in ret for item in sublist]

    def all_conditional_solidity_variables_read(self, include_loop=True) -> List[SolidityVariable]:
        """
        Return the Soldiity variables directly used in a condtion

        Use of the IR to filter index access
        Assumption: the solidity vars are used directly in the conditional node
        It won't work if the variable is assigned to a temp variable
        """
        if include_loop:
            if self._all_conditional_solidity_variables_read_with_loop is None:
                self._all_conditional_solidity_variables_read_with_loop = self._explore_functions(
                    lambda x: self._explore_func_conditional(
                        x, self._solidity_variable_in_binary, include_loop
                    )
                )
            return self._all_conditional_solidity_variables_read_with_loop

        if self._all_conditional_solidity_variables_read is None:
            self._all_conditional_solidity_variables_read = self._explore_functions(
                lambda x: self._explore_func_conditional(
                    x, self._solidity_variable_in_binary, include_loop
                )
            )
        return self._all_conditional_solidity_variables_read

    @staticmethod
    def _solidity_variable_in_internal_calls(node: "Node") -> List[SolidityVariable]:
        from slither.slithir.operations.internal_call import InternalCall

        ret = []
        for ir in node.irs:
            if isinstance(ir, InternalCall):
                ret += ir.read
        return [var for var in ret if isinstance(var, SolidityVariable)]

    @staticmethod
    def _explore_func_nodes(func: "Function", f: Callable[["Node"], List[SolidityVariable]]):
        ret = [f(n) for n in func.nodes]
        return [item for sublist in ret for item in sublist]

    def all_solidity_variables_used_as_args(self) -> List[SolidityVariable]:
        """
        Return the Soldiity variables directly used in a call

        Use of the IR to filter index access
        Used to catch check(msg.sender)
        """
        if self._all_solidity_variables_used_as_args is None:
            self._all_solidity_variables_used_as_args = self._explore_functions(
                lambda x: self._explore_func_nodes(x, self._solidity_variable_in_internal_calls)
            )
        return self._all_solidity_variables_used_as_args

    # endregion
    ###################################################################################
    ###################################################################################
    # region Visitor
    ###################################################################################
    ###################################################################################

    def apply_visitor(self, Visitor: Callable) -> List:
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

    # endregion
    ###################################################################################
    ###################################################################################
    # region Getters from/to object
    ###################################################################################
    ###################################################################################

    def get_local_variable_from_name(self, variable_name: str) -> Optional[LocalVariable]:
        """
            Return a local variable from a name

        Args:
            variable_name (str): name of the variable
        Returns:
            LocalVariable
        """
        return next((v for v in self.variables if v.name == variable_name), None)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Export
    ###################################################################################
    ###################################################################################

    def cfg_to_dot(self, filename: str):
        """
            Export the function to a dot file
        Args:
            filename (str)
        """
        with open(filename, "w", encoding="utf8") as f:
            f.write("digraph{\n")
            for node in self.nodes:
                f.write(f'{node.node_id}[label="{str(node)}"];\n')
                for son in node.sons:
                    f.write(f"{node.node_id}->{son.node_id};\n")

            f.write("}\n")

    def dominator_tree_to_dot(self, filename: str):
        """
            Export the dominator tree of the function to a dot file
        Args:
            filename (str)
        """

        def description(node):
            desc = f"{node}\n"
            desc += f"id: {node.node_id}"
            if node.dominance_frontier:
                desc += f"\ndominance frontier: {[n.node_id for n in node.dominance_frontier]}"
            return desc

        with open(filename, "w", encoding="utf8") as f:
            f.write("digraph{\n")
            for node in self.nodes:
                f.write(f'{node.node_id}[label="{description(node)}"];\n')
                if node.immediate_dominator:
                    f.write(f"{node.immediate_dominator.node_id}->{node.node_id};\n")

            f.write("}\n")

    def slithir_cfg_to_dot(self, filename: str):
        """
        Export the CFG to a DOT file. The nodes includes the Solidity expressions and the IRs
        :param filename:
        :return:
        """
        content = self.slithir_cfg_to_dot_str()
        with open(filename, "w", encoding="utf8") as f:
            f.write(content)

    def slithir_cfg_to_dot_str(self, skip_expressions=False) -> str:
        """
        Export the CFG to a DOT format. The nodes includes the Solidity expressions and the IRs
        :return: the DOT content
        :rtype: str
        """
        from slither.core.cfg.node import NodeType

        content = ""
        content += "digraph{\n"
        for node in self.nodes:
            label = f"Node Type: {str(node.type)} {node.node_id}\n"
            if node.expression and not skip_expressions:
                label += f"\nEXPRESSION:\n{node.expression}\n"
            if node.irs and not skip_expressions:
                label += "\nIRs:\n" + "\n".join([str(ir) for ir in node.irs])
            content += f'{node.node_id}[label="{label}"];\n'
            if node.type in [NodeType.IF, NodeType.IFLOOP]:
                true_node = node.son_true
                if true_node:
                    content += f'{node.node_id}->{true_node.node_id}[label="True"];\n'
                false_node = node.son_false
                if false_node:
                    content += f'{node.node_id}->{false_node.node_id}[label="False"];\n'
            else:
                for son in node.sons:
                    content += f"{node.node_id}->{son.node_id};\n"

        content += "}\n"
        return content

    # endregion
    ###################################################################################
    ###################################################################################
    # region Summary information
    ###################################################################################
    ###################################################################################

    def is_reading(self, variable: "Variable") -> bool:
        """
            Check if the function reads the variable
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is read
        """
        return variable in self.variables_read

    def is_reading_in_conditional_node(self, variable: "Variable") -> bool:
        """
            Check if the function reads the variable in a IF node
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is read
        """
        variables_reads = [n.variables_read for n in self.nodes if n.contains_if()]
        variables_read = [item for sublist in variables_reads for item in sublist]
        return variable in variables_read

    def is_reading_in_require_or_assert(self, variable: "Variable") -> bool:
        """
            Check if the function reads the variable in an require or assert
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is read
        """
        variables_reads = [n.variables_read for n in self.nodes if n.contains_require_or_assert()]
        variables_read = [item for sublist in variables_reads for item in sublist]
        return variable in variables_read

    def is_writing(self, variable: "Variable") -> bool:
        """
            Check if the function writes the variable
        Args:
            variable (Variable):
        Returns:
            bool: True if the variable is written
        """
        return variable in self.variables_written

    @abstractmethod
    def get_summary(
        self,
    ) -> Tuple[str, str, str, List[str], List[str], List[str], List[str], List[str]]:
        pass

    def is_protected(self) -> bool:
        """
            Determine if the function is protected using a check on msg.sender

            Consider onlyOwner as a safe modifier.
            If the owner functionality is incorrectly implemented, this will lead to incorrectly
            classify the function as protected

            Otherwise only detects if msg.sender is directly used in a condition
            For example, it wont work for:
                address a = msg.sender
                require(a == owner)
        Returns
            (bool)
        """

        if self._is_protected is None:
            if self.is_constructor:
                self._is_protected = True
                return True
            if "onlyOwner" in [m.name for m in self.modifiers]:
                self._is_protected = True
                return True
            conditional_vars = self.all_conditional_solidity_variables_read(include_loop=False)
            args_vars = self.all_solidity_variables_used_as_args()
            self._is_protected = (
                SolidityVariableComposed("msg.sender") in conditional_vars + args_vars
            )
        return self._is_protected

    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyses
    ###################################################################################
    ###################################################################################

    def _analyze_read_write(self):
        """Compute variables read/written/..."""
        write_var = [x.variables_written_as_expression for x in self.nodes]
        write_var = [x for x in write_var if x]
        write_var = [item for sublist in write_var for item in sublist]
        write_var = list(set(write_var))
        # Remove dupplicate if they share the same string representation
        write_var = [
            next(obj)
            for i, obj in groupby(sorted(write_var, key=lambda x: str(x)), lambda x: str(x))
        ]
        self._expression_vars_written = write_var

        write_var = [x.variables_written for x in self.nodes]
        write_var = [x for x in write_var if x]
        write_var = [item for sublist in write_var for item in sublist]
        write_var = list(set(write_var))
        # Remove dupplicate if they share the same string representation
        write_var = [
            next(obj)
            for i, obj in groupby(sorted(write_var, key=lambda x: str(x)), lambda x: str(x))
        ]
        self._vars_written = write_var

        read_var = [x.variables_read_as_expression for x in self.nodes]
        read_var = [x for x in read_var if x]
        read_var = [item for sublist in read_var for item in sublist]
        # Remove dupplicate if they share the same string representation
        read_var = [
            next(obj)
            for i, obj in groupby(sorted(read_var, key=lambda x: str(x)), lambda x: str(x))
        ]
        self._expression_vars_read = read_var

        read_var = [x.variables_read for x in self.nodes]
        read_var = [x for x in read_var if x]
        read_var = [item for sublist in read_var for item in sublist]
        # Remove dupplicate if they share the same string representation
        read_var = [
            next(obj)
            for i, obj in groupby(sorted(read_var, key=lambda x: str(x)), lambda x: str(x))
        ]
        self._vars_read = read_var

        self._state_vars_written = [
            x for x in self.variables_written if isinstance(x, StateVariable)
        ]
        self._state_vars_read = [x for x in self.variables_read if isinstance(x, StateVariable)]
        self._solidity_vars_read = [
            x for x in self.variables_read if isinstance(x, SolidityVariable)
        ]

        self._vars_read_or_written = self._vars_written + self._vars_read

        slithir_variables = [x.slithir_variables for x in self.nodes]
        slithir_variables = [x for x in slithir_variables if x]
        self._slithir_variables = [item for sublist in slithir_variables for item in sublist]

    def _analyze_calls(self):
        calls = [x.calls_as_expression for x in self.nodes]
        calls = [x for x in calls if x]
        calls = [item for sublist in calls for item in sublist]
        self._expression_calls = list(set(calls))

        internal_calls = [x.internal_calls for x in self.nodes]
        internal_calls = [x for x in internal_calls if x]
        internal_calls = [item for sublist in internal_calls for item in sublist]
        self._internal_calls = list(set(internal_calls))

        self._solidity_calls = [c for c in internal_calls if isinstance(c, SolidityFunction)]

        low_level_calls = [x.low_level_calls for x in self.nodes]
        low_level_calls = [x for x in low_level_calls if x]
        low_level_calls = [item for sublist in low_level_calls for item in sublist]
        self._low_level_calls = list(set(low_level_calls))

        high_level_calls = [x.high_level_calls for x in self.nodes]
        high_level_calls = [x for x in high_level_calls if x]
        high_level_calls = [item for sublist in high_level_calls for item in sublist]
        self._high_level_calls = list(set(high_level_calls))

        library_calls = [x.library_calls for x in self.nodes]
        library_calls = [x for x in library_calls if x]
        library_calls = [item for sublist in library_calls for item in sublist]
        self._library_calls = list(set(library_calls))

        external_calls_as_expressions = [x.external_calls_as_expressions for x in self.nodes]
        external_calls_as_expressions = [x for x in external_calls_as_expressions if x]
        external_calls_as_expressions = [
            item for sublist in external_calls_as_expressions for item in sublist
        ]
        self._external_calls_as_expressions = list(set(external_calls_as_expressions))

    # endregion
    ###################################################################################
    ###################################################################################
    # region Nodes
    ###################################################################################
    ###################################################################################

    def new_node(
        self, node_type: "NodeType", src: Union[str, Dict], scope: Union[Scope, "Function"]
    ) -> "Node":
        from slither.core.cfg.node import Node

        node = Node(node_type, self._counter_nodes, scope, self.file_scope)
        node.set_offset(src, self.compilation_unit)
        self._counter_nodes += 1
        node.set_function(self)
        self._nodes.append(node)

        return node

    # endregion
    ###################################################################################
    ###################################################################################
    # region SlithIr and SSA
    ###################################################################################
    ###################################################################################

    def _get_last_ssa_variable_instances(
        self, target_state: bool, target_local: bool
    ) -> Dict[str, Set["SlithIRVariable"]]:
        # pylint: disable=too-many-locals,too-many-branches
        from slither.slithir.variables import ReferenceVariable
        from slither.slithir.operations import OperationWithLValue
        from slither.core.cfg.node import NodeType

        if not self.is_implemented:
            return {}

        if self._entry_point is None:
            return {}
        # node, values
        to_explore: List[Tuple["Node", Dict]] = [(self._entry_point, {})]
        # node -> values
        explored: Dict = {}
        # name -> instances
        ret: Dict = {}

        while to_explore:
            node, values = to_explore[0]
            to_explore = to_explore[1::]

            if node.type != NodeType.ENTRYPOINT:
                for ir_ssa in node.irs_ssa:
                    if isinstance(ir_ssa, OperationWithLValue):
                        lvalue = ir_ssa.lvalue
                        if isinstance(lvalue, ReferenceVariable):
                            lvalue = lvalue.points_to_origin
                        if isinstance(lvalue, StateVariable) and target_state:
                            values[lvalue.canonical_name] = {lvalue}
                        if isinstance(lvalue, LocalVariable) and target_local:
                            values[lvalue.canonical_name] = {lvalue}

            # Check for fixpoint
            if node in explored:
                if values == explored[node]:
                    continue
                for k, instances in values.items():
                    if k not in explored[node]:
                        explored[node][k] = set()
                    explored[node][k] |= instances
                values = explored[node]
            else:
                explored[node] = values

            # Return condition
            if node.will_return:
                for name, instances in values.items():
                    if name not in ret:
                        ret[name] = set()
                    ret[name] |= instances

            for son in node.sons:
                to_explore.append((son, dict(values)))

        return ret

    def get_last_ssa_state_variables_instances(
        self,
    ) -> Dict[str, Set["SlithIRVariable"]]:
        return self._get_last_ssa_variable_instances(target_state=True, target_local=False)

    def get_last_ssa_local_variables_instances(
        self,
    ) -> Dict[str, Set["SlithIRVariable"]]:
        return self._get_last_ssa_variable_instances(target_state=False, target_local=True)

    @staticmethod
    def _unchange_phi(ir: "Operation"):
        from slither.slithir.operations import Phi, PhiCallback

        if not isinstance(ir, (Phi, PhiCallback)) or len(ir.rvalues) > 1:
            return False
        if not ir.rvalues:
            return True
        return ir.rvalues[0] == ir.lvalue

    def fix_phi(self, last_state_variables_instances, initial_state_variables_instances):
        from slither.slithir.operations import InternalCall, PhiCallback
        from slither.slithir.variables import Constant, StateIRVariable

        for node in self.nodes:
            for ir in node.irs_ssa:
                if node == self.entry_point:
                    if isinstance(ir.lvalue, StateIRVariable):
                        additional = [initial_state_variables_instances[ir.lvalue.canonical_name]]
                        additional += last_state_variables_instances[ir.lvalue.canonical_name]
                        ir.rvalues = list(set(additional + ir.rvalues))
                    # function parameter
                    else:
                        # find index of the parameter
                        idx = self.parameters.index(ir.lvalue.non_ssa_version)
                        # find non ssa version of that index
                        additional = [n.ir.arguments[idx] for n in self.reachable_from_nodes]
                        additional = unroll(additional)
                        additional = [a for a in additional if not isinstance(a, Constant)]
                        ir.rvalues = list(set(additional + ir.rvalues))
                if isinstance(ir, PhiCallback):
                    callee_ir = ir.callee_ir
                    if isinstance(callee_ir, InternalCall):
                        last_ssa = callee_ir.function.get_last_ssa_state_variables_instances()
                        if ir.lvalue.canonical_name in last_ssa:
                            ir.rvalues = list(last_ssa[ir.lvalue.canonical_name])
                        else:
                            ir.rvalues = [ir.lvalue]
                    else:
                        additional = last_state_variables_instances[ir.lvalue.canonical_name]
                        ir.rvalues = list(set(additional + ir.rvalues))

            node.irs_ssa = [ir for ir in node.irs_ssa if not self._unchange_phi(ir)]

    def generate_slithir_and_analyze(self):
        for node in self.nodes:
            node.slithir_generation()

        self._analyze_read_write()
        self._analyze_calls()

    @abstractmethod
    def generate_slithir_ssa(self, all_ssa_state_variables_instances):
        pass

    def update_read_write_using_ssa(self):
        for node in self.nodes:
            node.update_read_write_using_ssa()
        self._analyze_read_write()

    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __str__(self):
        return self.name

    # endregion
