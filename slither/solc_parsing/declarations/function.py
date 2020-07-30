import logging
from typing import Dict, Optional, Union, List, TYPE_CHECKING

from slither.core.cfg.node import NodeType, link_nodes, insert_node, Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import (
    Function,
    ModifierStatements,
    FunctionType,
)

from slither.core.expressions import AssignmentOperation
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple
from slither.solc_parsing.cfg.node import NodeSolc
from slither.solc_parsing.exceptions import ParsingError
from slither.solc_parsing.expressions.expression_parsing import parse_expression
from slither.solc_parsing.types.types import ASTNode, Block, IfStatement, ForStatement, WhileStatement, \
    VariableDeclarationStatement, TryStatement, TryCatchClause, VariableDeclaration, ExpressionStatement, \
    TupleExpression, Identifier, Assignment, ParameterList, Return, Continue, Break, EmitStatement, Throw, \
    FunctionDefinition, ModifierInvocation, InlineAssembly
from slither.solc_parsing.variables.local_variable import LocalVariableSolc
from slither.solc_parsing.variables.local_variable_init_from_tuple import (
    LocalVariableInitFromTupleSolc,
)
from slither.solc_parsing.yul.parse_yul import YulBlock
from slither.utils.expression_manipulations import SplitTernaryExpression
from slither.visitors.expression.export_values import ExportValues
from slither.visitors.expression.has_conditional import HasConditional

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression
    from slither.solc_parsing.declarations.contract import ContractSolc
    from slither.solc_parsing.slitherSolc import SlitherSolc
    from slither.core.slither_core import SlitherCore

LOGGER = logging.getLogger("FunctionSolc")


def link_underlying_nodes(node1: NodeSolc, node2: NodeSolc):
    link_nodes(node1.underlying_node, node2.underlying_node)


# pylint: disable=too-many-lines,too-many-branches,too-many-locals,too-many-statements,too-many-instance-attributes


class FunctionSolc:

    def __init__(
        self,
        function: Function,
        function_data: FunctionDefinition,
        contract_parser: "ContractSolc",
    ):
        self._slither_parser: "SlitherSolc" = contract_parser.slither_parser
        self._contract_parser = contract_parser
        self._function = function

        # Only present if compact AST
        self._referenced_declaration: Optional[int] = None
        self._function.name = function_data.name
        self._function.id = function_data.id
        self._functionNotParsed = function_data
        self._params_was_analyzed = False
        self._content_was_analyzed = False

        self._counter_scope_local_variables = 0
        # variable renamed will map the solc id
        # to the variable. It only works for compact format
        # Later if an expression provides the referencedDeclaration attr
        # we can retrieve the variable
        # It only matters if two variables have the same name in the function
        # which is only possible with solc > 0.5
        self._variables_renamed: Dict[
            int, Union[LocalVariableSolc, LocalVariableInitFromTupleSolc]
        ] = {}

        self._analyze_type()

        self.parameters_src = SourceMapping()
        self.returns_src = SourceMapping()

        self._node_to_nodesolc: Dict[Node, NodeSolc] = dict()
        self._node_to_yulobject: Dict[Node, YulBlock] = dict()

        self._local_variables_parser: List[
            Union[LocalVariableSolc, LocalVariableInitFromTupleSolc]
        ] = []

    @property
    def underlying_function(self) -> Function:
        return self._function

    @property
    def contract_parser(self) -> "ContractSolc":
        return self._contract_parser

    @property
    def slither_parser(self) -> "SlitherSolc":
        return self._slither_parser

    @property
    def slither(self) -> "SlitherCore":
        return self._function.slither

    ###################################################################################
    ###################################################################################
    # region AST format
    ###################################################################################
    ###################################################################################

    @property
    def referenced_declaration(self) -> Optional[str]:
        """
        Return the compact AST referenced declaration id (None for legacy AST)
        """
        return self._referenced_declaration

    # endregion
    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################

    @property
    def variables_renamed(
            self,
    ) -> Dict[int, Union[LocalVariableSolc, LocalVariableInitFromTupleSolc]]:
        return self._variables_renamed

    def _add_local_variable(
            self, local_var_parser: Union[LocalVariableSolc, LocalVariableInitFromTupleSolc]
    ):
        # If two local variables have the same name
        # We add a suffix to the new variable
        # This is done to prevent collision during SSA translation
        # Use of while in case of collision
        # In the worst case, the name will be really long
        if local_var_parser.underlying_variable.name:
            known_variables = [v.name for v in self._function.variables]
            while local_var_parser.underlying_variable.name in known_variables:
                local_var_parser.underlying_variable.name += "_scope_{}".format(
                    self._counter_scope_local_variables
                )
                self._counter_scope_local_variables += 1
                known_variables = [v.name for v in self._function.variables]
        if local_var_parser.reference_id is not None:
            self._variables_renamed[local_var_parser.reference_id] = local_var_parser
        self._function.variables_as_dict[
            local_var_parser.underlying_variable.name
        ] = local_var_parser.underlying_variable
        self._local_variables_parser.append(local_var_parser)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyses
    ###################################################################################
    ###################################################################################

    @property
    def function_not_parsed(self) -> FunctionDefinition:
        return self._functionNotParsed

    def _analyze_type(self):
        """
        Analyz the type of the function
        Myst be called in the constructor as the name might change according to the function's type
        For example both the fallback and the receiver will have an empty name
        :return:
        """

        if self._function.name == "":
            self._function.function_type = FunctionType.FALLBACK
            # 0.6.x introduced the receiver function
            # It has also an empty name, so we need to check the kind attribute
            if self._functionNotParsed.kind == "receive":
                self._function.function_type = FunctionType.RECEIVE
        else:
            self._function.function_type = FunctionType.NORMAL

        if self._function.name == self._function.contract_declarer.name:
            self._function.function_type = FunctionType.CONSTRUCTOR

    def _analyze_attributes(self):
        if isinstance(self._functionNotParsed, FunctionDefinition):
            if self._functionNotParsed.mutability == 'payable':
                self._function.payable = True
            elif self._functionNotParsed.mutability == 'pure':
                self._function.pure = True
                self._function.view = True
            elif self._functionNotParsed.mutability == 'view':
                self._function.view = True

            if self._functionNotParsed.kind == "constructor":
                self._function.function_type = FunctionType.CONSTRUCTOR

        self._function.visibility = self._functionNotParsed.visibility

    def analyze_params(self):
        # Can be re-analyzed due to inheritance
        if self._params_was_analyzed:
            return

        self._params_was_analyzed = True

        self._analyze_attributes()

        if self._functionNotParsed.params:
            self._parse_params(self._functionNotParsed.params)
        if self._functionNotParsed.rets:
            self._parse_returns(self._functionNotParsed.rets)

    def analyze_content(self):
        if self._content_was_analyzed:
            return

        self._content_was_analyzed = True

        if self._functionNotParsed.body:
            self._function.is_implemented = True
            self._parse_cfg(self._functionNotParsed.body)

        for modifier in self._functionNotParsed.modifiers:
            self._parse_modifier(modifier)

        for local_var_parser in self._local_variables_parser:
            local_var_parser.analyze(self)

        for node_parser in self._node_to_nodesolc.values():
            node_parser.analyze_expressions(self)

        for node_parser in self._node_to_yulobject.values():
            node_parser.analyze_expressions()

        self._filter_ternary()

        self._remove_alone_endif()

    # endregion
    ###################################################################################
    ###################################################################################
    # region Nodes
    ###################################################################################
    ###################################################################################

    def _new_node(self, node_type: NodeType, src: Union[str, Dict]) -> NodeSolc:
        node = self._function.new_node(node_type, src)
        node_parser = NodeSolc(node)
        self._node_to_nodesolc[node] = node_parser
        return node_parser

    def _new_yul_block(self, src: Union[str, Dict]) -> YulBlock:
        node = self._function.new_node(NodeType.ASSEMBLY, src)
        yul_object = YulBlock(
            self._function.contract,
            node,
            [self._function.name, f"asm_{len(self._node_to_yulobject)}"],
            parent_func=self._function,
        )
        self._node_to_yulobject[node] = yul_object
        return yul_object

    # endregion
    ###################################################################################
    ###################################################################################
    # region Parsing function
    ###################################################################################
    ###################################################################################

    def _parse_if(self, stmt: IfStatement, node: NodeSolc) -> NodeSolc:
        condition_node = self._new_node(NodeType.IF, stmt.condition.src)
        condition_node.add_unparsed_expression(stmt.condition)
        link_underlying_nodes(node, condition_node)
        trueStatement = self._parse(stmt.true_body, condition_node)

        if stmt.false_body:
            falseStatement = self._parse(stmt.false_body, condition_node)
        else:
            falseStatement = None

        endIf_node = self._new_node(NodeType.ENDIF, stmt.src)
        link_underlying_nodes(trueStatement, endIf_node)

        if falseStatement:
            link_underlying_nodes(falseStatement, endIf_node)
        else:
            link_underlying_nodes(condition_node, endIf_node)
        return endIf_node

    def _parse_while(self, stmt: WhileStatement, node: NodeSolc) -> NodeSolc:
        node_startWhile = self._new_node(NodeType.STARTLOOP, stmt.src)

        node_condition = self._new_node(NodeType.IFLOOP, stmt.condition.src)
        node_condition.add_unparsed_expression(stmt.condition)
        statement = self._parse(stmt.body, node_condition)

        node_endWhile = self._new_node(NodeType.ENDLOOP, stmt.src)

        link_underlying_nodes(node, node_startWhile)

        if stmt.is_do_while:
            # empty block, loop from the start to the condition
            if not node_condition.underlying_node.sons:
                link_underlying_nodes(node_startWhile, node_condition)
            else:
                link_nodes(node_startWhile.underlying_node, node_condition.underlying_node.sons[0])
        else:
            link_underlying_nodes(node_startWhile, node_condition)
        link_underlying_nodes(statement, node_condition)
        link_underlying_nodes(node_condition, node_endWhile)

        return node_endWhile

    def _parse_for(self, stmt: ForStatement, node: NodeSolc) -> NodeSolc:
        node_startLoop = self._new_node(NodeType.STARTLOOP, stmt.src)
        node_endLoop = self._new_node(NodeType.ENDLOOP, stmt.src)

        if stmt.init:
            node_init_expression = self._parse(stmt.init, node)
            link_underlying_nodes(node_init_expression, node_startLoop)
        else:
            link_underlying_nodes(node, node_startLoop)

        if stmt.cond:
            node_condition = self._new_node(NodeType.IFLOOP, stmt.cond.src)
            node_condition.add_unparsed_expression(stmt.cond)
            link_underlying_nodes(node_startLoop, node_condition)

            node_beforeBody = node_condition
        else:
            node_condition = None

            node_beforeBody = node_startLoop

        node_body = self._parse(stmt.body, node_beforeBody)

        if node_condition:
            link_underlying_nodes(node_condition, node_endLoop)

        node_LoopExpression = None
        if stmt.loop:
            node_LoopExpression = self._parse(stmt.loop, node_body)
            link_underlying_nodes(node_LoopExpression, node_beforeBody)
        else:
            link_underlying_nodes(node_body, node_beforeBody)

        if not stmt.cond:
            if not stmt.loop:
                # TODO: fix case where loop has no expression
                link_underlying_nodes(node_startLoop, node_endLoop)
            elif node_LoopExpression:
                link_underlying_nodes(node_LoopExpression, node_endLoop)

        return node_endLoop

    def _parse_try_catch(self, stmt: TryStatement, node: NodeSolc) -> NodeSolc:
        new_node = self._new_node(NodeType.TRY, stmt.src)
        new_node.add_unparsed_expression(stmt.external_call)
        link_underlying_nodes(node, new_node)
        node = new_node

        for clause in stmt.clauses:
            self._parse(clause, node)
        return node

    def _parse_catch(self, stmt: TryCatchClause, node: NodeSolc) -> NodeSolc:
        try_node = self._new_node(NodeType.CATCH, stmt.src)
        link_underlying_nodes(node, try_node)

        if stmt.params:
            for param in stmt.params.params:
                self._add_param(param)

        return self._parse(stmt.block, try_node)

    def _parse_variable_definition(self, stmt: VariableDeclarationStatement, node: NodeSolc) -> NodeSolc:
        if len(stmt.variables) == 1:
            local_var = LocalVariable()
            local_var.set_function(self._function)
            local_var.set_offset(stmt.src, self._function.slither)

            local_var_parser = LocalVariableSolc(local_var, stmt)
            self._add_local_variable(local_var_parser)

            new_node = self._new_node(NodeType.VARIABLE, stmt.src)
            new_node.underlying_node.add_variable_declaration(local_var)
            link_underlying_nodes(node, new_node)
            return new_node
        else:
            """
            There are 2 cases we need to handle
            
            1)  Initializing multiple vars with multiple individual values:
                    var (a, b) = (1,2);
                In this case, we convert to the following code:
                    var a = 1;
                    var b = 2;
                    
            2)  Initializing multiple vars with any other method (function call, skipped args, etc):
                    var (a, , c) = f();
                In this case, we convert to the following code:
                    var a;
                    var c;
                    (a, , c) = f();
            """

            if isinstance(stmt.initial_value, TupleExpression) \
                    and len(stmt.initial_value.components) == len(stmt.variables):

                for i, variable in enumerate(stmt.variables):
                    if variable is None:
                        continue

                    node = self._parse_variable_definition(VariableDeclarationStatement(
                        [variable],
                        stmt.initial_value.components[i],
                        src=variable.src,
                        id=variable.id,
                    ), node)

                return node
            else:
                for i, variable in enumerate(stmt.variables):
                    if not variable:
                        continue

                    node = self._parse_variable_definition_init_tuple(VariableDeclarationStatement(
                        [variable],
                        None,
                        src=variable.src,
                        id=variable.id,
                    ), i, node)

                new_node = self._new_node(NodeType.EXPRESSION, stmt.src)
                new_node.add_unparsed_expression(Assignment(
                    TupleExpression(
                        [Identifier(v.name, type_str=v.type_str, constant=False, pure=False, src=v.src,
                                    id=v.id) if v else None for v in stmt.variables],
                        False,
                        type_str="tuple()",
                        constant=False,
                        pure=False,
                        src=stmt.src,
                        id=stmt.id,
                    ),
                    "=",
                    stmt.initial_value,
                    type_str="tuple()",
                    constant=False,
                    pure=False,
                    src=stmt.src,
                    id=stmt.id,
                ))
                link_underlying_nodes(node, new_node)
                return new_node

    def _parse_variable_definition_init_tuple(
            self, stmt: VariableDeclarationStatement, index: int, node: NodeSolc
    ) -> NodeSolc:
        local_var = LocalVariableInitFromTuple()
        local_var.set_function(self._function)
        local_var.set_offset(stmt.src, self._function.slither)

        local_var_parser = LocalVariableInitFromTupleSolc(local_var, stmt, index)

        self._add_local_variable(local_var_parser)

        new_node = self._new_node(NodeType.VARIABLE, stmt.src)
        new_node.underlying_node.add_variable_declaration(local_var)
        link_underlying_nodes(node, new_node)
        return new_node

    def _parse_continue(self, stmt: Continue, node: NodeSolc) -> NodeSolc:
        new_node = self._new_node(NodeType.CONTINUE, stmt.src)
        link_underlying_nodes(node, new_node)
        return new_node

    def _parse_break(self, stmt: Break, node: NodeSolc) -> NodeSolc:
        new_node = self._new_node(NodeType.BREAK, stmt.src)
        link_underlying_nodes(node, new_node)
        return new_node

    def _parse_throw(self, stmt: Throw, node: NodeSolc) -> NodeSolc:
        new_node = self._new_node(NodeType.THROW, stmt.src)
        link_underlying_nodes(node, new_node)
        return new_node

    def _parse_emit_statement(self, stmt: EmitStatement, node: NodeSolc) -> NodeSolc:
        new_node = self._new_node(NodeType.EXPRESSION, stmt.src)
        new_node.add_unparsed_expression(stmt.event_call)
        link_underlying_nodes(node, new_node)
        return new_node

    def _parse_block(self, stmt: Block, node: NodeSolc) -> NodeSolc:
        for statement in stmt.statements:
            node = self._parse(statement, node)
        return node

    def _parse_expression_statement(self, stmt: ExpressionStatement, node: NodeSolc) -> NodeSolc:
        new_node = self._new_node(NodeType.EXPRESSION, stmt.src)
        new_node.add_unparsed_expression(stmt.expression)
        link_underlying_nodes(node, new_node)
        return new_node

    def _parse_return(self, stmt: Return, node: NodeSolc) -> NodeSolc:
        return_node = self._new_node(NodeType.RETURN, stmt.src)
        link_underlying_nodes(node, return_node)

        if stmt.expression:
            return_node.add_unparsed_expression(stmt.expression)

        return return_node

    def _parse_inline_assembly(self, stmt: InlineAssembly, node: NodeSolc) -> NodeSolc:
        self._function.contains_assembly = True

        if stmt.ast:
            if isinstance(stmt.ast, dict):
                # Added with solc 0.6 - the yul code is an AST
                yul_object = self._new_yul_block(stmt.src)
                entrypoint = yul_object.entrypoint
                exitpoint = yul_object.convert(stmt.ast)

                # technically, entrypoint and exitpoint are YulNodes and we should be returning a NodeSolc here
                # but they both expose an underlying_node so oh well
                link_underlying_nodes(node, entrypoint)
                return exitpoint
            else:
                # Added with solc 0.4.12
                asm_node = self._new_node(NodeType.ASSEMBLY, stmt.src)
                asm_node.underlying_node.add_inline_asm(stmt.ast)
                link_underlying_nodes(node, asm_node)
                return node
        else:
            asm_node = self._new_node(NodeType.ASSEMBLY, stmt.src)
            link_underlying_nodes(node, asm_node)
            return node

    def _parse_unhandled(self, stmt: ASTNode, node: NodeSolc) -> NodeSolc:
        raise Exception("unhandled ast node", stmt.__class__)

    def _parse(self, stmt: ASTNode, node: NodeSolc) -> NodeSolc:
        return FunctionSolc.PARSERS.get(stmt.__class__, FunctionSolc._parse_unhandled)(self, stmt, node)

    PARSERS = {
        VariableDeclarationStatement: _parse_variable_definition,
        WhileStatement: _parse_while,
        Block: _parse_block,
        TryStatement: _parse_try_catch,
        TryCatchClause: _parse_catch,
        ExpressionStatement: _parse_expression_statement,
        ForStatement: _parse_for,
        IfStatement: _parse_if,
        Return: _parse_return,
        Continue: _parse_continue,
        Break: _parse_break,
        Throw: _parse_throw,
        EmitStatement: _parse_emit_statement,
        InlineAssembly: _parse_inline_assembly,
    }

    def _parse_cfg(self, cfg: ASTNode):
        assert isinstance(cfg, Block)

        node = self._new_node(NodeType.ENTRYPOINT, cfg.src)
        self._function.entry_point = node.underlying_node

        if not cfg.statements:
            self._function.is_empty = True
        else:
            self._function.is_empty = False
            self._parse(cfg, node)
            self._remove_incorrect_edges()
            self._remove_alone_endif()

    # endregion
    ###################################################################################
    ###################################################################################
    # region Loops
    ###################################################################################
    ###################################################################################

    def _find_end_loop(self, node: Node, visited: List[Node], counter: int) -> Optional[Node]:
        # counter allows to explore nested loop
        if node in visited:
            return None

        if node.type == NodeType.ENDLOOP:
            if counter == 0:
                return node
            counter -= 1

        # nested loop
        if node.type == NodeType.STARTLOOP:
            counter += 1

        visited = visited + [node]
        for son in node.sons:
            ret = self._find_end_loop(son, visited, counter)
            if ret:
                return ret

        return None

    def _find_start_loop(self, node: Node, visited: List[Node]) -> Optional[Node]:
        if node in visited:
            return None

        if node.type == NodeType.STARTLOOP:
            return node

        visited = visited + [node]
        for father in node.fathers:
            ret = self._find_start_loop(father, visited)
            if ret:
                return ret

        return None

    def _fix_break_node(self, node: Node):
        end_node = self._find_end_loop(node, [], 0)

        if not end_node:
            # If there is not end condition on the loop
            # The exploration will reach a STARTLOOP before reaching the endloop
            # We start with -1 as counter to catch this corner case
            end_node = self._find_end_loop(node, [], -1)
            if not end_node:
                raise ParsingError("Break in no-loop context {}".format(node.function))

        for son in node.sons:
            son.remove_father(node)
        node.set_sons([end_node])
        end_node.add_father(node)

    def _fix_continue_node(self, node: Node):
        start_node = self._find_start_loop(node, [])

        if not start_node:
            raise ParsingError("Continue in no-loop context {}".format(node.node_id))

        for son in node.sons:
            son.remove_father(node)
        node.set_sons([start_node])
        start_node.add_father(node)

    def _fix_try(self, node: Node):
        end_node = next((son for son in node.sons if son.type != NodeType.CATCH), None)
        if end_node:
            for son in node.sons:
                if son.type == NodeType.CATCH:
                    self._fix_catch(son, end_node)

    def _fix_catch(self, node: Node, end_node: Node):
        if not node.sons:
            link_nodes(node, end_node)
        else:
            for son in node.sons:
                if son != end_node:
                    self._fix_catch(son, end_node)

    def _add_param(self, param: VariableDeclaration) -> LocalVariableSolc:

        local_var = LocalVariable()
        local_var.set_function(self._function)
        local_var.set_offset(param.src, self._function.slither)

        local_var_parser = LocalVariableSolc(local_var, param)

        local_var_parser.analyze(self)

        # see https://solidity.readthedocs.io/en/v0.4.24/types.html?highlight=storage%20location#data-location
        if local_var.location == "default":
            local_var.set_location("memory")

        self._add_local_variable(local_var_parser)
        return local_var_parser

    def _parse_params(self, params: ParameterList):
        self.parameters_src.set_offset(params.src, self._function.slither)

        for param in params.params:
            local_var = self._add_param(param)
            self._function.add_parameters(local_var.underlying_variable)

    def _parse_returns(self, returns: ParameterList):
        self.returns_src.set_offset(returns.src, self._function.slither)

        for ret in returns.params:
            local_var = self._add_param(ret)
            self._function.add_return(local_var.underlying_variable)

    def _parse_modifier(self, modifier: ModifierInvocation):
        m = parse_expression(modifier, self)
        # self._expression_modifiers.append(m)

        # Do not parse modifier nodes for interfaces
        if not self._function.is_implemented:
            return

        for m in ExportValues(m).result():
            if isinstance(m, Function):
                node_parser = self._new_node(NodeType.EXPRESSION, modifier.src)
                node_parser.add_unparsed_expression(modifier)
                # The latest entry point is the entry point, or the latest modifier call
                if self._function.modifiers:
                    latest_entry_point = self._function.modifiers_statements[-1].nodes[-1]
                else:
                    latest_entry_point = self._function.entry_point
                insert_node(latest_entry_point, node_parser.underlying_node)
                self._function.add_modifier(
                    ModifierStatements(
                        modifier=m,
                        entry_point=latest_entry_point,
                        nodes=[latest_entry_point, node_parser.underlying_node],
                    )
                )

            elif isinstance(m, Contract):
                node_parser = self._new_node(NodeType.EXPRESSION, modifier.src)
                node_parser.add_unparsed_expression(modifier)
                # The latest entry point is the entry point, or the latest constructor call
                if self._function.explicit_base_constructor_calls_statements:
                    latest_entry_point = self._function.explicit_base_constructor_calls_statements[
                        -1
                    ].nodes[-1]
                else:
                    latest_entry_point = self._function.entry_point
                insert_node(latest_entry_point, node_parser.underlying_node)
                self._function.add_explicit_base_constructor_calls_statements(
                    ModifierStatements(
                        modifier=m,
                        entry_point=latest_entry_point,
                        nodes=[latest_entry_point, node_parser.underlying_node],
                    )
                )

    # endregion
    ###################################################################################
    ###################################################################################
    # region Edges
    ###################################################################################
    ###################################################################################

    def _remove_incorrect_edges(self):
        for node in self._node_to_nodesolc:
            if node.type in [NodeType.RETURN, NodeType.THROW]:
                for son in node.sons:
                    son.remove_father(node)
                node.set_sons([])
            if node.type in [NodeType.BREAK]:
                self._fix_break_node(node)
            if node.type in [NodeType.CONTINUE]:
                self._fix_continue_node(node)
            if node.type in [NodeType.TRY]:
                self._fix_try(node)

    def _remove_alone_endif(self):
        """
        Can occur on:
        if(..){
            return
        }
        else{
            return
        }

        Iterate until a fix point to remove the ENDIF node
        creates on the following pattern
        if(){
            return
        }
        else if(){
            return
        }
        """
        prev_nodes = []
        while set(prev_nodes) != set(self._node_to_nodesolc.keys()):
            prev_nodes = self._node_to_nodesolc.keys()
            to_remove: List[Node] = []
            for node in self._node_to_nodesolc:
                if node.type == NodeType.ENDIF and not node.fathers:
                    for son in node.sons:
                        son.remove_father(node)
                    node.set_sons([])
                    to_remove.append(node)
            self._function.nodes = [n for n in self._function.nodes if n not in to_remove]
            for remove in to_remove:
                if remove in self._node_to_nodesolc:
                    del self._node_to_nodesolc[remove]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Ternary
    ###################################################################################
    ###################################################################################

    def _filter_ternary(self) -> bool:
        ternary_found = True
        updated = False
        while ternary_found:
            ternary_found = False
            for node in self._node_to_nodesolc:
                has_cond = HasConditional(node.expression)
                if has_cond.result():
                    st = SplitTernaryExpression(node.expression)
                    condition = st.condition
                    if not condition:
                        raise ParsingError(
                            f"Incorrect ternary conversion {node.expression} {node.source_mapping_str}"
                        )
                    true_expr = st.true_expression
                    false_expr = st.false_expression
                    self._split_ternary_node(node, condition, true_expr, false_expr)
                    ternary_found = True
                    updated = True
                    break
        return updated

    def _split_ternary_node(
            self,
            node: Node,
            condition: "Expression",
            true_expr: "Expression",
            false_expr: "Expression",
    ):
        condition_node = self._new_node(NodeType.IF, node.source_mapping)
        condition_node.underlying_node.add_expression(condition)
        condition_node.analyze_expressions(self)

        if node.type == NodeType.VARIABLE:
            condition_node.underlying_node.add_variable_declaration(node.variable_declaration)

        true_node_parser = self._new_node(NodeType.EXPRESSION, node.source_mapping)
        if node.type == NodeType.VARIABLE:
            assert isinstance(true_expr, AssignmentOperation)
            # true_expr = true_expr.expression_right
        elif node.type == NodeType.RETURN:
            true_node_parser.underlying_node.type = NodeType.RETURN
        true_node_parser.underlying_node.add_expression(true_expr)
        true_node_parser.analyze_expressions(self)

        false_node_parser = self._new_node(NodeType.EXPRESSION, node.source_mapping)
        if node.type == NodeType.VARIABLE:
            assert isinstance(false_expr, AssignmentOperation)
        elif node.type == NodeType.RETURN:
            false_node_parser.underlying_node.type = NodeType.RETURN
            # false_expr = false_expr.expression_right
        false_node_parser.underlying_node.add_expression(false_expr)
        false_node_parser.analyze_expressions(self)

        endif_node = self._new_node(NodeType.ENDIF, node.source_mapping)

        for father in node.fathers:
            father.remove_son(node)
            father.add_son(condition_node.underlying_node)
            condition_node.underlying_node.add_father(father)

        for son in node.sons:
            son.remove_father(node)
            son.add_father(endif_node.underlying_node)
            endif_node.underlying_node.add_son(son)

        link_underlying_nodes(condition_node, true_node_parser)
        link_underlying_nodes(condition_node, false_node_parser)

        if true_node_parser.underlying_node.type not in [
            NodeType.THROW,
            NodeType.RETURN,
        ]:
            link_underlying_nodes(true_node_parser, endif_node)
        if false_node_parser.underlying_node.type not in [
            NodeType.THROW,
            NodeType.RETURN,
        ]:
            link_underlying_nodes(false_node_parser, endif_node)

        self._function.nodes = [n for n in self._function.nodes if n.node_id != node.node_id]
        del self._node_to_nodesolc[node]

    # endregion
