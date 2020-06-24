"""
"""
import logging
from typing import Dict, Optional, Union, List, TYPE_CHECKING

from slither.core.cfg.node import NodeType, link_nodes, insert_node, Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function, ModifierStatements, FunctionType

from slither.core.expressions import AssignmentOperation
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple

from slither.solc_parsing.cfg.node import NodeSolc
from slither.solc_parsing.expressions.expression_parsing import parse_expression
from slither.solc_parsing.variables.local_variable import LocalVariableSolc
from slither.solc_parsing.variables.local_variable_init_from_tuple import (
    LocalVariableInitFromTupleSolc,
)
from slither.solc_parsing.variables.variable_declaration import MultipleVariablesDeclaration
from slither.solc_parsing.yul.parse_yul import YulObject
from slither.utils.expression_manipulations import SplitTernaryExpression
from slither.visitors.expression.export_values import ExportValues
from slither.visitors.expression.has_conditional import HasConditional
from slither.solc_parsing.exceptions import ParsingError
from slither.core.source_mapping.source_mapping import SourceMapping

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression
    from slither.solc_parsing.declarations.contract import ContractSolc
    from slither.solc_parsing.slitherSolc import SlitherSolc
    from slither.core.slither_core import SlitherCore

LOGGER = logging.getLogger("FunctionSolc")


def link_underlying_nodes(node1: NodeSolc, node2: NodeSolc):
    link_nodes(node1.underlying_node, node2.underlying_node)


class FunctionSolc:
    """
    """

    # elems = [(type, name)]

    def __init__(
        self, function: Function, function_data: Dict, contract_parser: "ContractSolc",
    ):
        self._slither_parser: "SlitherSolc" = contract_parser.slither_parser
        self._contract_parser = contract_parser
        self._function = function

        # Only present if compact AST
        self._referenced_declaration: Optional[int] = None
        if self.is_compact_ast:
            self._function.name = function_data["name"]
            if "id" in function_data:
                self._referenced_declaration = function_data["id"]
                self._function.id = function_data["id"]
        else:
            self._function.name = function_data["attributes"][self.get_key()]
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
        self._node_to_yulobject: Dict[Node, YulObject] = dict()

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

    def get_key(self) -> str:
        return self._slither_parser.get_key()

    def get_children(self, key: str) -> str:
        if self.is_compact_ast:
            return key
        return "children"

    @property
    def is_compact_ast(self):
        return self._slither_parser.is_compact_ast

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
            while local_var_parser.underlying_variable.name in self._function.variables:
                local_var_parser.underlying_variable.name += "_scope_{}".format(
                    self._counter_scope_local_variables
                )
                self._counter_scope_local_variables += 1
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
    def function_not_parsed(self) -> Dict:
        return self._functionNotParsed

    def _analyze_type(self):
        """
        Analyz the type of the function
        Myst be called in the constructor as the name might change according to the function's type
        For example both the fallback and the receiver will have an empty name
        :return:
        """
        if self.is_compact_ast:
            attributes = self._functionNotParsed
        else:
            attributes = self._functionNotParsed["attributes"]

        if self._function.name == "":
            self._function.function_type = FunctionType.FALLBACK
            # 0.6.x introduced the receiver function
            # It has also an empty name, so we need to check the kind attribute
            if "kind" in attributes:
                if attributes["kind"] == "receive":
                    self._function.function_type = FunctionType.RECEIVE
        else:
            self._function.function_type = FunctionType.NORMAL

        if self._function.name == self._function.contract_declarer.name:
            self._function.function_type = FunctionType.CONSTRUCTOR

    def _analyze_attributes(self):
        if self.is_compact_ast:
            attributes = self._functionNotParsed
        else:
            attributes = self._functionNotParsed["attributes"]

        if "payable" in attributes:
            self._function.payable = attributes["payable"]
        if "stateMutability" in attributes:
            if attributes["stateMutability"] == "payable":
                self._function.payable = True
            elif attributes["stateMutability"] == "pure":
                self._function.pure = True
                self._function.view = True
            elif attributes["stateMutability"] == "view":
                self._function.view = True

        if "constant" in attributes:
            self._function.view = attributes["constant"]

        if "isConstructor" in attributes and attributes["isConstructor"]:
            self._function.function_type = FunctionType.CONSTRUCTOR

        if "kind" in attributes:
            if attributes["kind"] == "constructor":
                self._function.function_type = FunctionType.CONSTRUCTOR

        if "visibility" in attributes:
            self._function.visibility = attributes["visibility"]
        # old solc
        elif "public" in attributes:
            if attributes["public"]:
                self._function.visibility = "public"
            else:
                self._function.visibility = "private"
        else:
            self._function.visibility = "public"

        if "payable" in attributes:
            self._function.payable = attributes["payable"]

    def analyze_params(self):
        # Can be re-analyzed due to inheritance
        if self._params_was_analyzed:
            return

        self._params_was_analyzed = True

        self._analyze_attributes()

        if self.is_compact_ast:
            params = self._functionNotParsed["parameters"]
            returns = self._functionNotParsed["returnParameters"]
        else:
            children = self._functionNotParsed[self.get_children("children")]
            params = children[0]
            returns = children[1]

        if params:
            self._parse_params(params)
        if returns:
            self._parse_returns(returns)

    def analyze_content(self):
        if self._content_was_analyzed:
            return

        self._content_was_analyzed = True

        if self.is_compact_ast:
            body = self._functionNotParsed["body"]

            if body and body[self.get_key()] == "Block":
                self._function.is_implemented = True
                self._parse_cfg(body)

            for modifier in self._functionNotParsed["modifiers"]:
                self._parse_modifier(modifier)

        else:
            children = self._functionNotParsed[self.get_children("children")]
            self._function.is_implemented = False
            for child in children[2:]:
                if child[self.get_key()] == "Block":
                    self._function.is_implemented = True
                    self._parse_cfg(child)

            # Parse modifier after parsing all the block
            # In the case a local variable is used in the modifier
            for child in children[2:]:
                if child[self.get_key()] == "ModifierInvocation":
                    self._parse_modifier(child)

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

    def _new_yul_object(self, src: Union[str, Dict]) -> YulObject:
        node = self._function.new_node(NodeType.ASSEMBLY, src)
        yul_object = YulObject(self._function.contract, node, [self._function.name, f"asm_{len(self._node_to_yulobject)}"], parent_func=self._function)
        self._node_to_yulobject[node] = yul_object
        return yul_object

    # endregion
    ###################################################################################
    ###################################################################################
    # region Parsing function
    ###################################################################################
    ###################################################################################

    def _parse_if(self, if_statement: Dict, node: NodeSolc) -> NodeSolc:
        # IfStatement = 'if' '(' Expression ')' Statement ( 'else' Statement )?
        falseStatement = None

        if self.is_compact_ast:
            condition = if_statement["condition"]
            # Note: check if the expression could be directly
            # parsed here
            condition_node = self._new_node(NodeType.IF, condition["src"])
            condition_node.add_unparsed_expression(condition)
            link_underlying_nodes(node, condition_node)
            trueStatement = self._parse_statement(if_statement["trueBody"], condition_node)
            if if_statement["falseBody"]:
                falseStatement = self._parse_statement(if_statement["falseBody"], condition_node)
        else:
            children = if_statement[self.get_children("children")]
            condition = children[0]
            # Note: check if the expression could be directly
            # parsed here
            condition_node = self._new_node(NodeType.IF, condition["src"])
            condition_node.add_unparsed_expression(condition)
            link_underlying_nodes(node, condition_node)
            trueStatement = self._parse_statement(children[1], condition_node)
            if len(children) == 3:
                falseStatement = self._parse_statement(children[2], condition_node)

        endIf_node = self._new_node(NodeType.ENDIF, if_statement["src"])
        link_underlying_nodes(trueStatement, endIf_node)

        if falseStatement:
            link_underlying_nodes(falseStatement, endIf_node)
        else:
            link_underlying_nodes(condition_node, endIf_node)
        return endIf_node

    def _parse_while(self, whilte_statement: Dict, node: NodeSolc) -> NodeSolc:
        # WhileStatement = 'while' '(' Expression ')' Statement

        node_startWhile = self._new_node(NodeType.STARTLOOP, whilte_statement["src"])

        if self.is_compact_ast:
            node_condition = self._new_node(NodeType.IFLOOP, whilte_statement["condition"]["src"])
            node_condition.add_unparsed_expression(whilte_statement["condition"])
            statement = self._parse_statement(whilte_statement["body"], node_condition)
        else:
            children = whilte_statement[self.get_children("children")]
            expression = children[0]
            node_condition = self._new_node(NodeType.IFLOOP, expression["src"])
            node_condition.add_unparsed_expression(expression)
            statement = self._parse_statement(children[1], node_condition)

        node_endWhile = self._new_node(NodeType.ENDLOOP, whilte_statement["src"])

        link_underlying_nodes(node, node_startWhile)
        link_underlying_nodes(node_startWhile, node_condition)
        link_underlying_nodes(statement, node_condition)
        link_underlying_nodes(node_condition, node_endWhile)

        return node_endWhile

    def _parse_for_compact_ast(self, statement: Dict, node: NodeSolc) -> NodeSolc:
        body = statement["body"]
        init_expression = statement["initializationExpression"]
        condition = statement["condition"]
        loop_expression = statement["loopExpression"]

        node_startLoop = self._new_node(NodeType.STARTLOOP, statement["src"])
        node_endLoop = self._new_node(NodeType.ENDLOOP, statement["src"])

        if init_expression:
            node_init_expression = self._parse_statement(init_expression, node)
            link_underlying_nodes(node_init_expression, node_startLoop)
        else:
            link_underlying_nodes(node, node_startLoop)

        if condition:
            node_condition = self._new_node(NodeType.IFLOOP, condition["src"])
            node_condition.add_unparsed_expression(condition)
            link_underlying_nodes(node_startLoop, node_condition)
            link_underlying_nodes(node_condition, node_endLoop)
        else:
            node_condition = node_startLoop

        node_body = self._parse_statement(body, node_condition)

        node_LoopExpression = None
        if loop_expression:
            node_LoopExpression = self._parse_statement(loop_expression, node_body)
            link_underlying_nodes(node_LoopExpression, node_condition)
        else:
            link_underlying_nodes(node_body, node_condition)

        if not condition:
            if not loop_expression:
                # TODO: fix case where loop has no expression
                link_underlying_nodes(node_startLoop, node_endLoop)
            elif node_LoopExpression:
                link_underlying_nodes(node_LoopExpression, node_endLoop)

        return node_endLoop

    def _parse_for(self, statement: Dict, node: NodeSolc) -> NodeSolc:
        # ForStatement = 'for' '(' (SimpleStatement)? ';' (Expression)? ';' (ExpressionStatement)? ')' Statement

        # the handling of loop in the legacy ast is too complex
        # to integrate the comapct ast
        # its cleaner to do it separately
        if self.is_compact_ast:
            return self._parse_for_compact_ast(statement, node)

        hasInitExession = True
        hasCondition = True
        hasLoopExpression = True

        # Old solc version do not prevent in the attributes
        # if the loop has a init value /condition or expression
        # There is no way to determine that for(a;;) and for(;a;) are different with old solc
        if "attributes" in statement:
            attributes = statement["attributes"]
            if "initializationExpression" in statement:
                if not statement["initializationExpression"]:
                    hasInitExession = False
            elif "initializationExpression" in attributes:
                if not attributes["initializationExpression"]:
                    hasInitExession = False

            if "condition" in statement:
                if not statement["condition"]:
                    hasCondition = False
            elif "condition" in attributes:
                if not attributes["condition"]:
                    hasCondition = False

            if "loopExpression" in statement:
                if not statement["loopExpression"]:
                    hasLoopExpression = False
            elif "loopExpression" in attributes:
                if not attributes["loopExpression"]:
                    hasLoopExpression = False

        node_startLoop = self._new_node(NodeType.STARTLOOP, statement["src"])
        node_endLoop = self._new_node(NodeType.ENDLOOP, statement["src"])

        children = statement[self.get_children("children")]

        if hasInitExession:
            if len(children) >= 2:
                if children[0][self.get_key()] in [
                    "VariableDefinitionStatement",
                    "VariableDeclarationStatement",
                    "ExpressionStatement",
                ]:
                    node_initExpression = self._parse_statement(children[0], node)
                    link_underlying_nodes(node_initExpression, node_startLoop)
                else:
                    hasInitExession = False
            else:
                hasInitExession = False

        if not hasInitExession:
            link_underlying_nodes(node, node_startLoop)
        node_condition = node_startLoop

        if hasCondition:
            if hasInitExession and len(children) >= 2:
                candidate = children[1]
            else:
                candidate = children[0]
            if candidate[self.get_key()] not in [
                "VariableDefinitionStatement",
                "VariableDeclarationStatement",
                "ExpressionStatement",
            ]:
                expression = candidate
                node_condition = self._new_node(NodeType.IFLOOP, expression["src"])
                # expression = parse_expression(candidate, self)
                node_condition.add_unparsed_expression(expression)
                link_underlying_nodes(node_startLoop, node_condition)
                link_underlying_nodes(node_condition, node_endLoop)
                hasCondition = True
            else:
                hasCondition = False

        node_statement = self._parse_statement(children[-1], node_condition)

        node_LoopExpression = node_statement
        if hasLoopExpression:
            if len(children) > 2:
                if children[-2][self.get_key()] == "ExpressionStatement":
                    node_LoopExpression = self._parse_statement(children[-2], node_statement)
            if not hasCondition:
                link_underlying_nodes(node_LoopExpression, node_endLoop)

        if not hasCondition and not hasLoopExpression:
            link_underlying_nodes(node, node_endLoop)

        link_underlying_nodes(node_LoopExpression, node_condition)

        return node_endLoop

    def _parse_dowhile(self, do_while_statement: Dict, node: NodeSolc) -> NodeSolc:

        node_startDoWhile = self._new_node(NodeType.STARTLOOP, do_while_statement["src"])

        if self.is_compact_ast:
            node_condition = self._new_node(NodeType.IFLOOP, do_while_statement["condition"]["src"])
            node_condition.add_unparsed_expression(do_while_statement["condition"])
            statement = self._parse_statement(do_while_statement["body"], node_condition)
        else:
            children = do_while_statement[self.get_children("children")]
            # same order in the AST as while
            expression = children[0]
            node_condition = self._new_node(NodeType.IFLOOP, expression["src"])
            node_condition.add_unparsed_expression(expression)
            statement = self._parse_statement(children[1], node_condition)

        node_endDoWhile = self._new_node(NodeType.ENDLOOP, do_while_statement["src"])

        link_underlying_nodes(node, node_startDoWhile)
        # empty block, loop from the start to the condition
        if not node_condition.underlying_node.sons:
            link_underlying_nodes(node_startDoWhile, node_condition)
        else:
            link_nodes(node_startDoWhile.underlying_node, node_condition.underlying_node.sons[0])
        link_underlying_nodes(statement, node_condition)
        link_underlying_nodes(node_condition, node_endDoWhile)
        return node_endDoWhile

    def _parse_try_catch(self, statement: Dict, node: NodeSolc) -> NodeSolc:
        externalCall = statement.get("externalCall", None)

        if externalCall is None:
            raise ParsingError("Try/Catch not correctly parsed by Slither %s" % statement)

        new_node = self._new_node(NodeType.TRY, statement["src"])
        new_node.add_unparsed_expression(externalCall)
        link_underlying_nodes(node, new_node)
        node = new_node

        for clause in statement.get("clauses", []):
            self._parse_catch(clause, node)
        return node

    def _parse_catch(self, statement: Dict, node: NodeSolc) -> NodeSolc:
        block = statement.get("block", None)

        if block is None:
            raise ParsingError("Catch not correctly parsed by Slither %s" % statement)
        try_node = self._new_node(NodeType.CATCH, statement["src"])
        link_underlying_nodes(node, try_node)

        if self.is_compact_ast:
            params = statement["parameters"]
        else:
            params = statement[self.get_children("children")]

        if params:
            for param in params.get("parameters", []):
                assert param[self.get_key()] == "VariableDeclaration"
                self._add_param(param)

        return self._parse_statement(block, try_node)

    def _parse_variable_definition(self, statement: Dict, node: NodeSolc) -> NodeSolc:
        try:
            local_var = LocalVariable()
            local_var.set_function(self._function)
            local_var.set_offset(statement["src"], self._function.slither)

            local_var_parser = LocalVariableSolc(local_var, statement)
            self._add_local_variable(local_var_parser)
            # local_var.analyze(self)

            new_node = self._new_node(NodeType.VARIABLE, statement["src"])
            new_node.underlying_node.add_variable_declaration(local_var)
            link_underlying_nodes(node, new_node)
            return new_node
        except MultipleVariablesDeclaration:
            # Custom handling of var (a,b) = .. style declaration
            if self.is_compact_ast:
                variables = statement["declarations"]
                count = len(variables)

                if (
                    statement["initialValue"]["nodeType"] == "TupleExpression"
                    and len(statement["initialValue"]["components"]) == count
                ):
                    inits = statement["initialValue"]["components"]
                    i = 0
                    new_node = node
                    for variable in variables:
                        init = inits[i]
                        src = variable["src"]
                        i = i + 1

                        new_statement = {
                            "nodeType": "VariableDefinitionStatement",
                            "src": src,
                            "declarations": [variable],
                            "initialValue": init,
                        }
                        new_node = self._parse_variable_definition(new_statement, new_node)

                else:
                    # If we have
                    # var (a, b) = f()
                    # we can split in multiple declarations, without init
                    # Then we craft one expression that does the assignment
                    variables = []
                    i = 0
                    new_node = node
                    for variable in statement["declarations"]:
                        i = i + 1
                        if variable:
                            src = variable["src"]
                            # Create a fake statement to be consistent
                            new_statement = {
                                "nodeType": "VariableDefinitionStatement",
                                "src": src,
                                "declarations": [variable],
                            }
                            variables.append(variable)

                            new_node = self._parse_variable_definition_init_tuple(
                                new_statement, i, new_node
                            )

                    var_identifiers = []
                    # craft of the expression doing the assignement
                    for v in variables:
                        identifier = {
                            "nodeType": "Identifier",
                            "src": v["src"],
                            "name": v["name"],
                            "typeDescriptions": {"typeString": v["typeDescriptions"]["typeString"]},
                        }
                        var_identifiers.append(identifier)

                    tuple_expression = {
                        "nodeType": "TupleExpression",
                        "src": statement["src"],
                        "components": var_identifiers,
                    }

                    expression = {
                        "nodeType": "Assignment",
                        "src": statement["src"],
                        "operator": "=",
                        "type": "tuple()",
                        "leftHandSide": tuple_expression,
                        "rightHandSide": statement["initialValue"],
                        "typeDescriptions": {"typeString": "tuple()"},
                    }
                    node = new_node
                    new_node = self._new_node(NodeType.EXPRESSION, statement["src"])
                    new_node.add_unparsed_expression(expression)
                    link_underlying_nodes(node, new_node)

            else:
                count = 0
                children = statement[self.get_children("children")]
                child = children[0]
                while child[self.get_key()] == "VariableDeclaration":
                    count = count + 1
                    child = children[count]

                assert len(children) == (count + 1)
                tuple_vars = children[count]

                variables_declaration = children[0:count]
                i = 0
                new_node = node
                if tuple_vars[self.get_key()] == "TupleExpression":
                    assert len(tuple_vars[self.get_children("children")]) == count
                    for variable in variables_declaration:
                        init = tuple_vars[self.get_children("children")][i]
                        src = variable["src"]
                        i = i + 1
                        # Create a fake statement to be consistent
                        new_statement = {
                            self.get_key(): "VariableDefinitionStatement",
                            "src": src,
                            self.get_children("children"): [variable, init],
                        }

                        new_node = self._parse_variable_definition(new_statement, new_node)
                else:
                    # If we have
                    # var (a, b) = f()
                    # we can split in multiple declarations, without init
                    # Then we craft one expression that does the assignment
                    assert tuple_vars[self.get_key()] in ["FunctionCall", "Conditional"]
                    variables = []
                    for variable in variables_declaration:
                        src = variable["src"]
                        i = i + 1
                        # Create a fake statement to be consistent
                        new_statement = {
                            self.get_key(): "VariableDefinitionStatement",
                            "src": src,
                            self.get_children("children"): [variable],
                        }
                        variables.append(variable)

                        new_node = self._parse_variable_definition_init_tuple(
                            new_statement, i, new_node
                        )
                    var_identifiers = []
                    # craft of the expression doing the assignement
                    for v in variables:
                        identifier = {
                            self.get_key(): "Identifier",
                            "src": v["src"],
                            "attributes": {
                                "value": v["attributes"][self.get_key()],
                                "type": v["attributes"]["type"],
                            },
                        }
                        var_identifiers.append(identifier)

                    expression = {
                        self.get_key(): "Assignment",
                        "src": statement["src"],
                        "attributes": {"operator": "=", "type": "tuple()"},
                        self.get_children("children"): [
                            {
                                self.get_key(): "TupleExpression",
                                "src": statement["src"],
                                self.get_children("children"): var_identifiers,
                            },
                            tuple_vars,
                        ],
                    }
                    node = new_node
                    new_node = self._new_node(NodeType.EXPRESSION, statement["src"])
                    new_node.add_unparsed_expression(expression)
                    link_underlying_nodes(node, new_node)

            return new_node

    def _parse_variable_definition_init_tuple(
        self, statement: Dict, index: int, node: NodeSolc
    ) -> NodeSolc:
        local_var = LocalVariableInitFromTuple()
        local_var.set_function(self._function)
        local_var.set_offset(statement["src"], self._function.slither)

        local_var_parser = LocalVariableInitFromTupleSolc(local_var, statement, index)

        self._add_local_variable(local_var_parser)

        new_node = self._new_node(NodeType.VARIABLE, statement["src"])
        new_node.underlying_node.add_variable_declaration(local_var)
        link_underlying_nodes(node, new_node)
        return new_node

    def _parse_statement(self, statement: Dict, node: NodeSolc) -> NodeSolc:
        """

        Return:
            node
        """
        # Statement = IfStatement | WhileStatement | ForStatement | Block | InlineAssemblyStatement |
        #            ( DoWhileStatement | PlaceholderStatement | Continue | Break | Return |
        #                          Throw | EmitStatement | SimpleStatement ) ';'
        # SimpleStatement = VariableDefinition | ExpressionStatement

        name = statement[self.get_key()]
        # SimpleStatement = VariableDefinition | ExpressionStatement
        if name == "IfStatement":
            node = self._parse_if(statement, node)
        elif name == "WhileStatement":
            node = self._parse_while(statement, node)
        elif name == "ForStatement":
            node = self._parse_for(statement, node)
        elif name == "Block":
            node = self._parse_block(statement, node)
        elif name == "InlineAssembly":
            # Added with solc 0.6 - the yul code is an AST
            if 'AST' in statement:
                self._function.contains_assembly = True
                yul_object = self._new_yul_object(statement['src'])
                entrypoint = yul_object.entrypoint
                exitpoint = yul_object.convert(statement['AST'])

                # technically, entrypoint and exitpoint are YulNodes and we should be returning a NodeSolc here
                # but they both expose an underlying_node so oh well
                link_underlying_nodes(node, entrypoint)
                node = exitpoint
            else:
                asm_node = self._new_node(NodeType.ASSEMBLY, statement['src'])
                self._function._contains_assembly = True
                # Added with solc 0.4.12
                if 'operations' in statement:
                    asm_node.underlying_node.add_inline_asm(statement['operations'])
                link_underlying_nodes(node, asm_node)
                node = asm_node
        elif name == "DoWhileStatement":
            node = self._parse_dowhile(statement, node)
        # For Continue / Break / Return / Throw
        # The is fixed later
        elif name == "Continue":
            continue_node = self._new_node(NodeType.CONTINUE, statement["src"])
            link_underlying_nodes(node, continue_node)
            node = continue_node
        elif name == "Break":
            break_node = self._new_node(NodeType.BREAK, statement["src"])
            link_underlying_nodes(node, break_node)
            node = break_node
        elif name == "Return":
            return_node = self._new_node(NodeType.RETURN, statement["src"])
            link_underlying_nodes(node, return_node)
            if self.is_compact_ast:
                if statement["expression"]:
                    return_node.add_unparsed_expression(statement["expression"])
            else:
                if (
                    self.get_children("children") in statement
                    and statement[self.get_children("children")]
                ):
                    assert len(statement[self.get_children("children")]) == 1
                    expression = statement[self.get_children("children")][0]
                    return_node.add_unparsed_expression(expression)
            node = return_node
        elif name == "Throw":
            throw_node = self._new_node(NodeType.THROW, statement["src"])
            link_underlying_nodes(node, throw_node)
            node = throw_node
        elif name == "EmitStatement":
            # expression = parse_expression(statement[self.get_children('children')][0], self)
            if self.is_compact_ast:
                expression = statement["eventCall"]
            else:
                expression = statement[self.get_children("children")][0]
            new_node = self._new_node(NodeType.EXPRESSION, statement["src"])
            new_node.add_unparsed_expression(expression)
            link_underlying_nodes(node, new_node)
            node = new_node
        elif name in ["VariableDefinitionStatement", "VariableDeclarationStatement"]:
            node = self._parse_variable_definition(statement, node)
        elif name == "ExpressionStatement":
            # assert len(statement[self.get_children('expression')]) == 1
            # assert not 'attributes' in statement
            # expression = parse_expression(statement[self.get_children('children')][0], self)
            if self.is_compact_ast:
                expression = statement[self.get_children("expression")]
            else:
                expression = statement[self.get_children("expression")][0]
            new_node = self._new_node(NodeType.EXPRESSION, statement["src"])
            new_node.add_unparsed_expression(expression)
            link_underlying_nodes(node, new_node)
            node = new_node
        elif name == "TryStatement":
            node = self._parse_try_catch(statement, node)
        # elif name == 'TryCatchClause':
        #     self._parse_catch(statement, node)
        else:
            raise ParsingError("Statement not parsed %s" % name)

        return node

    def _parse_block(self, block: Dict, node: NodeSolc):
        """
        Return:
            Node
        """
        assert block[self.get_key()] == "Block"

        if self.is_compact_ast:
            statements = block["statements"]
        else:
            statements = block[self.get_children("children")]

        for statement in statements:
            node = self._parse_statement(statement, node)
        return node

    def _parse_cfg(self, cfg: Dict):

        assert cfg[self.get_key()] == "Block"

        node = self._new_node(NodeType.ENTRYPOINT, cfg["src"])
        self._function.entry_point = node.underlying_node

        if self.is_compact_ast:
            statements = cfg["statements"]
        else:
            statements = cfg[self.get_children("children")]

        if not statements:
            self._function.is_empty = True
        else:
            self._function.is_empty = False
            self._parse_block(cfg, node)
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
                self._fix_catch(son, end_node)

    def _add_param(self, param: Dict) -> LocalVariableSolc:

        local_var = LocalVariable()
        local_var.set_function(self._function)
        local_var.set_offset(param["src"], self._function.slither)

        local_var_parser = LocalVariableSolc(local_var, param)

        local_var_parser.analyze(self)

        # see https://solidity.readthedocs.io/en/v0.4.24/types.html?highlight=storage%20location#data-location
        if local_var.location == "default":
            local_var.set_location("memory")

        self._add_local_variable(local_var_parser)
        return local_var_parser

    def _parse_params(self, params: Dict):
        assert params[self.get_key()] == "ParameterList"

        self.parameters_src.set_offset(params["src"], self._function.slither)

        if self.is_compact_ast:
            params = params["parameters"]
        else:
            params = params[self.get_children("children")]

        for param in params:
            assert param[self.get_key()] == "VariableDeclaration"
            local_var = self._add_param(param)
            self._function.add_parameters(local_var.underlying_variable)

    def _parse_returns(self, returns: Dict):

        assert returns[self.get_key()] == "ParameterList"

        self.returns_src.set_offset(returns["src"], self._function.slither)

        if self.is_compact_ast:
            returns = returns["parameters"]
        else:
            returns = returns[self.get_children("children")]

        for ret in returns:
            assert ret[self.get_key()] == "VariableDeclaration"
            local_var = self._add_param(ret)
            self._function.add_return(local_var.underlying_variable)

    def _parse_modifier(self, modifier: Dict):
        m = parse_expression(modifier, self)
        # self._expression_modifiers.append(m)

        # Do not parse modifier nodes for interfaces
        if not self._function.is_implemented:
            return

        for m in ExportValues(m).result():
            if isinstance(m, Function):
                node_parser = self._new_node(NodeType.EXPRESSION, modifier["src"])
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
                node_parser = self._new_node(NodeType.EXPRESSION, modifier["src"])
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
        for node in self._node_to_nodesolc.keys():
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
            for node in self._node_to_nodesolc.keys():
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
            for node in self._node_to_nodesolc.keys():
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

        if true_node_parser.underlying_node.type not in [NodeType.THROW, NodeType.RETURN]:
            link_underlying_nodes(true_node_parser, endif_node)
        if false_node_parser.underlying_node.type not in [NodeType.THROW, NodeType.RETURN]:
            link_underlying_nodes(false_node_parser, endif_node)

        self._function.nodes = [n for n in self._function.nodes if n.node_id != node.node_id]
        del self._node_to_nodesolc[node]

    # endregion
