"""
    Node module
"""
from enum import Enum
from typing import Optional, List, Set, Dict, Tuple, Union, TYPE_CHECKING

from slither.core.children.child_function import ChildFunction
from slither.core.declarations.solidity_variables import (
    SolidityVariable,
    SolidityFunction,
)
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.core.solidity_types import ElementaryType
from slither.slithir.convert import convert_expression
from slither.slithir.operations import (
    Balance,
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
from slither.slithir.variables import (
    Constant,
    LocalIRVariable,
    ReferenceVariable,
    StateIRVariable,
    TemporaryVariable,
    TupleVariable,
)
from slither.all_exceptions import SlitherException
from slither.core.declarations import Contract

from slither.core.expressions.expression import Expression

if TYPE_CHECKING:
    from slither.core.declarations import Function
    from slither.slithir.variables.variable import SlithIRVariable
    from slither.core.slither_core import SlitherCore
    from slither.utils.type_helpers import (
        InternalCallType,
        HighLevelCallType,
        LibraryCallType,
        LowLevelCallType,
    )


# pylint: disable=too-many-lines,too-many-branches,too-many-instance-attributes

###################################################################################
###################################################################################
# region NodeType
###################################################################################
###################################################################################


class NodeType(Enum):
    ENTRYPOINT = 0x0  # no expression

    # Node with expression

    EXPRESSION = 0x10  # normal case
    RETURN = 0x11  # RETURN may contain an expression
    IF = 0x12
    VARIABLE = 0x13  # Declaration of variable
    ASSEMBLY = 0x14
    IFLOOP = 0x15

    # Merging nodes
    # Can have phi IR operation
    ENDIF = 0x50  # ENDIF node source mapping points to the if/else body
    STARTLOOP = 0x51  # STARTLOOP node source mapping points to the entire loop body
    ENDLOOP = 0x52  # ENDLOOP node source mapping points to the entire loop body

    # Below the nodes have no expression
    # But are used to expression CFG structure

    # Absorbing node
    THROW = 0x20

    # Loop related nodes
    BREAK = 0x31
    CONTINUE = 0x32

    # Only modifier node
    PLACEHOLDER = 0x40

    TRY = 0x41
    CATCH = 0x42

    # Node not related to the CFG
    # Use for state variable declaration
    OTHER_ENTRYPOINT = 0x60

    #    @staticmethod
    def __str__(self):
        if self == NodeType.ENTRYPOINT:
            return "ENTRY_POINT"
        if self == NodeType.EXPRESSION:
            return "EXPRESSION"
        if self == NodeType.RETURN:
            return "RETURN"
        if self == NodeType.IF:
            return "IF"
        if self == NodeType.VARIABLE:
            return "NEW VARIABLE"
        if self == NodeType.ASSEMBLY:
            return "INLINE ASM"
        if self == NodeType.IFLOOP:
            return "IF_LOOP"
        if self == NodeType.THROW:
            return "THROW"
        if self == NodeType.BREAK:
            return "BREAK"
        if self == NodeType.CONTINUE:
            return "CONTINUE"
        if self == NodeType.PLACEHOLDER:
            return "_"
        if self == NodeType.TRY:
            return "TRY"
        if self == NodeType.CATCH:
            return "CATCH"
        if self == NodeType.ENDIF:
            return "END_IF"
        if self == NodeType.STARTLOOP:
            return "BEGIN_LOOP"
        if self == NodeType.ENDLOOP:
            return "END_LOOP"
        if self == NodeType.OTHER_ENTRYPOINT:
            return "OTHER_ENTRYPOINT"
        return "Unknown type {}".format(hex(self.value))


# endregion

# I am not sure why, but pylint reports a lot of "no-member" issue that are not real (Josselin)
# pylint: disable=no-member
class Node(SourceMapping, ChildFunction):  # pylint: disable=too-many-public-methods
    """
    Node class

    """

    def __init__(self, node_type: NodeType, node_id: int):
        super().__init__()
        self._node_type = node_type

        # TODO: rename to explicit CFG
        self._sons: List["Node"] = []
        self._fathers: List["Node"] = []

        ## Dominators info
        # Dominators nodes
        self._dominators: Set["Node"] = set()
        self._immediate_dominator: Optional["Node"] = None
        ## Nodes of the dominators tree
        # self._dom_predecessors = set()
        self._dom_successors: Set["Node"] = set()
        # Dominance frontier
        self._dominance_frontier: Set["Node"] = set()
        # Phi origin
        # key are variable name
        self._phi_origins_state_variables: Dict[str, Tuple[StateVariable, Set["Node"]]] = {}
        self._phi_origins_local_variables: Dict[str, Tuple[LocalVariable, Set["Node"]]] = {}
        # self._phi_origins_member_variables: Dict[str, Tuple[MemberVariable, Set["Node"]]] = {}

        self._expression: Optional[Expression] = None
        self._variable_declaration: Optional[LocalVariable] = None
        self._node_id: int = node_id

        self._vars_written: List[Variable] = []
        self._vars_read: List[Variable] = []

        self._ssa_vars_written: List["SlithIRVariable"] = []
        self._ssa_vars_read: List["SlithIRVariable"] = []

        self._internal_calls: List["Function"] = []
        self._solidity_calls: List[SolidityFunction] = []
        self._high_level_calls: List["HighLevelCallType"] = []  # contains library calls
        self._library_calls: List["LibraryCallType"] = []
        self._low_level_calls: List["LowLevelCallType"] = []
        self._external_calls_as_expressions: List[Expression] = []
        self._internal_calls_as_expressions: List[Expression] = []
        self._irs: List[Operation] = []
        self._irs_ssa: List[Operation] = []

        self._state_vars_written: List[StateVariable] = []
        self._state_vars_read: List[StateVariable] = []
        self._solidity_vars_read: List[SolidityVariable] = []

        self._ssa_state_vars_written: List[StateIRVariable] = []
        self._ssa_state_vars_read: List[StateIRVariable] = []

        self._local_vars_read: List[LocalVariable] = []
        self._local_vars_written: List[LocalVariable] = []

        self._slithir_vars: Set["SlithIRVariable"] = set()  # non SSA

        self._ssa_local_vars_read: List[LocalIRVariable] = []
        self._ssa_local_vars_written: List[LocalIRVariable] = []

        self._expression_vars_written: List[Expression] = []
        self._expression_vars_read: List[Expression] = []
        self._expression_calls: List[Expression] = []

        # Computed on the fly, can be True of False
        self._can_reenter: Optional[bool] = None
        self._can_send_eth: Optional[bool] = None

        self._asm_source_code: Optional[Union[str, Dict]] = None

    ###################################################################################
    ###################################################################################
    # region General's properties
    ###################################################################################
    ###################################################################################

    @property
    def slither(self) -> "SlitherCore":
        return self.function.slither

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
    def type(self, new_type: NodeType):
        self._node_type = new_type

    @property
    def will_return(self) -> bool:
        if not self.sons and self.type != NodeType.THROW:
            if SolidityFunction("revert()") not in self.solidity_calls:
                if SolidityFunction("revert(string)") not in self.solidity_calls:
                    return True
        return False

    # endregion
    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################

    @property
    def variables_read(self) -> List[Variable]:
        """
        list(Variable): Variables read (local/state/solidity)
        """
        return list(self._vars_read)

    @property
    def state_variables_read(self) -> List[StateVariable]:
        """
        list(StateVariable): State variables read
        """
        return list(self._state_vars_read)

    @property
    def local_variables_read(self) -> List[LocalVariable]:
        """
        list(LocalVariable): Local variables read
        """
        return list(self._local_vars_read)

    @property
    def solidity_variables_read(self) -> List[SolidityVariable]:
        """
        list(SolidityVariable): State variables read
        """
        return list(self._solidity_vars_read)

    @property
    def ssa_variables_read(self) -> List["SlithIRVariable"]:
        """
        list(Variable): Variables read (local/state/solidity)
        """
        return list(self._ssa_vars_read)

    @property
    def ssa_state_variables_read(self) -> List[StateIRVariable]:
        """
        list(StateVariable): State variables read
        """
        return list(self._ssa_state_vars_read)

    @property
    def ssa_local_variables_read(self) -> List[LocalIRVariable]:
        """
        list(LocalVariable): Local variables read
        """
        return list(self._ssa_local_vars_read)

    @property
    def variables_read_as_expression(self) -> List[Expression]:
        return self._expression_vars_read

    @variables_read_as_expression.setter
    def variables_read_as_expression(self, exprs: List[Expression]):
        self._expression_vars_read = exprs

    @property
    def slithir_variables(self) -> List["SlithIRVariable"]:
        return list(self._slithir_vars)

    @property
    def variables_written(self) -> List[Variable]:
        """
        list(Variable): Variables written (local/state/solidity)
        """
        return list(self._vars_written)

    @property
    def state_variables_written(self) -> List[StateVariable]:
        """
        list(StateVariable): State variables written
        """
        return list(self._state_vars_written)

    @property
    def local_variables_written(self) -> List[LocalVariable]:
        """
        list(LocalVariable): Local variables written
        """
        return list(self._local_vars_written)

    @property
    def ssa_variables_written(self) -> List["SlithIRVariable"]:
        """
        list(Variable): Variables written (local/state/solidity)
        """
        return list(self._ssa_vars_written)

    @property
    def ssa_state_variables_written(self) -> List[StateIRVariable]:
        """
        list(StateVariable): State variables written
        """
        return list(self._ssa_state_vars_written)

    @property
    def ssa_local_variables_written(self) -> List[LocalIRVariable]:
        """
        list(LocalVariable): Local variables written
        """
        return list(self._ssa_local_vars_written)

    @property
    def variables_written_as_expression(self) -> List[Expression]:
        return self._expression_vars_written

    @variables_written_as_expression.setter
    def variables_written_as_expression(self, exprs: List[Expression]):
        self._expression_vars_written = exprs

    # endregion
    ###################################################################################
    ###################################################################################
    # region Calls
    ###################################################################################
    ###################################################################################

    @property
    def internal_calls(self) -> List["InternalCallType"]:
        """
        list(Function or SolidityFunction): List of internal/soldiity function calls
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
        Include library calls
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
    def external_calls_as_expressions(self) -> List[Expression]:
        """
        list(CallExpression): List of message calls (that creates a transaction)
        """
        return self._external_calls_as_expressions

    @external_calls_as_expressions.setter
    def external_calls_as_expressions(self, exprs: List[Expression]):
        self._external_calls_as_expressions = exprs

    @property
    def internal_calls_as_expressions(self) -> List[Expression]:
        """
        list(CallExpression): List of internal calls (that dont create a transaction)
        """
        return self._internal_calls_as_expressions

    @internal_calls_as_expressions.setter
    def internal_calls_as_expressions(self, exprs: List[Expression]):
        self._internal_calls_as_expressions = exprs

    @property
    def calls_as_expression(self) -> List[Expression]:
        return list(self._expression_calls)

    @calls_as_expression.setter
    def calls_as_expression(self, exprs: List[Expression]):
        self._expression_calls = exprs

    def can_reenter(self, callstack=None) -> bool:
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
        # pylint: disable=import-outside-toplevel
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
        # pylint: disable=import-outside-toplevel
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
    def expression(self) -> Optional[Expression]:
        """
        Expression: Expression of the node
        """
        return self._expression

    def add_expression(self, expression: Expression, bypass_verif_empty: bool = False):
        assert self._expression is None or bypass_verif_empty
        self._expression = expression

    def add_variable_declaration(self, var: LocalVariable):
        assert self._variable_declaration is None
        self._variable_declaration = var
        if var.expression:
            self._vars_written += [var]
            self._local_vars_written += [var]

    @property
    def variable_declaration(self) -> Optional[LocalVariable]:
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
            c.name in ["require(bool)", "require(bool,string)", "assert(bool)"]
            for c in self.internal_calls
        )

    def contains_if(self, include_loop=True) -> bool:
        """
            Check if the node is a IF node
        Returns:
            bool: True if the node is a conditional node (IF or IFLOOP)
        """
        if include_loop:
            return self.type in [NodeType.IF, NodeType.IFLOOP]
        return self.type == NodeType.IF

    def is_conditional(self, include_loop=True) -> bool:
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
    def inline_asm(self) -> Optional[Union[str, Dict]]:
        return self._asm_source_code

    def add_inline_asm(self, asm: Union[str, Dict]):
        self._asm_source_code = asm

    # endregion
    ###################################################################################
    ###################################################################################
    # region Graph
    ###################################################################################
    ###################################################################################

    def add_father(self, father: "Node"):
        """Add a father node

        Args:
            father: father to add
        """
        self._fathers.append(father)

    def set_fathers(self, fathers: List["Node"]):
        """Set the father nodes

        Args:
            fathers: list of fathers to add
        """
        self._fathers = fathers

    @property
    def fathers(self) -> List["Node"]:
        """Returns the father nodes

        Returns:
            list(Node): list of fathers
        """
        return list(self._fathers)

    def remove_father(self, father: "Node"):
        """Remove the father node. Do nothing if the node is not a father

        Args:
            :param father:
        """
        self._fathers = [x for x in self._fathers if x.node_id != father.node_id]

    def remove_son(self, son: "Node"):
        """Remove the son node. Do nothing if the node is not a son

        Args:
            :param son:
        """
        self._sons = [x for x in self._sons if x.node_id != son.node_id]

    def add_son(self, son: "Node"):
        """Add a son node

        Args:
            son: son to add
        """
        self._sons.append(son)

    def set_sons(self, sons: List["Node"]):
        """Set the son nodes

        Args:
            sons: list of fathers to add
        """
        self._sons = sons

    @property
    def sons(self) -> List["Node"]:
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
    def irs(self) -> List[Operation]:
        """Returns the slithIR representation

        return
            list(slithIR.Operation)
        """
        return self._irs

    @property
    def irs_ssa(self) -> List[Operation]:
        """Returns the slithIR representation with SSA

        return
            list(slithIR.Operation)
        """
        return self._irs_ssa

    @irs_ssa.setter
    def irs_ssa(self, irs):
        self._irs_ssa = irs

    def add_ssa_ir(self, ir: Operation):
        """
        Use to place phi operation
        """
        ir.set_node(self)
        self._irs_ssa.append(ir)

    def slithir_generation(self):
        if self.expression:
            expression = self.expression
            self._irs = convert_expression(expression, self)

        self._find_read_write_call()

    def all_slithir_operations(self) -> List[Operation]:
        irs = self.irs
        for ir in irs:
            if isinstance(ir, InternalCall):
                irs += ir.function.all_slithir_operations()
        return irs

    @staticmethod
    def _is_non_slithir_var(var: Variable):
        return not isinstance(var, (Constant, ReferenceVariable, TemporaryVariable, TupleVariable))

    @staticmethod
    def _is_valid_slithir_var(var: Variable):
        return isinstance(var, (ReferenceVariable, TemporaryVariable, TupleVariable))

    # endregion
    ###################################################################################
    ###################################################################################
    # region Dominators
    ###################################################################################
    ###################################################################################

    @property
    def dominators(self) -> Set["Node"]:
        """
        Returns:
            set(Node)
        """
        return self._dominators

    @dominators.setter
    def dominators(self, dom: Set["Node"]):
        self._dominators = dom

    @property
    def immediate_dominator(self) -> Optional["Node"]:
        """
        Returns:
            Node or None
        """
        return self._immediate_dominator

    @immediate_dominator.setter
    def immediate_dominator(self, idom: "Node"):
        self._immediate_dominator = idom

    @property
    def dominance_frontier(self) -> Set["Node"]:
        """
        Returns:
            set(Node)
        """
        return self._dominance_frontier

    @dominance_frontier.setter
    def dominance_frontier(self, doms: Set["Node"]):
        """
        Returns:
            set(Node)
        """
        self._dominance_frontier = doms

    @property
    def dominator_successors(self):
        return self._dom_successors

    @property
    def dominance_exploration_ordered(self) -> List["Node"]:
        """
        Sorted list of all the nodes to explore to follow the dom
        :return: list(nodes)
        """
        # Explore direct dominance
        to_explore = sorted(list(self.dominator_successors), key=lambda x: x.node_id)

        # Explore dominance frontier
        # The frontier is the limit where this node dominates
        # We need to explore it because the sub of the direct dominance
        # Might not be dominator of their own sub
        to_explore += sorted(list(self.dominance_frontier), key=lambda x: x.node_id)
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
    ) -> Dict[str, Tuple[LocalVariable, Set["Node"]]]:
        return self._phi_origins_local_variables

    @property
    def phi_origins_state_variables(
        self,
    ) -> Dict[str, Tuple[StateVariable, Set["Node"]]]:
        return self._phi_origins_state_variables

    # @property
    # def phi_origin_member_variables(self) -> Dict[str, Tuple[MemberVariable, Set["Node"]]]:
    #     return self._phi_origins_member_variables

    def add_phi_origin_local_variable(self, variable: LocalVariable, node: "Node"):
        if variable.name not in self._phi_origins_local_variables:
            self._phi_origins_local_variables[variable.name] = (variable, set())
        (v, nodes) = self._phi_origins_local_variables[variable.name]
        assert v == variable
        nodes.add(node)

    def add_phi_origin_state_variable(self, variable: StateVariable, node: "Node"):
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

    def _find_read_write_call(self):  # pylint: disable=too-many-statements

        for ir in self.irs:

            self._slithir_vars |= {v for v in ir.read if self._is_valid_slithir_var(v)}

            if isinstance(ir, OperationWithLValue):
                var = ir.lvalue
                if var and self._is_valid_slithir_var(var):
                    self._slithir_vars.add(var)

            if not isinstance(ir, (Phi, Index, Member)):
                self._vars_read += [v for v in ir.read if self._is_non_slithir_var(v)]
                for var in ir.read:
                    if isinstance(var, ReferenceVariable):
                        self._vars_read.append(var.points_to_origin)
            elif isinstance(ir, (Member, Index)):
                var = ir.variable_left if isinstance(ir, Member) else ir.variable_right
                if self._is_non_slithir_var(var):
                    self._vars_read.append(var)
                if isinstance(var, ReferenceVariable):
                    origin = var.points_to_origin
                    if self._is_non_slithir_var(origin):
                        self._vars_read.append(origin)

            if isinstance(ir, OperationWithLValue):
                if isinstance(ir, (Index, Member, Length, Balance)):
                    continue  # Don't consider Member and Index operations -> ReferenceVariable
                var = ir.lvalue
                if isinstance(var, ReferenceVariable):
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
            elif isinstance(ir, HighLevelCall) and not isinstance(ir, LibraryCall):
                if isinstance(ir.destination.type, Contract):
                    self._high_level_calls.append((ir.destination.type, ir.function))
                elif ir.destination == SolidityVariable("this"):
                    self._high_level_calls.append((self.function.contract, ir.function))
                else:
                    try:
                        self._high_level_calls.append((ir.destination.type.type, ir.function))
                    except AttributeError as error:
                        #  pylint: disable=raise-missing-from
                        raise SlitherException(
                            f"Function not found on {ir}. Please try compiling with a recent Solidity version. {error}"
                        )
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
    def _convert_ssa(v: Variable):
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
            if isinstance(ir, PhiCallback):
                continue
            if not isinstance(ir, (Phi, Index, Member)):
                self._ssa_vars_read += [
                    v for v in ir.read if isinstance(v, (StateIRVariable, LocalIRVariable))
                ]
                for var in ir.read:
                    if isinstance(var, ReferenceVariable):
                        origin = var.points_to_origin
                        if isinstance(origin, (StateIRVariable, LocalIRVariable)):
                            self._ssa_vars_read.append(origin)

            elif isinstance(ir, (Member, Index)):
                if isinstance(ir.variable_right, (StateIRVariable, LocalIRVariable)):
                    self._ssa_vars_read.append(ir.variable_right)
                if isinstance(ir.variable_right, ReferenceVariable):
                    origin = ir.variable_right.points_to_origin
                    if isinstance(origin, (StateIRVariable, LocalIRVariable)):
                        self._ssa_vars_read.append(origin)

            if isinstance(ir, OperationWithLValue):
                if isinstance(ir, (Index, Member, Length, Balance)):
                    continue  # Don't consider Member and Index operations -> ReferenceVariable
                var = ir.lvalue
                if isinstance(var, ReferenceVariable):
                    var = var.points_to_origin
                # Only store non-slithIR variables
                if var and isinstance(var, (StateIRVariable, LocalIRVariable)):
                    if isinstance(ir, PhiCallback):
                        continue
                    self._ssa_vars_written.append(var)
        self._ssa_vars_read = list(set(self._ssa_vars_read))
        self._ssa_state_vars_read = [v for v in self._ssa_vars_read if isinstance(v, StateVariable)]
        self._ssa_local_vars_read = [v for v in self._ssa_vars_read if isinstance(v, LocalVariable)]
        self._ssa_vars_written = list(set(self._ssa_vars_written))
        self._ssa_state_vars_written = [
            v for v in self._ssa_vars_written if isinstance(v, StateVariable)
        ]
        self._ssa_local_vars_written = [
            v for v in self._ssa_vars_written if isinstance(v, LocalVariable)
        ]

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
        additional_info = ""
        if self.expression:
            additional_info += " " + str(self.expression)
        elif self.variable_declaration:
            additional_info += " " + str(self.variable_declaration)
        txt = str(self._node_type) + additional_info
        return txt


# endregion
###################################################################################
###################################################################################
# region Utils
###################################################################################
###################################################################################


def link_nodes(node1: Node, node2: Node):
    node1.add_son(node2)
    node2.add_father(node1)


def insert_node(origin: Node, node_inserted: Node):
    sons = origin.sons
    link_nodes(origin, node_inserted)
    for son in sons:
        son.remove_father(origin)
        origin.remove_son(son)

        link_nodes(node_inserted, son)


def recheable(node: Node) -> Set[Node]:
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
