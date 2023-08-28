import logging
from typing import Dict, Optional, Union, List, TYPE_CHECKING, Tuple, Set

from slither.core.cfg.node import NodeType, link_nodes, insert_node, Node
from slither.core.cfg.scope import Scope
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import (
    Function,
    FunctionType,
)
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions import AssignmentOperation
from slither.core.source_mapping.source_mapping import Source
from slither.core.variables.local_variable import LocalVariable
from slither.vyper_parsing.cfg.node import NodeVyper
from slither.solc_parsing.exceptions import ParsingError
from slither.vyper_parsing.variables.local_variable import LocalVariableVyper
from slither.vyper_parsing.ast.types import *

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit


def link_underlying_nodes(node1: NodeVyper, node2: NodeVyper):
    link_nodes(node1.underlying_node, node2.underlying_node)


class FunctionVyper:
    def __init__(
        self,
        function: Function,
        function_data: Dict,
        contract_parser: "ContractVyper",
    ) -> None:
        self._node_to_NodeVyper: Dict[Node, NodeVyper] = {}

        self._function = function
        print(function_data.name)
        print(function_data)
        self._function.name = function_data.name
        self._function.id = function_data.node_id

        self._local_variables_parser: List = []
        self._contract_parser = contract_parser

        for decorator in function_data.decorators:
            if not hasattr(decorator, "id"):
                continue  # TODO isinstance Name
            if decorator.id in ["external", "public", "internal"]:
                self._function.visibility = decorator.id
            elif decorator.id == "view":
                self._function.view = True
            elif decorator.id == "pure":
                self._function.pure = True
            elif decorator.id == "payable":
                self._function.payable = True
            else:
                raise ValueError(f"Unknown decorator {decorator.id}")
        # Interfaces do not have decorators and are external
        if self._function._visibility is None:
            self._function.visibility = "external"
        self._functionNotParsed = function_data
        self._params_was_analyzed = False
        self._content_was_analyzed = False

        # self._counter_scope_local_variables = 0
        # # variable renamed will map the solc id
        # # to the variable. It only works for compact format
        # # Later if an expression provides the referencedDeclaration attr
        # # we can retrieve the variable
        # # It only matters if two variables have the same name in the function
        # # which is only possible with solc > 0.5
        # self._variables_renamed: Dict[
        #     int, Union[LocalVariableVyper, LocalVariableInitFromTupleSolc]
        # ] = {}

        self._analyze_function_type()

        # self._node_to_NodeVyper: Dict[Node, NodeVyper] = {}
        # self._node_to_yulobject: Dict[Node, YulBlock] = {}

        # self._local_variables_parser: List[
        #     Union[LocalVariableVyper, LocalVariableInitFromTupleSolc]
        # ] = []

        if function_data.doc_string is not None:
            function.has_documentation = True

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
        # If two local variables have the same name
        # We add a suffix to the new variable
        # This is done to prevent collision during SSA translation
        # Use of while in case of collision
        # In the worst case, the name will be really long
        # TODO no shadowing?
        # if local_var_parser.underlying_variable.name:
        #     known_variables = [v.name for v in self._function.variables]
        #     while local_var_parser.underlying_variable.name in known_variables:
        #         local_var_parser.underlying_variable.name += (
        #             f"_scope_{self._counter_scope_local_variables}"
        #         )
        #         self._counter_scope_local_variables += 1
        #         known_variables = [v.name for v in self._function.variables]
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

        if body:
            self._function.is_implemented = True
            self._parse_cfg(body)

        for local_var_parser in self._local_variables_parser:
            local_var_parser.analyze(self._function)

        for node_parser in self._node_to_NodeVyper.values():
            node_parser.analyze_expressions(self._function)



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

    def _parse_cfg(self, cfg: Dict) -> None:


        curr_node = self._new_node(NodeType.ENTRYPOINT, "-1:-1:-1", self.underlying_function)
        self._function.entry_point = curr_node.underlying_node
        scope = Scope(True, False, self.underlying_function)

        if cfg:
            self._function.is_empty = False
            for expr in cfg:
                def parse_statement(curr_node, expr):
                    if isinstance(expr, AnnAssign):
                        local_var = LocalVariable()
                        local_var.set_function(self._function)
                        local_var.set_offset(expr.src, self._function.compilation_unit)

                        local_var_parser = LocalVariableVyper(local_var, expr)
                        self._add_local_variable(local_var_parser)

                        new_node = self._new_node(NodeType.VARIABLE, expr.src, scope)
                        if expr.value is not None:
                            new_node.add_unparsed_expression(expr.value)
                        new_node.underlying_node.add_variable_declaration(local_var)
                        link_underlying_nodes(curr_node, new_node)

                        curr_node = new_node

                    elif isinstance(expr, (AugAssign, Assign)):
                        new_node = self._new_node(NodeType.EXPRESSION, expr.src, scope)
                        new_node.add_unparsed_expression(expr)
                        link_underlying_nodes(curr_node, new_node)

                    # elif isinstance(expr, Assign):
                    #     new_node = self._new_node(NodeType.EXPRESSION, expr.src, scope)
                    #     new_node.add_unparsed_expression(expr.target)
                    #     new_node.add_unparsed_expression(expr.value)
                    #     link_underlying_nodes(curr_node, new_node)

                    elif isinstance(expr, For):

                        node_startLoop = self._new_node(NodeType.STARTLOOP, expr.src, scope)

                        local_var = LocalVariable()
                        local_var.set_function(self._function)
                        local_var.set_offset(expr.src, self._function.compilation_unit)

                        counter_var = AnnAssign(expr.target.src, expr.target.node_id, target=Name("-1:-1:-1", -1, "counter_var"), annotation=Name("-1:-1:-1", -1, "uint256"), value=Int("-1:-1:-1", -1, 0))
                        local_var_parser = LocalVariableVyper(local_var, counter_var)
                        self._add_local_variable(local_var_parser)
                        new_node = self._new_node(NodeType.VARIABLE, expr.src, scope)
                        new_node.add_unparsed_expression(counter_var.value)
                        new_node.underlying_node.add_variable_declaration(local_var)

                        if isinstance(expr.iter, (Attribute,Name)):
                            # HACK  
                            # The loop variable is not annotated so we infer its type by looking at the type of the iterator
                            if isinstance(expr.iter, Attribute): # state
                                iter_expr = expr.iter
                                loop_iterator = list(filter(lambda x: x._variable.name == iter_expr.attr,  self._contract_parser._variables_parser))[0]

                            else: # local
                                iter_expr = expr.iter
                                loop_iterator = list(filter(lambda x: x._variable.name == iter_expr.id, self._local_variables_parser))[0]

                            # TODO use expr.src instead of -1:-1:1?
                            cond_expr = Compare("-1:-1:-1", -1, left=Name("-1:-1:-1", -1, "counter_var"), op="<=", right=Call("-1:-1:-1", -1, func=Name("-1:-1:-1", -1, "len"), args=[iter_expr], keywords=[], keyword=None))
                            node_condition = self._new_node(NodeType.IFLOOP, expr.src, scope)
                            node_condition.add_unparsed_expression(cond_expr)

                            # TODO this should go in the body of the loop: expr.body.insert(0, ...)
                            if loop_iterator._elem_to_parse.value.id == "DynArray":
                                loop_var_annotation = loop_iterator._elem_to_parse.slice.value.elements[0]
                            else:
                                loop_var_annotation = loop_iterator._elem_to_parse.value

                            value = Subscript("-1:-1:-1", -1, value=Name("-1:-1:-1", -1, loop_iterator._variable.name), slice=Index("-1:-1:-1", -1, value=Name("-1:-1:-1", -1, "counter_var")))
                            loop_var = AnnAssign(expr.target.src, expr.target.node_id, target=expr.target, annotation=loop_var_annotation, value=value)
                            local_var = LocalVariable()
                            local_var.set_function(self._function)
                            local_var.set_offset(expr.src, self._function.compilation_unit)
                            local_var_parser = LocalVariableVyper(local_var, loop_var)
                            self._add_local_variable(local_var_parser)
                            new_node = self._new_node(NodeType.VARIABLE, expr.src, scope)
                            new_node.add_unparsed_expression(loop_var.value)
                            new_node.underlying_node.add_variable_declaration(local_var)

                        elif isinstance(expr.iter, Call):
                            range_val = expr.iter.args[0]
                            cond_expr = Compare("-1:-1:-1", -1, left=Name("-1:-1:-1", -1, "counter_var"), op="<=", right=range_val)
                            loop_var = AnnAssign(expr.target.src, expr.target.node_id, target=expr.target, annotation=Name("-1:-1:-1", -1, "uint256"), value=Name("-1:-1:-1", -1, "counter_var"))
                            local_var = LocalVariable()
                            local_var.set_function(self._function)
                            local_var.set_offset(expr.src, self._function.compilation_unit)
                            local_var_parser = LocalVariableVyper(local_var, loop_var)
                            self._add_local_variable(local_var_parser)
                            new_node = self._new_node(NodeType.VARIABLE, expr.src, scope)
                            new_node.add_unparsed_expression(loop_var.value)
                            new_node.underlying_node.add_variable_declaration(local_var)
                        else:
                            print(expr)
                            raise NotImplementedError
                        # assert False
                        node_endLoop = self._new_node(NodeType.ENDLOOP, expr.src, scope)



                        # link_underlying_nodes(node_startLoop, node_condition)
                        for stmt in expr.body:
                            parse_statement(curr_node, stmt)

                        # link_underlying_nodes(curr_node, new_node)

                    elif isinstance(expr, Continue):
                        pass
                    elif isinstance(expr, Break):
                        pass
                    elif isinstance(expr, Return):
                        node_parser = self._new_node(NodeType.RETURN, expr.src, scope)
                        if expr.value is not None:
                            node_parser.add_unparsed_expression(expr.value)

                        pass
                    elif isinstance(expr, Assert):
                        new_node = self._new_node(NodeType.EXPRESSION, expr.src, scope)
                        new_node.add_unparsed_expression(expr)



                    elif isinstance(expr, Log):
                        new_node = self._new_node(NodeType.EXPRESSION, expr.src, scope)
                        new_node.add_unparsed_expression(expr.value)
                        pass
                    elif isinstance(expr, If):
                        new_node = self._new_node(NodeType.IF, expr.test.src, scope)
                        new_node.add_unparsed_expression(expr.test)

                        for stmt in expr.body:
                            parse_statement(new_node, stmt)

                        for stmt in expr.orelse:
                            parse_statement(new_node, stmt)

                        pass
                    elif isinstance(expr, Expr):
                        pass
                    elif isinstance(expr, Pass):
                        pass
                    elif isinstance(expr, Raise):
                        print(expr)
                        # assert False
                        pass
                    else:
                        print(f"isinstance(expr, {expr.__class__.__name__})")
                        assert False
                    return curr_node
                curr_node = parse_statement(curr_node, expr)
            # self._parse_block(cfg, node, self.underlying_function)
        else:
            self._function.is_empty = True

    # endregion
    ###################################################################################
    ###################################################################################

    def _add_param(self, param: Arg, initialized: bool = False) -> LocalVariableVyper:

        local_var = LocalVariable()
        local_var.set_function(self._function)
        local_var.set_offset(param.src, self._function.compilation_unit)
        print("add_param", param)
        local_var_parser = LocalVariableVyper(local_var, param)

        if initialized:
            local_var.initialized = True

        # see https://solidity.readthedocs.io/en/v0.4.24/types.html?highlight=storage%20location#data-location
        if local_var.location == "default":
            local_var.set_location("memory")

        self._add_local_variable(local_var_parser)
        return local_var_parser

    def _parse_params(self, params: Arguments):

        print(params)
        self._function.parameters_src().set_offset(params.src, self._function.compilation_unit)

        for param in params.args:
            local_var = self._add_param(param)
            self._function.add_parameters(local_var.underlying_variable)

    def _parse_returns(self, returns: Union[Name, Tuple, Subscript]):

        print(returns)
        self._function.returns_src().set_offset(returns.src, self._function.compilation_unit)
        # Only the type of the arg is given, not a name. We create an an `Arg` with an empty name
        # so that the function has the correct return type in its signature but doesn't clash with 
        # other identifiers during name resolution (`find_variable`).
        if isinstance(returns, (Name, Subscript)):
            local_var = self._add_param(Arg(returns.src, returns.node_id, "", annotation=returns))
            self._function.add_return(local_var.underlying_variable)
        else:
            assert isinstance(returns, Tuple)
            for ret in returns.elements:
                local_var = self._add_param(Arg(ret.src, ret.node_id, "", annotation=ret))
                self._function.add_return(local_var.underlying_variable)

    ###################################################################################
    ###################################################################################
