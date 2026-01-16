"""
Function module
"""

import logging
from abc import abstractmethod, ABCMeta
from collections import namedtuple
from enum import Enum
from itertools import groupby
from typing import Any, TYPE_CHECKING, Optional, Union
from collections.abc import Callable

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


if TYPE_CHECKING:
    from slither.core.declarations import Contract, FunctionContract
    from slither.core.cfg.node import Node, NodeType
    from slither.core.variables.variable import Variable
    from slither.slithir.variables.variable import SlithIRVariable
    from slither.slithir.variables import LocalIRVariable
    from slither.core.expressions.expression import Expression
    from slither.slithir.operations import (
        HighLevelCall,
        InternalCall,
        LibraryCall,
        LowLevelCall,
        SolidityCall,
        Operation,
    )
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.core.scope.scope import FileScope

LOGGER = logging.getLogger("Function")
ReacheableNode = namedtuple("ReacheableNode", ["node", "ir"])


class ModifierStatements:
    def __init__(
        self,
        modifier: Union["Contract", "Function"],
        entry_point: "Node",
        nodes: list["Node"],
    ) -> None:
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
    def nodes(self) -> list["Node"]:
        return self._nodes

    @nodes.setter
    def nodes(self, nodes: list["Node"]):
        self._nodes = nodes


class FunctionType(Enum):
    NORMAL = 0
    CONSTRUCTOR = 1
    FALLBACK = 2
    RECEIVE = 3
    CONSTRUCTOR_VARIABLES = 10  # Fake function to hold variable declaration statements
    CONSTRUCTOR_CONSTANT_VARIABLES = 11  # Fake function to hold variable declaration statements


def _filter_state_variables_written(expressions: list["Expression"]):
    ret = []

    for expression in expressions:
        if isinstance(expression, (Identifier, UnaryOperation, MemberAccess)):
            ret.append(expression.expression)
        elif isinstance(expression, IndexAccess):
            ret.append(expression.expression_left)
    return ret


class FunctionLanguage(Enum):
    Solidity = 0
    Yul = 1
    Vyper = 2


class Function(SourceMapping, metaclass=ABCMeta):
    """
    Function class
    """

    def __init__(self, compilation_unit: "SlitherCompilationUnit") -> None:
        super().__init__()
        self._internal_scope: list[str] = []
        self._name: str | None = None
        self._view: bool = False
        self._pure: bool = False
        self._payable: bool = False
        self._visibility: str | None = None
        self._virtual: bool = False
        self._overrides: list[FunctionContract] = []
        self._overridden_by: list[FunctionContract] = []

        self._is_implemented: bool | None = None
        self._is_empty: bool | None = None
        self._entry_point: Node | None = None
        self._nodes: list[Node] = []
        self._variables: dict[str, LocalVariable] = {}
        # slithir Temporary and references variables (but not SSA)
        self._slithir_variables: set[SlithIRVariable] = set()
        self._parameters: list[LocalVariable] = []
        self._parameters_ssa: list[LocalIRVariable] = []
        self._parameters_src: SourceMapping = SourceMapping()
        # This is used for vyper calls with default arguments
        self._default_args_as_expressions: list[Expression] = []
        self._returns: list[LocalVariable] = []
        self._returns_ssa: list[LocalIRVariable] = []
        self._returns_src: SourceMapping = SourceMapping()
        self._return_values: list[SlithIRVariable] | None = None
        self._return_values_ssa: list[SlithIRVariable] | None = None
        self._vars_read: list[Variable] = []
        self._vars_written: list[Variable] = []
        self._state_vars_read: list[StateVariable] = []
        self._vars_read_or_written: list[Variable] = []
        self._solidity_vars_read: list[SolidityVariable] = []
        self._state_vars_written: list[StateVariable] = []
        self._internal_calls: list[InternalCall] = []
        self._solidity_calls: list[SolidityCall] = []
        self._low_level_calls: list[LowLevelCall] = []
        self._high_level_calls: list[tuple[Contract, HighLevelCall]] = []
        self._library_calls: list[LibraryCall] = []
        self._external_calls_as_expressions: list[Expression] = []
        self._expression_vars_read: list[Expression] = []
        self._expression_vars_written: list[Expression] = []
        self._expression_calls: list[Expression] = []
        # self._expression_modifiers: List["Expression"] = []
        self._modifiers: list[ModifierStatements] = []
        self._explicit_base_constructor_calls: list[ModifierStatements] = []
        self._contains_assembly: bool = False

        self._expressions: list[Expression] | None = None
        self._slithir_operations: list[Operation] | None = None
        self._slithir_ssa_operations: list[Operation] | None = None

        self._all_expressions: list[Expression] | None = None
        self._all_slithir_operations: list[Operation] | None = None
        self._all_internals_calls: list[InternalCall] | None = None
        self._all_high_level_calls: list[tuple[Contract, HighLevelCall]] | None = None
        self._all_library_calls: list[LibraryCall] | None = None
        self._all_low_level_calls: list[LowLevelCall] | None = None
        self._all_solidity_calls: list[SolidityCall] | None = None
        self._all_variables_read: list[Variable] | None = None
        self._all_variables_written: list[Variable] | None = None
        self._all_state_variables_read: list[StateVariable] | None = None
        self._all_solidity_variables_read: list[SolidityVariable] | None = None
        self._all_state_variables_written: list[StateVariable] | None = None
        self._all_slithir_variables: list[SlithIRVariable] | None = None
        self._all_nodes: list[Node] | None = None
        self._all_conditional_state_variables_read: list[StateVariable] | None = None
        self._all_conditional_state_variables_read_with_loop: list[StateVariable] | None = None
        self._all_conditional_solidity_variables_read: list[SolidityVariable] | None = None
        self._all_conditional_solidity_variables_read_with_loop: list[SolidityVariable] | None = (
            None
        )
        self._all_solidity_variables_used_as_args: list[SolidityVariable] | None = None

        self._is_shadowed: bool = False
        self._shadows: bool = False

        # set(ReacheableNode)
        self._reachable_from_nodes: set[ReacheableNode] = set()
        self._reachable_from_functions: set[Function] = set()
        self._all_reachable_from_functions: set[Function] | None = None

        # Constructor, fallback, State variable constructor
        self._function_type: FunctionType | None = None
        self._is_constructor: bool | None = None

        # Computed on the fly, can be True of False
        self._can_reenter: bool | None = None
        self._can_send_eth: bool | None = None

        self._nodes_ordered_dominators: list[Node] | None = None

        self._counter_nodes = 0

        # Memoize parameters:
        # TODO: identify all the memoize parameters and add a way to undo the memoization
        self._full_name: str | None = None
        self._signature: tuple[str, list[str], list[str]] | None = None
        self._solidity_signature: str | None = None
        self._signature_str: str | None = None
        self._canonical_name: str | None = None
        self._is_protected: bool | None = None

        self.compilation_unit: SlitherCompilationUnit = compilation_unit

        self.function_language: FunctionLanguage = (
            FunctionLanguage.Solidity if compilation_unit.is_solidity else FunctionLanguage.Vyper
        )

        self._id: str | None = None

        # To be improved with a parsing of the documentation
        self.has_documentation: bool = False

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
        if self._name == "" and self._function_type == FunctionType.FALLBACK:
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
    def internal_scope(self) -> list[str]:
        """
        Return a list of name representing the scope of the function
        This is used to model nested functions declared in YUL

        :return:
        """
        return self._internal_scope

    @internal_scope.setter
    def internal_scope(self, new_scope: list[str]):
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

    def can_reenter(self, callstack: list[Union["Function", "Variable"]] | None = None) -> bool:
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
    def id(self) -> str | None:
        """
        Return the reference ID of the function, if available.

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

    def set_function_type(self, t: FunctionType) -> None:
        assert isinstance(t, FunctionType)
        self._function_type = t

    @property
    def function_type(self) -> FunctionType | None:
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
    # region Virtual
    ###################################################################################
    ###################################################################################

    @property
    def is_virtual(self) -> bool:
        """
        Note for Solidity < 0.6.0 it will always be false
        bool: True if the function is virtual
        """
        return self._virtual

    @is_virtual.setter
    def is_virtual(self, v: bool):
        self._virtual = v

    @property
    def is_override(self) -> bool:
        """
        Note for Solidity < 0.6.0 it will always be false
        bool: True if the function overrides a base function
        """
        return len(self._overrides) > 0

    @property
    def overridden_by(self) -> list["FunctionContract"]:
        """
        List["FunctionContract"]: List of functions in child contracts that override this function
        This may include distinct instances of the same function due to inheritance
        """
        return self._overridden_by

    @property
    def overrides(self) -> list["FunctionContract"]:
        """
        List["FunctionContract"]: List of functions in parent contracts that this function overrides
        This may include distinct instances of the same function due to inheritance
        """
        return self._overrides

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

    def set_visibility(self, v: str) -> None:
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
    def nodes(self) -> list["Node"]:
        """
        list(Node): List of the nodes
        """
        return list(self._nodes)

    @nodes.setter
    def nodes(self, nodes: list["Node"]):
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

    def add_node(self, node: "Node") -> None:
        if not self._entry_point:
            self._entry_point = node
        self._nodes.append(node)

    @property
    def nodes_ordered_dominators(self) -> list["Node"]:
        # TODO: does not work properly; most likely due to modifier call
        # This will not work for modifier call that lead to multiple nodes
        # from slither.core.cfg.node import NodeType
        if self._nodes_ordered_dominators is None:
            self._nodes_ordered_dominators = []
            if self.entry_point:
                self._compute_nodes_ordered_dominators(self.entry_point)

            for node in self.nodes:
                # if node.type == NodeType.OTHER_ENTRYPOINT:
                if node not in self._nodes_ordered_dominators:
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
    def parameters(self) -> list["LocalVariable"]:
        """
        list(LocalVariable): List of the parameters
        """
        return list(self._parameters)

    def add_parameters(self, p: "LocalVariable") -> None:
        self._parameters.append(p)

    @property
    def parameters_ssa(self) -> list["LocalIRVariable"]:
        """
        list(LocalIRVariable): List of the parameters (SSA form)
        """
        return list(self._parameters_ssa)

    def add_parameter_ssa(self, var: "LocalIRVariable") -> None:
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
    def return_type(self) -> list[Type] | None:
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
    def type(self) -> list[Type] | None:
        """
        Return the list of return type
        If no return, return None
        Alias of return_type
        """
        return self.return_type

    @property
    def returns(self) -> list["LocalVariable"]:
        """
        list(LocalVariable): List of the return variables
        """
        return list(self._returns)

    def add_return(self, r: "LocalVariable") -> None:
        self._returns.append(r)

    @property
    def returns_ssa(self) -> list["LocalIRVariable"]:
        """
        list(LocalIRVariable): List of the return variables (SSA form)
        """
        return list(self._returns_ssa)

    def add_return_ssa(self, var: "LocalIRVariable") -> None:
        self._returns_ssa.append(var)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Modifiers
    ###################################################################################
    ###################################################################################

    @property
    def modifiers(self) -> list[Union["Contract", "Function"]]:
        """
        list(Modifier): List of the modifiers
        Can be contract for constructor's calls

        """
        return [c.modifier for c in self._modifiers]

    def add_modifier(self, modif: "ModifierStatements") -> None:
        self._modifiers.append(modif)

    @property
    def modifiers_statements(self) -> list[ModifierStatements]:
        """
        list(ModifierCall): List of the modifiers call (include expression and irs)
        """
        return list(self._modifiers)

    @property
    def explicit_base_constructor_calls(self) -> list["Function"]:
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
    def explicit_base_constructor_calls_statements(self) -> list[ModifierStatements]:
        """
        list(ModifierCall): List of the base constructors called explicitly by this presumed constructor definition.

        """
        # This is a list of contracts internally, so we convert it to a list of constructor functions.
        return list(self._explicit_base_constructor_calls)

    def add_explicit_base_constructor_calls_statements(self, modif: ModifierStatements) -> None:
        self._explicit_base_constructor_calls.append(modif)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################

    @property
    def variables(self) -> list[LocalVariable]:
        """
        Return all local variables
        Include parameters and return values
        """
        return list(self._variables.values())

    @property
    def local_variables(self) -> list[LocalVariable]:
        """
        Return all local variables (dont include parameters and return values)
        """
        return list(set(self.variables) - set(self.returns) - set(self.parameters))

    @property
    def variables_as_dict(self) -> dict[str, LocalVariable]:
        return self._variables

    @property
    def variables_read(self) -> list["Variable"]:
        """
        list(Variable): Variables read (local/state/solidity)
        """
        return list(self._vars_read)

    @property
    def variables_written(self) -> list["Variable"]:
        """
        list(Variable): Variables written (local/state/solidity)
        """
        return list(self._vars_written)

    @property
    def state_variables_read(self) -> list["StateVariable"]:
        """
        list(StateVariable): State variables read
        """
        return list(self._state_vars_read)

    @property
    def solidity_variables_read(self) -> list["SolidityVariable"]:
        """
        list(SolidityVariable): Solidity variables read
        """
        return list(self._solidity_vars_read)

    @property
    def state_variables_written(self) -> list["StateVariable"]:
        """
        list(StateVariable): State variables written
        """
        return list(self._state_vars_written)

    @property
    def variables_read_or_written(self) -> list["Variable"]:
        """
        list(Variable): Variables read or written (local/state/solidity)
        """
        return list(self._vars_read_or_written)

    @property
    def variables_read_as_expression(self) -> list["Expression"]:
        return self._expression_vars_read

    @property
    def variables_written_as_expression(self) -> list["Expression"]:
        return self._expression_vars_written

    @property
    def slithir_variables(self) -> list["SlithIRVariable"]:
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
    def internal_calls(self) -> list["InternalCall"]:
        """
        list(InternalCall): List of IR operations for internal calls
        """
        return list(self._internal_calls)

    @property
    def solidity_calls(self) -> list["SolidityCall"]:
        """
        list(SolidityCall): List of IR operations for Solidity calls
        """
        return list(self._solidity_calls)

    @property
    def high_level_calls(self) -> list[tuple["Contract", "HighLevelCall"]]:
        """
        list(Tuple(Contract, "HighLevelCall")): List of call target contract and IR of the high level call
        A variable is called in case of call to a public state variable
        Include library calls
        """
        return list(self._high_level_calls)

    @property
    def library_calls(self) -> list["LibraryCall"]:
        """
        list(LibraryCall): List of IR operations for library calls
        """
        return list(self._library_calls)

    @property
    def low_level_calls(self) -> list["LowLevelCall"]:
        """
        list(LowLevelCall): List of IR operations for low level calls
        A low level call is defined by
        - the variable called
        - the name of the function (call/delegatecall/callcode)
        """
        return list(self._low_level_calls)

    @property
    def external_calls_as_expressions(self) -> list["Expression"]:
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
    def calls_as_expressions(self) -> list["Expression"]:
        return self._expression_calls

    @property
    def expressions(self) -> list["Expression"]:
        """
        list(Expression): List of the expressions
        """
        if self._expressions is None:
            expressionss = [n.expression for n in self.nodes]
            expressions = [e for e in expressionss if e]
            self._expressions = expressions
        return self._expressions

    @property
    def return_values(self) -> list["SlithIRVariable"]:
        """
        list(Return Values): List of the return values
        """
        from slither.core.cfg.node import NodeType
        from slither.slithir.operations import Return
        from slither.slithir.variables import Constant

        if self._return_values is None:
            return_values = []
            returns = [n for n in self.nodes if n.type == NodeType.RETURN]
            [
                return_values.extend(ir.values)
                for node in returns
                for ir in node.irs
                if isinstance(ir, Return)
            ]
            self._return_values = list({x for x in return_values if not isinstance(x, Constant)})
        return self._return_values

    @property
    def return_values_ssa(self) -> list["SlithIRVariable"]:
        """
        list(Return Values in SSA form): List of the return values in ssa form
        """
        from slither.core.cfg.node import NodeType
        from slither.slithir.operations import Return
        from slither.slithir.variables import Constant

        if self._return_values_ssa is None:
            return_values_ssa = []
            returns = [n for n in self.nodes if n.type == NodeType.RETURN]
            [
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
    def slithir_operations(self) -> list["Operation"]:
        """
        list(Operation): List of the slithir operations
        """
        if self._slithir_operations is None:
            operationss = [n.irs for n in self.nodes]
            operations = [item for sublist in operationss for item in sublist if item]
            self._slithir_operations = operations
        return self._slithir_operations

    @property
    def slithir_ssa_operations(self) -> list["Operation"]:
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
    def signature(self) -> tuple[str, list[str], list[str]]:
        """
        (str, list(str), list(str)): Function signature as
        (name, list parameters type, list return values type)
        """
        # FIXME memoizing this function is not working properly for vyper
        # if self._signature is None:
        return (
            self.name,
            [str(x.type) for x in self.parameters],
            [str(x.type) for x in self.returns],
        )
        #     self._signature = signature
        # return self._signature

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
    def functions_shadowed(self) -> list["Function"]:
        pass

    # endregion
    ###################################################################################
    ###################################################################################
    # region Reachable
    ###################################################################################
    ###################################################################################

    @property
    def reachable_from_nodes(self) -> set[ReacheableNode]:
        """
        Return
            ReacheableNode
        """
        return self._reachable_from_nodes

    @property
    def reachable_from_functions(self) -> set["Function"]:
        return self._reachable_from_functions

    @property
    def all_reachable_from_functions(self) -> set["Function"]:
        """
        Give the recursive version of reachable_from_functions (all the functions that lead to call self in the CFG)
        """
        if self._all_reachable_from_functions is None:
            functions: set[Function] = set()

            new_functions = self.reachable_from_functions
            # iterate until we have are finding new functions
            while new_functions and not new_functions.issubset(functions):
                functions = functions.union(new_functions)
                # Use a temporary set, because we iterate over new_functions
                new_functionss: set[Function] = set()
                for f in new_functions:
                    new_functionss = new_functionss.union(f.reachable_from_functions)
                new_functions = new_functionss - functions

            self._all_reachable_from_functions = functions
        return self._all_reachable_from_functions

    def add_reachable_from_node(self, n: "Node", ir: "Operation") -> None:
        self._reachable_from_nodes.add(ReacheableNode(n, ir))
        self._reachable_from_functions.add(n.function)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Recursive getters
    ###################################################################################
    ###################################################################################

    def _explore_functions(self, f_new_values: Callable[["Function"], list]) -> list[Any]:
        values = f_new_values(self)
        explored = [self]
        to_explore = [
            ir.function
            for ir in self.internal_calls
            if isinstance(ir.function, Function) and ir.function not in explored
        ]
        to_explore += [
            ir.function
            for ir in self.library_calls
            if isinstance(ir.function, Function) and ir.function not in explored
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
                ir.function
                for ir in f.internal_calls
                if isinstance(ir.function, Function)
                and ir.function not in explored
                and ir.function not in to_explore
            ]
            to_explore += [
                ir.function
                for ir in f.library_calls
                if isinstance(ir.function, Function)
                and ir.function not in explored
                and ir.function not in to_explore
            ]
            to_explore += [m for m in f.modifiers if m not in explored and m not in to_explore]

        return list(set(values))

    def all_variables_read(self) -> list["Variable"]:
        """recursive version of variables_read"""
        if self._all_variables_read is None:
            self._all_variables_read = self._explore_functions(lambda x: x.variables_read)
        return self._all_variables_read

    def all_variables_written(self) -> list["Variable"]:
        """recursive version of variables_written"""
        if self._all_variables_written is None:
            self._all_variables_written = self._explore_functions(lambda x: x.variables_written)
        return self._all_variables_written

    def all_state_variables_read(self) -> list["StateVariable"]:
        """recursive version of variables_read"""
        if self._all_state_variables_read is None:
            self._all_state_variables_read = self._explore_functions(
                lambda x: x.state_variables_read
            )
        return self._all_state_variables_read

    def all_solidity_variables_read(self) -> list[SolidityVariable]:
        """recursive version of solidity_read"""
        if self._all_solidity_variables_read is None:
            self._all_solidity_variables_read = self._explore_functions(
                lambda x: x.solidity_variables_read
            )
        return self._all_solidity_variables_read

    def all_slithir_variables(self) -> list["SlithIRVariable"]:
        """recursive version of slithir_variables"""
        if self._all_slithir_variables is None:
            self._all_slithir_variables = self._explore_functions(lambda x: x.slithir_variables)
        return self._all_slithir_variables

    def all_nodes(self) -> list["Node"]:
        """recursive version of nodes"""
        if self._all_nodes is None:
            self._all_nodes = self._explore_functions(lambda x: x.nodes)
        return self._all_nodes

    def all_expressions(self) -> list["Expression"]:
        """recursive version of variables_read"""
        if self._all_expressions is None:
            self._all_expressions = self._explore_functions(lambda x: x.expressions)
        return self._all_expressions

    def all_slithir_operations(self) -> list["Operation"]:
        if self._all_slithir_operations is None:
            self._all_slithir_operations = self._explore_functions(lambda x: x.slithir_operations)
        return self._all_slithir_operations

    def all_state_variables_written(self) -> list[StateVariable]:
        """recursive version of variables_written"""
        if self._all_state_variables_written is None:
            self._all_state_variables_written = self._explore_functions(
                lambda x: x.state_variables_written
            )
        return self._all_state_variables_written

    def all_internal_calls(self) -> list["InternalCall"]:
        """recursive version of internal_calls"""
        if self._all_internals_calls is None:
            self._all_internals_calls = self._explore_functions(lambda x: x.internal_calls)
        return self._all_internals_calls

    def all_low_level_calls(self) -> list["LowLevelCall"]:
        """recursive version of low_level calls"""
        if self._all_low_level_calls is None:
            self._all_low_level_calls = self._explore_functions(lambda x: x.low_level_calls)
        return self._all_low_level_calls

    def all_high_level_calls(self) -> list[tuple["Contract", "HighLevelCall"]]:
        """recursive version of high_level calls"""
        if self._all_high_level_calls is None:
            self._all_high_level_calls = self._explore_functions(lambda x: x.high_level_calls)
        return self._all_high_level_calls

    def all_library_calls(self) -> list["LibraryCall"]:
        """recursive version of library calls"""
        if self._all_library_calls is None:
            self._all_library_calls = self._explore_functions(lambda x: x.library_calls)
        return self._all_library_calls

    def all_solidity_calls(self) -> list["SolidityCall"]:
        """recursive version of solidity calls"""
        if self._all_solidity_calls is None:
            self._all_solidity_calls = self._explore_functions(lambda x: x.solidity_calls)
        return self._all_solidity_calls

    @staticmethod
    def _explore_func_cond_read(func: "Function", include_loop: bool) -> list["StateVariable"]:
        ret = [n.state_variables_read for n in func.nodes if n.is_conditional(include_loop)]
        return [item for sublist in ret for item in sublist]

    def all_conditional_state_variables_read(self, include_loop=True) -> list["StateVariable"]:
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
    def _solidity_variable_in_binary(node: "Node") -> list[SolidityVariable]:
        from slither.slithir.operations.binary import Binary

        ret = []
        for ir in node.irs:
            if isinstance(ir, Binary):
                ret += ir.read
        return [var for var in ret if isinstance(var, SolidityVariable)]

    @staticmethod
    def _explore_func_conditional(
        func: "Function",
        f: Callable[["Node"], list[SolidityVariable]],
        include_loop: bool,
    ) -> list[Any]:
        ret = [f(n) for n in func.nodes if n.is_conditional(include_loop)]
        return [item for sublist in ret for item in sublist]

    def all_conditional_solidity_variables_read(
        self, include_loop: bool = True
    ) -> list[SolidityVariable]:
        """
        Return the Solidity variables directly used in a condition

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
    def _solidity_variable_in_internal_calls(node: "Node") -> list[SolidityVariable]:
        from slither.slithir.operations.internal_call import InternalCall

        ret = []
        for ir in node.irs:
            if isinstance(ir, InternalCall):
                ret += ir.read
        return [var for var in ret if isinstance(var, SolidityVariable)]

    @staticmethod
    def _explore_func_nodes(
        func: "Function", f: Callable[["Node"], list[SolidityVariable]]
    ) -> list[Any | SolidityVariableComposed]:
        ret = [f(n) for n in func.nodes]
        return [item for sublist in ret for item in sublist]

    def all_solidity_variables_used_as_args(self) -> list[SolidityVariable]:
        """
        Return the Solidity variables directly used in a call

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

    def apply_visitor(self, Visitor: Callable) -> list:
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

    def get_local_variable_from_name(self, variable_name: str) -> LocalVariable | None:
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
                f.write(f'{node.node_id}[label="{node!s}"];\n')
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

    def slithir_cfg_to_dot_str(self, skip_expressions: bool = False) -> str:
        """
        Export the CFG to a DOT format. The nodes includes the Solidity expressions and the IRs
        :return: the DOT content
        :rtype: str
        """
        from slither.core.cfg.node import NodeType

        content = ""
        content += "digraph{\n"
        for node in self.nodes:
            label = f"Node Type: {node.type.value} {node.node_id}\n"
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
    ) -> tuple[str, str, str, list[str], list[str], list[str], list[str], list[str]]:
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

    @property
    def is_reentrant(self) -> bool:
        """
        Determine if the function can be re-entered
        """
        reentrancy_modifier = "nonReentrant"

        if self.function_language == FunctionLanguage.Vyper:
            reentrancy_modifier = "nonreentrant(lock)"

        # TODO: compare with hash of known nonReentrant modifier instead of the name
        if reentrancy_modifier in [m.name for m in self.modifiers]:
            return False

        if self.visibility in ["public", "external"]:
            return True

        # If it's an internal function, check if all its entry points have the nonReentrant modifier
        all_entry_points = [
            f for f in self.all_reachable_from_functions if f.visibility in ["public", "external"]
        ]
        if not all_entry_points:
            return True
        return not all(
            reentrancy_modifier in [m.name for m in f.modifiers] for f in all_entry_points
        )

    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyses
    ###################################################################################
    ###################################################################################

    def _analyze_read_write(self) -> None:
        """Compute variables read/written/..."""
        write_var = [x.variables_written_as_expression for x in self.nodes]
        write_var = [x for x in write_var if x]
        write_var = [item for sublist in write_var for item in sublist]
        write_var = list(set(write_var))
        # Remove duplicate if they share the same string representation
        write_var = [
            next(obj)
            for i, obj in groupby(sorted(write_var, key=lambda x: str(x)), lambda x: str(x))
        ]
        self._expression_vars_written = write_var

        write_var = [x.variables_written for x in self.nodes]
        write_var = [x for x in write_var if x]
        write_var = [item for sublist in write_var for item in sublist]
        write_var = list(set(write_var))
        # Remove duplicate if they share the same string representation
        write_var = [
            next(obj)
            for i, obj in groupby(sorted(write_var, key=lambda x: str(x)), lambda x: str(x))
        ]
        self._vars_written = write_var

        read_var = [x.variables_read_as_expression for x in self.nodes]
        read_var = [x for x in read_var if x]
        read_var = [item for sublist in read_var for item in sublist]
        # Remove duplicate if they share the same string representation
        read_var = [
            next(obj)
            for i, obj in groupby(sorted(read_var, key=lambda x: str(x)), lambda x: str(x))
        ]
        self._expression_vars_read = read_var

        read_var = [x.variables_read for x in self.nodes]
        read_var = [x for x in read_var if x]
        read_var = [item for sublist in read_var for item in sublist]
        # Remove duplicate if they share the same string representation
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

    def _analyze_calls(self) -> None:
        calls = [x.calls_as_expression for x in self.nodes]
        calls = [x for x in calls if x]
        calls = [item for sublist in calls for item in sublist]
        self._expression_calls = list(set(calls))

        internal_calls = [x.internal_calls for x in self.nodes]
        internal_calls = [x for x in internal_calls if x]
        internal_calls = [item for sublist in internal_calls for item in sublist]
        self._internal_calls = list(set(internal_calls))

        self._solidity_calls = [
            ir for ir in internal_calls if isinstance(ir.function, SolidityFunction)
        ]

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
        self, node_type: "NodeType", src: str | dict, scope: Union[Scope, "Function"]
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
    ) -> dict[str, set["SlithIRVariable"]]:
        from slither.slithir.variables import ReferenceVariable
        from slither.slithir.operations import OperationWithLValue
        from slither.core.cfg.node import NodeType

        if not self.is_implemented:
            return {}

        if self._entry_point is None:
            return {}
        # node, values
        to_explore: list[tuple[Node, dict]] = [(self._entry_point, {})]
        # node -> values
        explored: dict = {}
        # name -> instances
        ret: dict = {}

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
    ) -> dict[str, set["SlithIRVariable"]]:
        return self._get_last_ssa_variable_instances(target_state=True, target_local=False)

    def get_last_ssa_local_variables_instances(
        self,
    ) -> dict[str, set["SlithIRVariable"]]:
        return self._get_last_ssa_variable_instances(target_state=False, target_local=True)

    @staticmethod
    def _unchange_phi(ir: "Operation") -> bool:
        from slither.slithir.operations import Phi, PhiCallback

        if not isinstance(ir, (Phi, PhiCallback)) or len(ir.rvalues) > 1:
            return False
        if not ir.rvalues:
            return True
        return ir.rvalues[0] == ir.lvalue

    def _fix_phi_entry(
        self,
        node: "Node",
        last_state_variables_instances: dict[str, list["StateVariable"]],
        initial_state_variables_instances: dict[str, "StateVariable"],
    ) -> None:
        from slither.slithir.variables import Constant, StateIRVariable, LocalIRVariable

        for ir in node.irs_ssa:
            if isinstance(ir.lvalue, StateIRVariable):
                additional = [initial_state_variables_instances[ir.lvalue.canonical_name]]
                additional += last_state_variables_instances[ir.lvalue.canonical_name]
                ir.rvalues = list(set(additional + ir.rvalues))
            # function parameter that are storage pointer
            else:
                # find index of the parameter
                idx = self.parameters.index(ir.lvalue.non_ssa_version)
                # find non ssa version of that index
                additional = [n.ir.arguments[idx] for n in self.reachable_from_nodes]
                additional = unroll(additional)
                additional = [a for a in additional if not isinstance(a, Constant)]
                ir.rvalues = list(set(additional + ir.rvalues))

                if isinstance(ir.lvalue, LocalIRVariable) and ir.lvalue.is_storage:
                    # Update the refers_to to point to the phi rvalues
                    # This basically means that the local variable is a storage that point to any
                    # state variable that the storage pointer alias analysis found
                    ir.lvalue.refers_to = [
                        rvalue for rvalue in ir.rvalues if isinstance(rvalue, StateIRVariable)
                    ]

    def fix_phi(
        self,
        last_state_variables_instances: dict[str, list["StateVariable"]],
        initial_state_variables_instances: dict[str, "StateVariable"],
    ) -> None:
        from slither.slithir.operations import InternalCall, PhiCallback, Phi
        from slither.slithir.variables import StateIRVariable, LocalIRVariable

        for node in self.nodes:
            if node == self.entry_point:
                self._fix_phi_entry(
                    node, last_state_variables_instances, initial_state_variables_instances
                )
            for ir in node.irs_ssa:
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

                # Propage storage ref information if it does not exist
                # This can happen if the refers_to variable was discovered through the phi operator on function parameter
                # aka you have storage pointer as function parameter
                # instead of having a storage pointer for which the aliases belong to the function body
                if (
                    isinstance(ir, Phi)
                    and isinstance(ir.lvalue, LocalIRVariable)
                    and ir.lvalue.is_storage
                    and not ir.lvalue.refers_to
                ):
                    refers_to = []
                    for candidate in ir.rvalues:
                        if isinstance(candidate, StateIRVariable):
                            refers_to.append(candidate)
                        if isinstance(candidate, LocalIRVariable) and candidate.is_storage:
                            refers_to += candidate.refers_to

                    ir.lvalue.refers_to = refers_to

            node.irs_ssa = [ir for ir in node.irs_ssa if not self._unchange_phi(ir)]

    def generate_slithir_and_analyze(self) -> None:
        for node in self.nodes:
            node.slithir_generation()

        self._analyze_read_write()
        self._analyze_calls()

    @abstractmethod
    def generate_slithir_ssa(self, all_ssa_state_variables_instances):
        pass

    def update_read_write_using_ssa(self) -> None:
        for node in self.nodes:
            node.update_read_write_using_ssa()
        self._analyze_read_write()

    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __str__(self) -> str:
        return self.name

    # endregion
