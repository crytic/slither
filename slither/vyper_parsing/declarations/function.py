from typing import Dict, Union, List, TYPE_CHECKING

from slither.core.cfg.node import NodeType, link_nodes, Node
from slither.core.cfg.scope import Scope
from slither.core.declarations.function import (
    Function,
    FunctionType,
)
from slither.core.declarations.function import ModifierStatements
from slither.core.declarations.modifier import Modifier
from slither.core.source_mapping.source_mapping import Source
from slither.core.variables.local_variable import LocalVariable
from slither.vyper_parsing.cfg.node import NodeVyper
from slither.solc_parsing.exceptions import ParsingError
from slither.vyper_parsing.variables.local_variable import LocalVariableVyper
from slither.vyper_parsing.ast.types import (
    Int,
    Call,
    Attribute,
    Name,
    Tuple as TupleVyper,
    ASTNode,
    AnnAssign,
    FunctionDef,
    Return,
    Assert,
    Compare,
    Log,
    Subscript,
    If,
    Pass,
    Assign,
    AugAssign,
    Raise,
    Expr,
    For,
    Index,
    Arg,
    Arguments,
    Continue,
    Break,
)

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.vyper_parsing.declarations.contract import ContractVyper


def link_underlying_nodes(node1: NodeVyper, node2: NodeVyper):
    link_nodes(node1.underlying_node, node2.underlying_node)


class FunctionVyper:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        function: Function,
        function_data: FunctionDef,
        contract_parser: "ContractVyper",
    ) -> None:

        self._function = function
        self._function.name = function_data.name
        self._function.id = function_data.node_id
        self._functionNotParsed = function_data
        self._decoratorNotParsed = None
        self._local_variables_parser: List[LocalVariableVyper] = []
        self._variables_renamed = []
        self._contract_parser = contract_parser
        self._node_to_NodeVyper: Dict[Node, NodeVyper] = {}

        for decorator in function_data.decorators:
            if isinstance(decorator, Call):
                # TODO handle multiple
                self._decoratorNotParsed = decorator
            elif isinstance(decorator, Name):
                if decorator.id in ["external", "public", "internal"]:
                    self._function.visibility = decorator.id
                elif decorator.id == "view":
                    self._function.view = True
                elif decorator.id == "pure":
                    self._function.pure = True
                elif decorator.id == "payable":
                    self._function.payable = True
                elif decorator.id == "nonpayable":
                    self._function.payable = False
            else:
                raise ValueError(f"Unknown decorator {decorator.id}")

        # Interfaces do not have decorators and are external
        if self._function._visibility is None:
            self._function.visibility = "external"

        self._params_was_analyzed = False
        self._content_was_analyzed = False
        self._counter_scope_local_variables = 0

        if function_data.doc_string is not None:
            function.has_documentation = True

        self._analyze_function_type()

    @property
    def underlying_function(self) -> Function:
        return self._function

    @property
    def compilation_unit(self) -> "SlitherCompilationUnit":
        return self._function.compilation_unit

    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################

    @property
    def variables_renamed(
        self,
    ) -> Dict[int, LocalVariableVyper]:
        return self._variables_renamed

    def _add_local_variable(self, local_var_parser: LocalVariableVyper) -> None:
        # Ensure variables name are unique for SSA conversion
        # This should not apply to actual Vyper variables currently
        # but is necessary if we have nested loops where we've created artificial variables e.g. counter_var
        if local_var_parser.underlying_variable.name:
            known_variables = [v.name for v in self._function.variables]
            while local_var_parser.underlying_variable.name in known_variables:
                local_var_parser.underlying_variable.name += (
                    f"_scope_{self._counter_scope_local_variables}"
                )
                self._counter_scope_local_variables += 1
                known_variables = [v.name for v in self._function.variables]
        # TODO no reference ID
        # if local_var_parser.reference_id is not None:
        #     self._variables_renamed[local_var_parser.reference_id] = local_var_parser
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
    def function_not_parsed(self) -> Dict:
        return self._functionNotParsed

    def _analyze_function_type(self) -> None:
        if self._function.name == "__init__":
            self._function.function_type = FunctionType.CONSTRUCTOR
        elif self._function.name == "__default__":
            self._function.function_type = FunctionType.FALLBACK
        else:
            self._function.function_type = FunctionType.NORMAL

    def analyze_params(self) -> None:
        if self._params_was_analyzed:
            return

        self._params_was_analyzed = True

        params = self._functionNotParsed.args
        returns = self._functionNotParsed.returns

        if params:
            self._parse_params(params)
        if returns:
            self._parse_returns(returns)

    def analyze_content(self) -> None:
        if self._content_was_analyzed:
            return

        self._content_was_analyzed = True

        body = self._functionNotParsed.body

        if body and not isinstance(body[0], Pass):
            self._function.is_implemented = True
            self._function.is_empty = False
            self._parse_cfg(body)
            self._update_reachability(self._function.entry_point)
        else:
            self._function.is_implemented = False
            self._function.is_empty = True

        for local_var_parser in self._local_variables_parser:
            local_var_parser.analyze(self._function)

        for node_parser in self._node_to_NodeVyper.values():
            node_parser.analyze_expressions(self._function)

        self._analyze_decorator()

    def _analyze_decorator(self) -> None:
        if not self._decoratorNotParsed:
            return

        decorator = self._decoratorNotParsed
        if decorator.args:
            name = f"{decorator.func.id}({decorator.args[0].value})"
        else:
            name = decorator.func.id

        contract = self._contract_parser.underlying_contract
        compilation_unit = self._contract_parser.underlying_contract.compilation_unit
        modifier = Modifier(compilation_unit)
        modifier.name = name
        modifier.set_offset(decorator.src, compilation_unit)
        modifier.set_contract(contract)
        modifier.set_contract_declarer(contract)
        latest_entry_point = self._function.entry_point
        self._function.add_modifier(
            ModifierStatements(
                modifier=modifier,
                entry_point=latest_entry_point,
                nodes=[latest_entry_point],
            )
        )

    # endregion
    ###################################################################################
    ###################################################################################
    # region Nodes
    ###################################################################################
    ###################################################################################

    def _new_node(
        self, node_type: NodeType, src: Union[str, Source], scope: Union[Scope, "Function"]
    ) -> NodeVyper:
        node = self._function.new_node(node_type, src, scope)
        node_parser = NodeVyper(node)
        self._node_to_NodeVyper[node] = node_parser
        return node_parser

    # endregion
    ###################################################################################
    ###################################################################################
    # region Parsing function
    ###################################################################################
    ###################################################################################
    def _update_reachability(self, node: Node) -> None:
        if node.is_reachable:
            return
        node.set_is_reachable(True)
        for son in node.sons:
            self._update_reachability(son)

    # pylint: disable=too-many-branches,too-many-statements,protected-access,too-many-locals
    def _parse_cfg(self, cfg: List[ASTNode]) -> None:

        entry_node = self._new_node(NodeType.ENTRYPOINT, "-1:-1:-1", self.underlying_function)
        self._function.entry_point = entry_node.underlying_node
        scope = Scope(True, False, self.underlying_function)

        def parse_statement(
            curr_node: NodeVyper,
            expr: ASTNode,
            continue_destination=None,
            break_destination=None,
        ) -> NodeVyper:
            if isinstance(expr, AnnAssign):
                local_var = LocalVariable()
                local_var.set_function(self._function)
                local_var.set_offset(expr.src, self._function.compilation_unit)

                local_var_parser = LocalVariableVyper(local_var, expr)
                self._add_local_variable(local_var_parser)

                new_node = self._new_node(NodeType.VARIABLE, expr.src, scope)
                if expr.value is not None:
                    local_var.initialized = True
                    new_node.add_unparsed_expression(expr.value)
                new_node.underlying_node.add_variable_declaration(local_var)
                link_underlying_nodes(curr_node, new_node)

                curr_node = new_node

            elif isinstance(expr, (AugAssign, Assign)):
                new_node = self._new_node(NodeType.EXPRESSION, expr.src, scope)
                new_node.add_unparsed_expression(expr)
                link_underlying_nodes(curr_node, new_node)

                curr_node = new_node

            elif isinstance(expr, Expr):
                # TODO This is a workaround to handle Vyper putting payable/view in the function body... https://github.com/vyperlang/vyper/issues/3578
                if not isinstance(expr.value, Name):
                    new_node = self._new_node(NodeType.EXPRESSION, expr.src, scope)
                    new_node.add_unparsed_expression(expr.value)
                    link_underlying_nodes(curr_node, new_node)

                    curr_node = new_node

            elif isinstance(expr, For):

                node_startLoop = self._new_node(NodeType.STARTLOOP, expr.src, scope)
                node_endLoop = self._new_node(NodeType.ENDLOOP, expr.src, scope)

                link_underlying_nodes(curr_node, node_startLoop)

                local_var = LocalVariable()
                local_var.set_function(self._function)
                local_var.set_offset(expr.src, self._function.compilation_unit)

                counter_var = AnnAssign(
                    expr.target.src,
                    expr.target.node_id,
                    target=Name("-1:-1:-1", -1, "counter_var"),
                    annotation=Name("-1:-1:-1", -1, "uint256"),
                    value=Int("-1:-1:-1", -1, 0),
                )
                local_var_parser = LocalVariableVyper(local_var, counter_var)
                self._add_local_variable(local_var_parser)
                counter_node = self._new_node(NodeType.VARIABLE, expr.src, scope)
                local_var.initialized = True
                counter_node.add_unparsed_expression(counter_var.value)
                counter_node.underlying_node.add_variable_declaration(local_var)

                link_underlying_nodes(node_startLoop, counter_node)

                node_condition = None
                if isinstance(expr.iter, (Attribute, Name)):
                    # HACK
                    # The loop variable is not annotated so we infer its type by looking at the type of the iterator
                    if isinstance(expr.iter, Attribute):  # state variable
                        iter_expr = expr.iter
                        loop_iterator = list(
                            filter(
                                lambda x: x._variable.name == iter_expr.attr,
                                self._contract_parser._variables_parser,
                            )
                        )[0]

                    else:  # local variable
                        iter_expr = expr.iter
                        loop_iterator = list(
                            filter(
                                lambda x: x._variable.name == iter_expr.id,
                                self._local_variables_parser,
                            )
                        )[0]

                    # TODO use expr.src instead of -1:-1:1?
                    cond_expr = Compare(
                        "-1:-1:-1",
                        -1,
                        left=Name("-1:-1:-1", -1, "counter_var"),
                        op="<=",
                        right=Call(
                            "-1:-1:-1",
                            -1,
                            func=Name("-1:-1:-1", -1, "len"),
                            args=[iter_expr],
                            keywords=[],
                            keyword=None,
                        ),
                    )
                    node_condition = self._new_node(NodeType.IFLOOP, expr.src, scope)
                    node_condition.add_unparsed_expression(cond_expr)

                    if loop_iterator._elem_to_parse.value.id == "DynArray":
                        loop_var_annotation = loop_iterator._elem_to_parse.slice.value.elements[0]
                    else:
                        loop_var_annotation = loop_iterator._elem_to_parse.value

                    value = Subscript(
                        "-1:-1:-1",
                        -1,
                        value=Name("-1:-1:-1", -1, loop_iterator._variable.name),
                        slice=Index("-1:-1:-1", -1, value=Name("-1:-1:-1", -1, "counter_var")),
                    )
                    loop_var = AnnAssign(
                        expr.target.src,
                        expr.target.node_id,
                        target=expr.target,
                        annotation=loop_var_annotation,
                        value=value,
                    )

                elif isinstance(expr.iter, Call):  # range
                    range_val = expr.iter.args[0]
                    cond_expr = Compare(
                        "-1:-1:-1",
                        -1,
                        left=Name("-1:-1:-1", -1, "counter_var"),
                        op="<=",
                        right=range_val,
                    )
                    node_condition = self._new_node(NodeType.IFLOOP, expr.src, scope)
                    node_condition.add_unparsed_expression(cond_expr)
                    loop_var = AnnAssign(
                        expr.target.src,
                        expr.target.node_id,
                        target=expr.target,
                        annotation=Name("-1:-1:-1", -1, "uint256"),
                        value=Name("-1:-1:-1", -1, "counter_var"),
                    )

                else:
                    raise NotImplementedError

                # After creating condition node, we link it declaration of the loop variable
                link_underlying_nodes(counter_node, node_condition)

                # Create an expression for the loop increment (counter_var += 1)
                loop_increment = AugAssign(
                    "-1:-1:-1",
                    -1,
                    target=Name("-1:-1:-1", -1, "counter_var"),
                    op="+=",
                    value=Int("-1:-1:-1", -1, 1),
                )
                node_increment = self._new_node(NodeType.EXPRESSION, expr.src, scope)
                node_increment.add_unparsed_expression(loop_increment)
                link_underlying_nodes(node_increment, node_condition)

                continue_destination = node_increment
                break_destination = node_endLoop

                # We assign the index variable or range variable in the loop body on each iteration
                expr.body.insert(0, loop_var)
                body_node = None
                new_node = node_condition
                for stmt in expr.body:
                    body_node = parse_statement(
                        new_node, stmt, continue_destination, break_destination
                    )
                    new_node = body_node

                if body_node is not None:
                    link_underlying_nodes(body_node, node_increment)

                link_underlying_nodes(node_condition, node_endLoop)

                curr_node = node_endLoop

            elif isinstance(expr, Continue):
                new_node = self._new_node(NodeType.CONTINUE, expr.src, scope)
                link_underlying_nodes(curr_node, new_node)
                link_underlying_nodes(new_node, continue_destination)

            elif isinstance(expr, Break):
                new_node = self._new_node(NodeType.BREAK, expr.src, scope)
                link_underlying_nodes(curr_node, new_node)
                link_underlying_nodes(new_node, break_destination)

            elif isinstance(expr, Return):
                new_node = self._new_node(NodeType.RETURN, expr.src, scope)
                if expr.value is not None:
                    new_node.add_unparsed_expression(expr.value)

                link_underlying_nodes(curr_node, new_node)
                curr_node = new_node

            elif isinstance(expr, Assert):
                new_node = self._new_node(NodeType.EXPRESSION, expr.src, scope)
                new_node.add_unparsed_expression(expr)

                link_underlying_nodes(curr_node, new_node)
                curr_node = new_node

            elif isinstance(expr, Log):
                new_node = self._new_node(NodeType.EXPRESSION, expr.src, scope)
                new_node.add_unparsed_expression(expr.value)

                link_underlying_nodes(curr_node, new_node)
                curr_node = new_node

            elif isinstance(expr, If):
                condition_node = self._new_node(NodeType.IF, expr.test.src, scope)
                condition_node.add_unparsed_expression(expr.test)

                endIf_node = self._new_node(NodeType.ENDIF, expr.src, scope)

                true_node = None
                new_node = condition_node
                for stmt in expr.body:
                    true_node = parse_statement(
                        new_node, stmt, continue_destination, break_destination
                    )
                    new_node = true_node

                link_underlying_nodes(true_node, endIf_node)

                false_node = None
                new_node = condition_node
                for stmt in expr.orelse:
                    false_node = parse_statement(
                        new_node, stmt, continue_destination, break_destination
                    )
                    new_node = false_node

                if false_node is not None:
                    link_underlying_nodes(false_node, endIf_node)

                else:
                    link_underlying_nodes(condition_node, endIf_node)

                link_underlying_nodes(curr_node, condition_node)
                curr_node = endIf_node

            elif isinstance(expr, Pass):
                pass
            elif isinstance(expr, Raise):
                new_node = self._new_node(NodeType.EXPRESSION, expr.src, scope)
                new_node.add_unparsed_expression(expr)
                link_underlying_nodes(curr_node, new_node)
                curr_node = new_node

            else:
                raise ParsingError(f"Statement not parsed {expr.__class__.__name__} {expr}")

            return curr_node

        curr_node = entry_node
        for expr in cfg:
            curr_node = parse_statement(curr_node, expr)

    # endregion
    ###################################################################################
    ###################################################################################

    def _add_param(self, param: Arg, initialized: bool = False) -> LocalVariableVyper:

        local_var = LocalVariable()
        local_var.set_function(self._function)
        local_var.set_offset(param.src, self._function.compilation_unit)
        local_var_parser = LocalVariableVyper(local_var, param)

        if initialized:
            local_var.initialized = True

        if local_var.location == "default":
            local_var.set_location("memory")

        self._add_local_variable(local_var_parser)
        return local_var_parser

    def _parse_params(self, params: Arguments):

        self._function.parameters_src().set_offset(params.src, self._function.compilation_unit)
        if params.defaults:
            self._function._default_args_as_expressions = params.defaults
        for param in params.args:
            local_var = self._add_param(param)
            self._function.add_parameters(local_var.underlying_variable)

    def _parse_returns(self, returns: Union[Name, TupleVyper, Subscript]):

        self._function.returns_src().set_offset(returns.src, self._function.compilation_unit)
        # Only the type of the arg is given, not a name. We create an an `Arg` with an empty name
        # so that the function has the correct return type in its signature but doesn't clash with
        # other identifiers during name resolution (`find_variable`).
        if isinstance(returns, (Name, Subscript)):
            local_var = self._add_param(Arg(returns.src, returns.node_id, "", annotation=returns))
            self._function.add_return(local_var.underlying_variable)
        else:
            assert isinstance(returns, TupleVyper)
            for ret in returns.elements:
                local_var = self._add_param(Arg(ret.src, ret.node_id, "", annotation=ret))
                self._function.add_return(local_var.underlying_variable)

    ###################################################################################
    ###################################################################################
