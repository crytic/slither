"""
Node module
"""

from enum import Enum
from typing import Optional, Union, TYPE_CHECKING

from slither.all_exceptions import SlitherException
from slither.core.declarations import Contract, Function, FunctionContract
from slither.core.declarations.solidity_variables import (
    SolidityVariable,
    SolidityFunction,
)
from slither.core.expressions.expression import Expression
from slither.core.solidity_types import ElementaryType
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.slithir.convert import convert_expression
from slither.slithir.operations import (
    HighLevelCall,
    Index,
    InternalCall,
    Length,
    LibraryCall,
    LowLevelCall,
    Member,
    OperationWithLValue,
    Phi,
    PhiCallback,
    SolidityCall,
    Return,
    Operation,
)
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables import (
    Constant,
    LocalIRVariable,
    ReferenceVariable,
    StateIRVariable,
    TemporaryVariable,
    TupleVariable,
)

if TYPE_CHECKING:
    from slither.slithir.variables.variable import SlithIRVariable
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.core.cfg.scope import Scope
    from slither.core.scope.scope import FileScope


###################################################################################
###################################################################################
# region NodeType
###################################################################################
###################################################################################


class NodeType(Enum):
    ENTRYPOINT = "ENTRY_POINT"  # no expression

    # Nodes that may have an expression

    EXPRESSION = "EXPRESSION"  # normal case
    RETURN = "RETURN"  # RETURN may contain an expression
    IF = "IF"
    VARIABLE = "NEW VARIABLE"  # Variable declaration
    ASSEMBLY = "INLINE ASM"
    ENDASSEMBLY = "END INLINE ASM"
    IFLOOP = "IF_LOOP"

    # Nodes where control flow merges
    # Can have phi IR operation
    ENDIF = "END_IF"  # ENDIF node source mapping points to the if/else "body"
    STARTLOOP = "BEGIN_LOOP"  # STARTLOOP node source mapping points to the entire loop "body"
    ENDLOOP = "END_LOOP"  # ENDLOOP node source mapping points to the entire loop "body"

    # Below the nodes do not have an expression but are used to expression CFG structure.

    # Absorbing node
    THROW = "THROW"

    # Loop related nodes
    BREAK = "BREAK"
    CONTINUE = "CONTINUE"

    # Only modifier node
    PLACEHOLDER = "_"

    TRY = "TRY"
    CATCH = "CATCH"

    # Node not related to the CFG
    # Use for state variable declaration
    OTHER_ENTRYPOINT = "OTHER_ENTRYPOINT"


# endregion


class Node(SourceMapping):
    """
    Node class

    """

    def __init__(
        self,
        node_type: NodeType,
        node_id: int,
        scope: Union["Scope", "Function"],
        file_scope: "FileScope",
    ) -> None:
        super().__init__()
        self._node_type = node_type

        # TODO: rename to explicit CFG
        self._sons: list[Node] = []
        self._fathers: list[Node] = []

        ## Dominators info
        # Dominators nodes
        self._dominators: set[Node] = set()
        self._immediate_dominator: Node | None = None
        ## Nodes of the dominators tree
        # self._dom_predecessors = set()
        self._dom_successors: set[Node] = set()
        # Dominance frontier
        self._dominance_frontier: set[Node] = set()
        # Phi origin
        # key are variable name
        self._phi_origins_state_variables: dict[str, tuple[StateVariable, set[Node]]] = {}
        self._phi_origins_local_variables: dict[str, tuple[LocalVariable, set[Node]]] = {}
        # self._phi_origins_member_variables: Dict[str, Tuple[MemberVariable, Set["Node"]]] = {}

        self._expression: Expression | None = None
        self._variable_declaration: LocalVariable | None = None
        self._node_id: int = node_id

        self._vars_written: list[Variable] = []
        self._vars_read: list[Variable | SolidityVariable] = []

        self._ssa_vars_written: list[SlithIRVariable] = []
        self._ssa_vars_read: list[SlithIRVariable] = []

        self._internal_calls: list[InternalCall] = []  # contains solidity calls
        self._solidity_calls: list[SolidityCall] = []
        self._high_level_calls: list[tuple[Contract, HighLevelCall]] = []  # contains library calls
        self._library_calls: list[LibraryCall] = []
        self._low_level_calls: list[LowLevelCall] = []
        self._external_calls_as_expressions: list[Expression] = []
        self._internal_calls_as_expressions: list[Expression] = []
        self._irs: list[Operation] = []
        self._all_slithir_operations: list[Operation] | None = None
        self._irs_ssa: list[Operation] = []

        self._state_vars_written: list[StateVariable] = []
        self._state_vars_read: list[StateVariable] = []
        self._solidity_vars_read: list[SolidityVariable] = []

        self._ssa_state_vars_written: list[StateIRVariable] = []
        self._ssa_state_vars_read: list[StateIRVariable] = []

        self._local_vars_read: list[LocalVariable] = []
        self._local_vars_written: list[LocalVariable] = []

        self._slithir_vars: set[
            SlithIRVariable | ReferenceVariable | TemporaryVariable | TupleVariable
        ] = set()  # non SSA

        self._ssa_local_vars_read: list[LocalIRVariable] = []
        self._ssa_local_vars_written: list[LocalIRVariable] = []

        self._expression_vars_written: list[Expression] = []
        self._expression_vars_read: list[Expression] = []
        self._expression_calls: list[Expression] = []

        # Computed on the fly, can be True of False
        self._can_reenter: bool | None = None
        self._can_send_eth: bool | None = None

        self._asm_source_code: str | dict | None = None

        self.scope: Scope | Function = scope
        self.file_scope: FileScope = file_scope
        self._function: Function | None = None

        self._is_reachable: bool = False

    ###################################################################################
    ###################################################################################
    # region General's properties
    ###################################################################################
    ###################################################################################

    @property
    def compilation_unit(self) -> "SlitherCompilationUnit":
        return self.function.compilation_unit

    @property
    def node_id(self) -> int:
        """Unique node id."""
        return self._node_id

    @property
    def type(self) -> NodeType:
        """
        NodeType: type of the node
        """
        return self._node_type

    @type.setter
    def type(self, new_type: NodeType) -> None:
        self._node_type = new_type

    @property
    def will_return(self) -> bool:
        if not self.sons and self.type != NodeType.THROW:
            solidity_calls = [ir.function for ir in self.solidity_calls]
            if SolidityFunction("revert()") not in solidity_calls:
                if SolidityFunction("revert(string)") not in solidity_calls:
                    return True
        return False

    def set_function(self, function: "Function") -> None:
        self._function = function

    @property
    def function(self) -> "Function":
        return self._function

    @property
    def is_reachable(self) -> bool:
        return self._is_reachable

    def set_is_reachable(self, new_is_reachable: bool) -> None:
        self._is_reachable = new_is_reachable

    # endregion
    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################

    @property
    def variables_read(self) -> list[Variable | SolidityVariable]:
        """
        list(Variable): Variables read (local/state/solidity)
        """
        return list(self._vars_read)

    @property
    def state_variables_read(self) -> list[StateVariable]:
        """
        list(StateVariable): State variables read
        """
        return list(self._state_vars_read)

    @property
    def local_variables_read(self) -> list[LocalVariable]:
        """
        list(LocalVariable): Local variables read
        """
        return list(self._local_vars_read)

    @property
    def solidity_variables_read(self) -> list[SolidityVariable]:
        """
        list(SolidityVariable): State variables read
        """
        return list(self._solidity_vars_read)

    @property
    def ssa_variables_read(self) -> list["SlithIRVariable"]:
        """
        list(Variable): Variables read (local/state/solidity)
        """
        return list(self._ssa_vars_read)

    @property
    def ssa_state_variables_read(self) -> list[StateIRVariable]:
        """
        list(StateVariable): State variables read
        """
        return list(self._ssa_state_vars_read)

    @property
    def ssa_local_variables_read(self) -> list[LocalIRVariable]:
        """
        list(LocalVariable): Local variables read
        """
        return list(self._ssa_local_vars_read)

    @property
    def variables_read_as_expression(self) -> list[Expression]:
        return self._expression_vars_read

    @variables_read_as_expression.setter
    def variables_read_as_expression(self, exprs: list[Expression]) -> None:
        self._expression_vars_read = exprs

    @property
    def slithir_variables(
        self,
    ) -> list[Union["SlithIRVariable", ReferenceVariable, TemporaryVariable, TupleVariable]]:
        return list(self._slithir_vars)

    @property
    def variables_written(self) -> list[Variable]:
        """
        list(Variable): Variables written (local/state/solidity)
        """
        return list(self._vars_written)

    @property
    def state_variables_written(self) -> list[StateVariable]:
        """
        list(StateVariable): State variables written
        """
        return list(self._state_vars_written)

    @property
    def local_variables_written(self) -> list[LocalVariable]:
        """
        list(LocalVariable): Local variables written
        """
        return list(self._local_vars_written)

    @property
    def ssa_variables_written(self) -> list["SlithIRVariable"]:
        """
        list(Variable): Variables written (local/state/solidity)
        """
        return list(self._ssa_vars_written)

    @property
    def ssa_state_variables_written(self) -> list[StateIRVariable]:
        """
        list(StateVariable): State variables written
        """
        return list(self._ssa_state_vars_written)

    @property
    def ssa_local_variables_written(self) -> list[LocalIRVariable]:
        """
        list(LocalVariable): Local variables written
        """
        return list(self._ssa_local_vars_written)

    @property
    def variables_written_as_expression(self) -> list[Expression]:
        return self._expression_vars_written

    @variables_written_as_expression.setter
    def variables_written_as_expression(self, exprs: list[Expression]) -> None:
        self._expression_vars_written = exprs

    # endregion
    ###################################################################################
    ###################################################################################
    # region Calls
    ###################################################################################
    ###################################################################################

    @property
    def internal_calls(self) -> list[InternalCall]:
        """
        list(InternalCall): List of IR operations with internal/solidity function calls
        """
        return list(self._internal_calls)

    @property
    def solidity_calls(self) -> list[SolidityCall]:
        """
        list(SolidityCall): List of IR operations with solidity calls
        """
        return list(self._solidity_calls)

    @property
    def high_level_calls(self) -> list[HighLevelCall]:
        """
        list(HighLevelCall): List of IR operations with high level calls (external calls).
        Include library calls
        """
        return list(self._high_level_calls)

    @property
    def library_calls(self) -> list[LibraryCall]:
        """
        list(LibraryCall): List of IR operations with library calls.
        """
        return list(self._library_calls)

    @property
    def low_level_calls(self) -> list[LowLevelCall]:
        """
        list(LowLevelCall): List of IR operations with low_level call
        """
        return list(self._low_level_calls)

    @property
    def external_calls_as_expressions(self) -> list[Expression]:
        """
        list(CallExpression): List of message calls (that creates a transaction)
        """
        return self._external_calls_as_expressions

    @external_calls_as_expressions.setter
    def external_calls_as_expressions(self, exprs: list[Expression]) -> None:
        self._external_calls_as_expressions = exprs

    @property
    def internal_calls_as_expressions(self) -> list[Expression]:
        """
        list(CallExpression): List of internal calls (that dont create a transaction)
        """
        return self._internal_calls_as_expressions

    @internal_calls_as_expressions.setter
    def internal_calls_as_expressions(self, exprs: list[Expression]) -> None:
        self._internal_calls_as_expressions = exprs

    @property
    def calls_as_expression(self) -> list[Expression]:
        return list(self._expression_calls)

    @calls_as_expression.setter
    def calls_as_expression(self, exprs: list[Expression]) -> None:
        self._expression_calls = exprs

    def can_reenter(self, callstack: list[Function | Variable] | None = None) -> bool:
        """
        Check if the node can re-enter
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
            for ir in self.irs:
                if isinstance(ir, Call) and ir.can_reenter(callstack):
                    self._can_reenter = True
                    return True
        return self._can_reenter

    def can_send_eth(self) -> bool:
        """
        Check if the node can send eth
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

    # endregion
    ###################################################################################
    ###################################################################################
    # region Expressions
    ###################################################################################
    ###################################################################################

    @property
    def expression(self) -> Expression | None:
        """
        Expression: Expression of the node
        """
        return self._expression

    def add_expression(self, expression: Expression, bypass_verif_empty: bool = False) -> None:
        assert self._expression is None or bypass_verif_empty
        self._expression = expression

    def add_variable_declaration(self, var: LocalVariable) -> None:
        assert self._variable_declaration is None
        self._variable_declaration = var
        if var.expression:
            self._vars_written += [var]
            self._local_vars_written += [var]

    @property
    def variable_declaration(self) -> LocalVariable | None:
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

    def contains_require_or_assert(self) -> bool:
        """
            Check if the node has a require or assert call
        Returns:
            bool: True if the node has a require or assert call
        """
        return any(
            ir.function.name
            in ["require(bool)", "require(bool,string)", "require(bool,error)", "assert(bool)"]
            for ir in self.internal_calls
        )

    def contains_if(self, include_loop: bool = True) -> bool:
        """
            Check if the node is a IF node
        Returns:
            bool: True if the node is a conditional node (IF or IFLOOP)
        """
        if include_loop:
            return self.type in [NodeType.IF, NodeType.IFLOOP]
        return self.type == NodeType.IF

    def is_conditional(self, include_loop: bool = True) -> bool:
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
                        if r.type == ElementaryType("bool"):
                            return True
        return False

    # endregion
    ###################################################################################
    ###################################################################################
    # region EVM
    ###################################################################################
    ###################################################################################

    @property
    def inline_asm(self) -> str | dict | None:
        return self._asm_source_code

    def add_inline_asm(self, asm: str | dict) -> None:
        self._asm_source_code = asm

    # endregion
    ###################################################################################
    ###################################################################################
    # region Graph
    ###################################################################################
    ###################################################################################

    def add_father(self, father: "Node") -> None:
        """Add a father node

        Args:
            father: father to add
        """
        self._fathers.append(father)

    def set_fathers(self, fathers: list["Node"]) -> None:
        """Set the father nodes

        Args:
            fathers: list of fathers to add
        """
        self._fathers = fathers

    @property
    def fathers(self) -> list["Node"]:
        """Returns the father nodes

        Returns:
            list(Node): list of fathers
        """
        return list(self._fathers)

    def remove_father(self, father: "Node") -> None:
        """Remove the father node. Do nothing if the node is not a father

        Args:
            :param father:
        """
        self._fathers = [x for x in self._fathers if x.node_id != father.node_id]

    def remove_son(self, son: "Node") -> None:
        """Remove the son node. Do nothing if the node is not a son

        Args:
            :param son:
        """
        self._sons = [x for x in self._sons if x.node_id != son.node_id]

    def add_son(self, son: "Node") -> None:
        """Add a son node

        Args:
            son: son to add
        """
        self._sons.append(son)

    def replace_son(self, ori_son: "Node", new_son: "Node") -> None:
        """Replace a son node. Do nothing if the node to replace is not a son

        Args:
            ori_son: son to replace
            new_son: son to replace with
        """
        for i, s in enumerate(self._sons):
            if s.node_id == ori_son.node_id:
                idx = i
                break
        else:
            return
        self._sons[idx] = new_son

    def set_sons(self, sons: list["Node"]) -> None:
        """Set the son nodes

        Args:
            sons: list of fathers to add
        """
        self._sons = sons

    @property
    def sons(self) -> list["Node"]:
        """Returns the son nodes

        Returns:
            list(Node): list of sons
        """
        return list(self._sons)

    @property
    def son_true(self) -> Optional["Node"]:
        if self.type in [NodeType.IF, NodeType.IFLOOP]:
            return self._sons[0]
        return None

    @property
    def son_false(self) -> Optional["Node"]:
        if self.type in [NodeType.IF, NodeType.IFLOOP] and len(self._sons) >= 1:
            return self._sons[1]
        return None

    # endregion
    ###################################################################################
    ###################################################################################
    # region SlithIR
    ###################################################################################
    ###################################################################################

    @property
    def irs(self) -> list[Operation]:
        """Returns the slithIR representation

        return
            list(slithIR.Operation)
        """
        return self._irs

    @property
    def irs_ssa(self) -> list[Operation]:
        """Returns the slithIR representation with SSA

        return
            list(slithIR.Operation)
        """
        return self._irs_ssa

    @irs_ssa.setter
    def irs_ssa(self, irs: list[Operation]) -> None:
        self._irs_ssa = irs

    def add_ssa_ir(self, ir: Operation) -> None:
        """
        Use to place phi operation
        """
        ir.set_node(self)  # type: ignore
        self._irs_ssa.append(ir)

    def slithir_generation(self) -> None:
        if self.expression:
            expression = self.expression
            self._irs = convert_expression(expression, self)  # type:ignore

        self._find_read_write_call()

    def all_slithir_operations(self) -> list[Operation]:
        if self._all_slithir_operations is None:
            irs = list(self.irs)
            for ir in self.irs:
                if isinstance(ir, InternalCall):
                    irs += ir.function.all_slithir_operations()
            self._all_slithir_operations = irs
        return self._all_slithir_operations

    @staticmethod
    def _is_non_slithir_var(var: Variable) -> bool:
        return not isinstance(var, (Constant, ReferenceVariable, TemporaryVariable, TupleVariable))

    @staticmethod
    def _is_valid_slithir_var(var: Variable) -> bool:
        return isinstance(var, (ReferenceVariable, TemporaryVariable, TupleVariable))

    # endregion
    ###################################################################################
    ###################################################################################
    # region Dominators
    ###################################################################################
    ###################################################################################

    @property
    def dominators(self) -> set["Node"]:
        """
        Returns:
            set(Node)
        """
        return self._dominators

    @dominators.setter
    def dominators(self, dom: set["Node"]) -> None:
        self._dominators = dom

    @property
    def immediate_dominator(self) -> Optional["Node"]:
        """
        Returns:
            Node or None
        """
        return self._immediate_dominator

    @immediate_dominator.setter
    def immediate_dominator(self, idom: "Node") -> None:
        self._immediate_dominator = idom

    @property
    def dominance_frontier(self) -> set["Node"]:
        """
        Returns:
            set(Node)
        """
        return self._dominance_frontier

    @dominance_frontier.setter
    def dominance_frontier(self, doms: set["Node"]) -> None:
        """
        Returns:
            set(Node)
        """
        self._dominance_frontier = doms

    @property
    def dominator_successors(self) -> set["Node"]:
        return self._dom_successors

    @property
    def dominance_exploration_ordered(self) -> list["Node"]:
        """
        Sorted list of all the nodes to explore to follow the dom
        :return: list(nodes)
        """
        # Explore direct dominance
        to_explore = sorted(self.dominator_successors, key=lambda x: x.node_id)

        # Explore dominance frontier
        # The frontier is the limit where this node dominates
        # We need to explore it because the sub of the direct dominance
        # Might not be dominator of their own sub
        to_explore += sorted(self.dominance_frontier, key=lambda x: x.node_id)
        return to_explore

    # endregion
    ###################################################################################
    ###################################################################################
    # region Phi operation
    ###################################################################################
    ###################################################################################

    @property
    def phi_origins_local_variables(
        self,
    ) -> dict[str, tuple[LocalVariable, set["Node"]]]:
        return self._phi_origins_local_variables

    @property
    def phi_origins_state_variables(
        self,
    ) -> dict[str, tuple[StateVariable, set["Node"]]]:
        return self._phi_origins_state_variables

    # @property
    # def phi_origin_member_variables(self) -> Dict[str, Tuple[MemberVariable, Set["Node"]]]:
    #     return self._phi_origins_member_variables

    def add_phi_origin_local_variable(self, variable: LocalVariable, node: "Node") -> None:
        if variable.name not in self._phi_origins_local_variables:
            assert variable.name
            self._phi_origins_local_variables[variable.name] = (variable, set())
        (v, nodes) = self._phi_origins_local_variables[variable.name]
        assert v == variable
        nodes.add(node)

    def add_phi_origin_state_variable(self, variable: StateVariable, node: "Node") -> None:
        if variable.canonical_name not in self._phi_origins_state_variables:
            self._phi_origins_state_variables[variable.canonical_name] = (
                variable,
                set(),
            )
        (v, nodes) = self._phi_origins_state_variables[variable.canonical_name]
        assert v == variable
        nodes.add(node)

    # def add_phi_origin_member_variable(self, variable: MemberVariable, node: "Node"):
    #     if variable.name not in self._phi_origins_member_variables:
    #         self._phi_origins_member_variables[variable.name] = (variable, set())
    #     (v, nodes) = self._phi_origins_member_variables[variable.name]
    #     assert v == variable
    #     nodes.add(node)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyses
    ###################################################################################
    ###################################################################################

    def _find_read_write_call(self) -> None:
        for ir in self.irs:
            self._slithir_vars |= {v for v in ir.read if self._is_valid_slithir_var(v)}

            if isinstance(ir, OperationWithLValue):
                var = ir.lvalue
                if var and self._is_valid_slithir_var(var):
                    # The type is checked by is_valid_slithir_var
                    self._slithir_vars.add(var)  # type: ignore

            if not isinstance(ir, (Phi, Index, Member)):
                self._vars_read += [v for v in ir.read if self._is_non_slithir_var(v)]
                for var in ir.read:
                    if isinstance(var, ReferenceVariable):
                        self._vars_read.append(var.points_to_origin)
            elif isinstance(ir, (Member, Index)):
                # TODO investigate types for member variable left
                var = ir.variable_left if isinstance(ir, Member) else ir.variable_right
                if var and self._is_non_slithir_var(var):
                    self._vars_read.append(var)
                if isinstance(var, ReferenceVariable):
                    origin = var.points_to_origin
                    if self._is_non_slithir_var(origin):
                        self._vars_read.append(origin)

            if isinstance(ir, OperationWithLValue):
                if isinstance(ir, (Index, Member, Length)):
                    continue  # Don't consider Member and Index operations -> ReferenceVariable
                var = ir.lvalue
                if isinstance(var, ReferenceVariable):
                    var = var.points_to_origin
                if var and self._is_non_slithir_var(var):
                    self._vars_written.append(var)

            if isinstance(ir, InternalCall):
                self._internal_calls.append(ir)
            if isinstance(ir, SolidityCall):
                # TODO: consider removing dependency of solidity_call to internal_call
                self._solidity_calls.append(ir)
                self._internal_calls.append(ir)
            if isinstance(ir, LowLevelCall):
                assert isinstance(ir.destination, (Variable, SolidityVariable))
                self._low_level_calls.append(ir)
            elif isinstance(ir, HighLevelCall) and not isinstance(ir, LibraryCall):
                # Todo investigate this if condition
                # It does seem right to compare against a contract
                # This might need a refactoring
                if isinstance(ir.destination.type, Contract):
                    self._high_level_calls.append((ir.destination.type, ir))
                elif ir.destination == SolidityVariable("this"):
                    func = self.function
                    # Can't use this in a top level function
                    assert isinstance(func, FunctionContract)
                    self._high_level_calls.append((func.contract, ir))
                else:
                    try:
                        # Todo this part needs more tests and documentation
                        self._high_level_calls.append((ir.destination.type.type, ir))
                    except AttributeError as error:
                        raise SlitherException(
                            f"Function not found on IR: {ir}.\nNode: {self} ({self.source_mapping})\nFunction: {self.function}\nPlease try compiling with a recent Solidity version. {error}"
                        )
            elif isinstance(ir, LibraryCall):
                assert isinstance(ir.destination, Contract)
                assert isinstance(ir.function, Function)
                self._high_level_calls.append((ir.destination, ir))
                self._library_calls.append(ir)

        self._vars_read = list(set(self._vars_read))
        self._state_vars_read = [v for v in self._vars_read if isinstance(v, StateVariable)]
        self._local_vars_read = [v for v in self._vars_read if isinstance(v, LocalVariable)]
        self._solidity_vars_read = [
            v_ for v_ in self._vars_read if isinstance(v_, SolidityVariable)
        ]
        self._vars_written = list(set(self._vars_written))
        self._state_vars_written = [v for v in self._vars_written if isinstance(v, StateVariable)]
        self._local_vars_written = [v for v in self._vars_written if isinstance(v, LocalVariable)]
        self._internal_calls = list(set(self._internal_calls))
        self._solidity_calls = list(set(self._solidity_calls))
        self._high_level_calls = list(set(self._high_level_calls))
        self._library_calls = list(set(self._library_calls))
        self._low_level_calls = list(set(self._low_level_calls))

    @staticmethod
    def _convert_ssa(v: Variable) -> StateVariable | LocalVariable | None:
        non_ssa_var: StateVariable | LocalVariable | None
        if isinstance(v, StateIRVariable):
            contract = v.contract
            assert v.name
            non_ssa_var = contract.get_state_variable_from_name(v.name)
            return non_ssa_var
        assert isinstance(v, LocalIRVariable)
        function = v.function
        assert v.name
        non_ssa_var = function.get_local_variable_from_name(v.name)
        return non_ssa_var

    def _update_read_using_ssa(self, ir: Operation) -> None:
        """
        Update self._ssa_vars_read
        This look for all operations that read a IRvariable
        It uses the result of the storage pointer
        - For "normal" operation, the read are mostly everything in ir.read
        - For "index", the read is the left part (the right part being a reference variable)
        - For Phi, nothing is considered read

        """

        # For variable read, phi and index have special treatments
        # Phi don't lead to values read
        # Index leads to read the variable right (the left variable is a ref variable, not the actual object)
        # Not that Member is a normal operation here, given we filter out constant by checking for the IRvaraible
        if not isinstance(ir, (Phi, Index)):
            self._ssa_vars_read += [
                v for v in ir.read if isinstance(v, (StateIRVariable, LocalIRVariable))
            ]
            for var in ir.read:
                if isinstance(var, ReferenceVariable):
                    origin = var.points_to_origin
                    if isinstance(origin, (StateIRVariable, LocalIRVariable)):
                        self._ssa_vars_read.append(origin)

                # If we read from a storage variable (outside of phi operator)
                if isinstance(var, LocalIRVariable) and var.is_storage:
                    for refer_to in var.refers_to:
                        # the following should always be true
                        if isinstance(refer_to, (StateIRVariable, LocalIRVariable)):
                            self._ssa_vars_read.append(refer_to)

        elif isinstance(ir, Index):
            variable_right: RVALUE = ir.variable_right
            if isinstance(variable_right, (StateIRVariable, LocalIRVariable)):
                self._ssa_vars_read.append(variable_right)

            if isinstance(variable_right, ReferenceVariable):
                origin = variable_right.points_to_origin
                if isinstance(origin, (StateIRVariable, LocalIRVariable)):
                    self._ssa_vars_read.append(origin)

    def _update_write_using_ssa(self, ir: Operation) -> None:
        """
        Update self._ssa_vars_written
        This look for all operations that write a IRvariable
        It uses the result of the storage pointer

        Index/member/Length are not considering writing to anything
        For index/member it is implictely handled when their associated RefernceVarible are written

        """

        if isinstance(ir, OperationWithLValue) and not isinstance(ir, Phi):
            if isinstance(ir, (Index, Member, Length)):
                return  # Don't consider Member and Index operations -> ReferenceVariable

            var = ir.lvalue

            if isinstance(var, ReferenceVariable):
                var = var.points_to_origin

            candidates = [var]

            # If we write to a storage pointer, add everything it points to as target
            # if it's a variable declaration we do not want to consider the right variable written in that case
            # string storage ss = s; // s is a storage variable but should not be considered written at that point
            if (
                isinstance(var, LocalIRVariable)
                and var.is_storage
                and ir.node.type is not NodeType.VARIABLE
            ):
                candidates += var.refers_to

            for var in candidates:
                # Only store non-slithIR variables
                if var and isinstance(var, (StateIRVariable, LocalIRVariable)):
                    if isinstance(ir, PhiCallback):
                        continue
                    self._ssa_vars_written.append(var)

    def update_read_write_using_ssa(self) -> None:
        for ir in self.irs_ssa:
            if isinstance(ir, PhiCallback):
                continue

            self._update_read_using_ssa(ir)
            self._update_write_using_ssa(ir)

        self._ssa_vars_read = list(set(self._ssa_vars_read))
        self._ssa_state_vars_read = [v for v in self._ssa_vars_read if isinstance(v, StateVariable)]
        self._ssa_local_vars_read = [v for v in self._ssa_vars_read if isinstance(v, LocalVariable)]
        self._ssa_vars_written = list(set(self._ssa_vars_written))
        self._ssa_state_vars_written = [
            v for v in self._ssa_vars_written if v and isinstance(v, StateIRVariable)
        ]
        self._ssa_local_vars_written = [
            v for v in self._ssa_vars_written if v and isinstance(v, LocalIRVariable)
        ]

        vars_read = [self._convert_ssa(x) for x in self._ssa_vars_read]
        vars_written = [self._convert_ssa(x) for x in self._ssa_vars_written]

        self._vars_read += [v_ for v_ in vars_read if v_ and v_ not in self._vars_read]
        self._state_vars_read = [v for v in self._vars_read if isinstance(v, StateVariable)]
        self._local_vars_read = [v for v in self._vars_read if isinstance(v, LocalVariable)]

        self._vars_written += [v_ for v_ in vars_written if v_ and v_ not in self._vars_written]
        self._state_vars_written = [v for v in self._vars_written if isinstance(v, StateVariable)]
        self._local_vars_written = [v for v in self._vars_written if isinstance(v, LocalVariable)]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __str__(self) -> str:
        additional_info = ""
        if self.expression:
            additional_info += " " + str(self.expression)
        elif self.variable_declaration:
            additional_info += " " + str(self.variable_declaration)
        txt = str(self._node_type.value) + additional_info
        return txt


# endregion
###################################################################################
###################################################################################
# region Utils
###################################################################################
###################################################################################


def link_nodes(node1: Node, node2: Node) -> None:
    node1.add_son(node2)
    node2.add_father(node1)


def insert_node(origin: Node, node_inserted: Node) -> None:
    sons = origin.sons
    link_nodes(origin, node_inserted)
    for son in sons:
        son.remove_father(origin)
        origin.remove_son(son)

        link_nodes(node_inserted, son)


def recheable(node: Node) -> set[Node]:
    """
    Return the set of nodes reacheable from the node
    :param node:
    :return: set(Node)
    """
    nodes = node.sons
    visited = set()
    while nodes:
        next_node = nodes[0]
        nodes = nodes[1:]
        if next_node not in visited:
            visited.add(next_node)
            for son in next_node.sons:
                if son not in visited:
                    nodes.append(son)
    return visited


# endregion
