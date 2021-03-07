import abc
import json
from typing import Optional, Dict, List, Union

from slither.core.cfg.node import NodeType, Node, link_nodes
from slither.core.declarations import (
    Function,
    SolidityFunction,
    Contract,
)
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions import (
    Literal,
    AssignmentOperation,
    AssignmentOperationType,
    Identifier,
    CallExpression,
    TupleExpression,
    BinaryOperation,
    UnaryOperation,
)
from slither.core.expressions.expression import Expression
from slither.core.slither_core import SlitherCore
from slither.core.solidity_types import ElementaryType
from slither.core.variables.local_variable import LocalVariable
from slither.exceptions import SlitherException
from slither.solc_parsing.yul.evm_functions import (
    format_function_descriptor,
    builtins,
    YulBuiltin,
    unary_ops,
    binary_ops,
)
from slither.visitors.expression.find_calls import FindCalls
from slither.visitors.expression.read_var import ReadVar
from slither.visitors.expression.write_var import WriteVar


class YulNode:
    def __init__(self, node: Node, scope: "YulScope"):
        self._node = node
        self._scope = scope
        self._unparsed_expression: Optional[Dict] = None

    @property
    def underlying_node(self) -> Node:
        return self._node

    def add_unparsed_expression(self, expression: Dict):
        assert self._unparsed_expression is None
        self._unparsed_expression = expression

    def analyze_expressions(self):
        if self._node.type == NodeType.VARIABLE and not self._node.expression:
            self._node.add_expression(self._node.variable_declaration.expression)
        if self._unparsed_expression:
            expression = parse_yul(self._scope, self, self._unparsed_expression)
            self._node.add_expression(expression)

        if self._node.expression:
            if self._node.type == NodeType.VARIABLE:
                # Update the expression to be an assignement to the variable
                _expression = AssignmentOperation(
                    Identifier(self._node.variable_declaration),
                    self._node.expression,
                    AssignmentOperationType.ASSIGN,
                    self._node.variable_declaration.type,
                )
                _expression.set_offset(self._node.expression.source_mapping, self._node.slither)
                self._node.add_expression(_expression, bypass_verif_empty=True)

            expression = self._node.expression
            read_var = ReadVar(expression)
            self._node.variables_read_as_expression = read_var.result()

            write_var = WriteVar(expression)
            self._node.variables_written_as_expression = write_var.result()

            find_call = FindCalls(expression)
            self._node.calls_as_expression = find_call.result()
            self._node.external_calls_as_expressions = [
                c for c in self._node.calls_as_expression if not isinstance(c.called, Identifier)
            ]
            self._node.internal_calls_as_expressions = [
                c for c in self._node.calls_as_expression if isinstance(c.called, Identifier)
            ]


def link_underlying_nodes(node1: YulNode, node2: YulNode):
    link_nodes(node1.underlying_node, node2.underlying_node)


def _name_to_yul_name(variable_name: str, yul_id: List[str]) -> str:
    """
    Translate the variable name to a unique yul name
    Within the same function, yul blocks can declare
    different variables with the same name
    We need to create unique name per variable
    to prevent collision during the SSA generation

    :param var:
    :param yul_id:
    :return:
    """
    return variable_name + f"_{'_'.join(yul_id)}"


class YulScope(metaclass=abc.ABCMeta):
    __slots__ = [
        "_contract",
        "_id",
        "_yul_local_variables",
        "_yul_local_functions",
        "_parent_func",
    ]

    def __init__(
        self, contract: Optional[Contract], yul_id: List[str], parent_func: Function = None
    ):
        self._contract = contract
        self._id: List[str] = yul_id
        self._yul_local_variables: List[YulLocalVariable] = []
        self._yul_local_functions: List[YulFunction] = []
        self._parent_func = parent_func

    @property
    def id(self) -> List[str]:
        return self._id

    @property
    def contract(self) -> Optional[Contract]:
        return self._contract

    @property
    def slither(self) -> SlitherCore:
        return self._contract.slither

    @property
    def parent_func(self) -> Optional[Function]:
        return self._parent_func

    @property
    @abc.abstractmethod
    def function(self) -> Function:
        pass

    @abc.abstractmethod
    def new_node(self, node_type: NodeType, src: Union[str, Dict]) -> YulNode:
        pass

    def add_yul_local_variable(self, var):
        self._yul_local_variables.append(var)

    def get_yul_local_variable_from_name(self, variable_name):
        return next(
            (
                v
                for v in self._yul_local_variables
                if v.underlying.name == _name_to_yul_name(variable_name, self.id)
            ),
            None,
        )

    def add_yul_local_function(self, func):
        self._yul_local_functions.append(func)

    def get_yul_local_function_from_name(self, func_name):
        return next(
            (v for v in self._yul_local_functions if v.underlying.name == func_name),
            None,
        )


class YulLocalVariable:  # pylint: disable=too-few-public-methods
    __slots__ = ["_variable", "_root"]

    def __init__(self, var: LocalVariable, root: YulScope, ast: Dict):
        assert ast["nodeType"] == "YulTypedName"

        self._variable = var
        self._root = root

        # start initializing the underlying variable
        var.set_function(root.function)
        var.set_offset(ast["src"], root.slither)

        var.name = _name_to_yul_name(ast["name"], root.id)
        var.set_type(ElementaryType("uint256"))
        var.set_location("memory")

    @property
    def underlying(self) -> LocalVariable:
        return self._variable


class YulFunction(YulScope):
    __slots__ = ["_function", "_root", "_ast", "_nodes", "_entrypoint"]

    def __init__(self, func: Function, root: YulScope, ast: Dict):
        super().__init__(root.contract, root.id + [ast["name"]], parent_func=root.parent_func)

        assert ast["nodeType"] == "YulFunctionDefinition"

        self._function: Function = func
        self._root: YulScope = root
        self._ast: Dict = ast

        # start initializing the underlying function

        func.name = ast["name"]
        func.set_visibility("private")
        func.set_offset(ast["src"], root.slither)
        func.set_contract(root.contract)
        func.slither = root.slither
        func.set_contract_declarer(root.contract)
        func.scope = root.id
        func.is_implemented = True

        self._nodes: List[YulNode] = []
        self._entrypoint = self.new_node(NodeType.ASSEMBLY, ast["src"])
        func.entry_point = self._entrypoint.underlying_node

        self.add_yul_local_function(self)

    @property
    def underlying(self) -> Function:
        return self._function

    @property
    def slither(self) -> SlitherCore:
        return self._entrypoint.underlying_node.slither

    @property
    def function(self) -> Function:
        return self._function

    def convert_body(self):
        node = self.new_node(NodeType.ENTRYPOINT, self._ast["src"])
        link_underlying_nodes(self._entrypoint, node)

        for param in self._ast.get("parameters", []):
            node = convert_yul(self, node, param)
            self._function.add_parameters(
                self.get_yul_local_variable_from_name(param["name"]).underlying
            )

        for ret in self._ast.get("returnVariables", []):
            node = convert_yul(self, node, ret)
            self._function.add_return(self.get_yul_local_variable_from_name(ret["name"]).underlying)

        convert_yul(self, node, self._ast["body"])

    def parse_body(self):
        for node in self._nodes:
            node.analyze_expressions()

    def new_node(self, node_type, src) -> YulNode:
        if self._function:
            node = self._function.new_node(node_type, src)
        else:
            raise SlitherException("standalone yul objects are not supported yet")

        yul_node = YulNode(node, self)
        self._nodes.append(yul_node)
        return yul_node


class YulBlock(YulScope):
    """
    A YulBlock represents a standalone yul component.
    For example an inline assembly block

    """

    __slots__ = ["_entrypoint", "_parent_func", "_nodes"]

    def __init__(self, contract: Optional[Contract], entrypoint: Node, yul_id: List[str], **kwargs):
        super().__init__(contract, yul_id, **kwargs)

        self._entrypoint: YulNode = YulNode(entrypoint, self)
        self._nodes: List[YulNode] = []

    @property
    def entrypoint(self) -> YulNode:
        return self._entrypoint

    @property
    def function(self) -> Function:
        return self._parent_func

    def new_node(self, node_type: NodeType, src: Union[str, Dict]) -> YulNode:
        if self._parent_func:
            node = self._parent_func.new_node(node_type, src)
        else:
            raise SlitherException("standalone yul objects are not supported yet")

        yul_node = YulNode(node, self)
        self._nodes.append(yul_node)
        return yul_node

    def convert(self, ast: Dict) -> YulNode:
        return convert_yul(self, self._entrypoint, ast)

    def analyze_expressions(self):
        for node in self._nodes:
            node.analyze_expressions()


###################################################################################
###################################################################################
# region Block conversion
###################################################################################
###################################################################################


# The functions in this region, at a high level, will extract the control flow
# structures and metadata from the input AST. These include things like function
# definitions and local variables.
#
# Each function takes three parameters:
#     1)  root is the current YulScope, where you can find things like local variables
#     2)  parent is the previous YulNode, which you'll have to link to
#     3)  ast is a dictionary and is the current node in the Yul ast being converted
#
# Each function must return a single parameter:
#     1)  the new YulNode that the CFG ends at
#
# The entrypoint is the function at the end of this region, `convert_yul`, which
# dispatches to a specialized function based on a lookup dictionary.


def convert_yul_block(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    for statement in ast["statements"]:
        parent = convert_yul(root, parent, statement)
    return parent


def convert_yul_function_definition(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    func = FunctionContract(root.slither)
    yul_function = YulFunction(func, root, ast)

    root.contract.add_function(func)
    root.slither.add_function(func)
    root.add_yul_local_function(yul_function)

    yul_function.convert_body()
    yul_function.parse_body()

    return parent


def convert_yul_variable_declaration(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    for variable_ast in ast["variables"]:
        parent = convert_yul(root, parent, variable_ast)

    node = root.new_node(NodeType.EXPRESSION, ast["src"])
    node.add_unparsed_expression(ast)
    link_underlying_nodes(parent, node)

    return node


def convert_yul_assignment(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    node = root.new_node(NodeType.EXPRESSION, ast["src"])
    node.add_unparsed_expression(ast)
    link_underlying_nodes(parent, node)
    return node


def convert_yul_expression_statement(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    src = ast["src"]
    expression_ast = ast["expression"]

    expression = root.new_node(NodeType.EXPRESSION, src)
    expression.add_unparsed_expression(expression_ast)
    link_underlying_nodes(parent, expression)

    return expression


def convert_yul_if(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    # we're cheating and pretending that yul supports if/else so we can convert switch cleaner

    src = ast["src"]
    condition_ast = ast["condition"]
    true_body_ast = ast["body"]
    false_body_ast = ast["false_body"] if "false_body" in ast else None

    condition = root.new_node(NodeType.IF, src)
    end = root.new_node(NodeType.ENDIF, src)

    condition.add_unparsed_expression(condition_ast)

    true_body = convert_yul(root, condition, true_body_ast)

    if false_body_ast:
        false_body = convert_yul(root, condition, false_body_ast)
        link_underlying_nodes(false_body, end)
    else:
        link_underlying_nodes(condition, end)

    link_underlying_nodes(parent, condition)
    link_underlying_nodes(true_body, end)

    return end


def convert_yul_switch(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    """
    This is unfortunate. We don't really want a switch in our IR so we're going to
    translate it into a series of if/else statements.
    """
    cases_ast = ast["cases"]
    expression_ast = ast["expression"]

    # this variable stores the result of the expression so we don't accidentally compute it more than once
    switch_expr_var = "switch_expr_{}".format(ast["src"].replace(":", "_"))

    rewritten_switch = {
        "nodeType": "YulBlock",
        "src": ast["src"],
        "statements": [
            {
                "nodeType": "YulVariableDeclaration",
                "src": expression_ast["src"],
                "variables": [
                    {
                        "nodeType": "YulTypedName",
                        "src": expression_ast["src"],
                        "name": switch_expr_var,
                        "type": "",
                    },
                ],
                "value": expression_ast,
            },
        ],
    }

    last_if: Optional[Dict] = None

    default_ast = None

    for case_ast in cases_ast:
        body_ast = case_ast["body"]
        value_ast = case_ast["value"]

        if value_ast == "default":
            default_ast = case_ast
            continue

        current_if = {
            "nodeType": "YulIf",
            "src": case_ast["src"],
            "condition": {
                "nodeType": "YulFunctionCall",
                "src": case_ast["src"],
                "functionName": {
                    "nodeType": "YulIdentifier",
                    "src": case_ast["src"],
                    "name": "eq",
                },
                "arguments": [
                    {
                        "nodeType": "YulIdentifier",
                        "src": case_ast["src"],
                        "name": switch_expr_var,
                    },
                    value_ast,
                ],
            },
            "body": body_ast,
        }

        if last_if:
            last_if["false_body"] = current_if  # pylint: disable=unsupported-assignment-operation
        else:
            rewritten_switch["statements"].append(current_if)

        last_if = current_if

    if default_ast:
        body_ast = default_ast["body"]

        if last_if:
            last_if["false_body"] = body_ast
        else:
            rewritten_switch["statements"].append(body_ast)

    return convert_yul(root, parent, rewritten_switch)


def convert_yul_for_loop(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    pre_ast = ast["pre"]
    condition_ast = ast["condition"]
    post_ast = ast["post"]
    body_ast = ast["body"]

    start_loop = root.new_node(NodeType.STARTLOOP, ast["src"])
    end_loop = root.new_node(NodeType.ENDLOOP, ast["src"])

    link_underlying_nodes(parent, start_loop)

    pre = convert_yul(root, start_loop, pre_ast)

    condition = root.new_node(NodeType.IFLOOP, condition_ast["src"])
    condition.add_unparsed_expression(condition_ast)
    link_underlying_nodes(pre, condition)

    link_underlying_nodes(condition, end_loop)

    body = convert_yul(root, condition, body_ast)

    post = convert_yul(root, body, post_ast)

    link_underlying_nodes(post, condition)

    return end_loop


def convert_yul_break(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    break_ = root.new_node(NodeType.BREAK, ast["src"])
    link_underlying_nodes(parent, break_)
    return break_


def convert_yul_continue(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    continue_ = root.new_node(NodeType.CONTINUE, ast["src"])
    link_underlying_nodes(parent, continue_)
    return continue_


def convert_yul_leave(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    leave = root.new_node(NodeType.RETURN, ast["src"])
    link_underlying_nodes(parent, leave)
    return leave


def convert_yul_typed_name(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    local_var = LocalVariable()

    var = YulLocalVariable(local_var, root, ast)
    root.add_yul_local_variable(var)

    node = root.new_node(NodeType.VARIABLE, ast["src"])
    node.underlying_node.add_variable_declaration(local_var)
    link_underlying_nodes(parent, node)

    return node


def convert_yul_unsupported(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    raise SlitherException(
        f"no converter available for {ast['nodeType']} {json.dumps(ast, indent=2)}"
    )


def convert_yul(root: YulScope, parent: YulNode, ast: Dict) -> YulNode:
    return converters.get(ast["nodeType"], convert_yul_unsupported)(root, parent, ast)


converters = {
    "YulBlock": convert_yul_block,
    "YulFunctionDefinition": convert_yul_function_definition,
    "YulVariableDeclaration": convert_yul_variable_declaration,
    "YulAssignment": convert_yul_assignment,
    "YulExpressionStatement": convert_yul_expression_statement,
    "YulIf": convert_yul_if,
    "YulSwitch": convert_yul_switch,
    "YulForLoop": convert_yul_for_loop,
    "YulBreak": convert_yul_break,
    "YulContinue": convert_yul_continue,
    "YulLeave": convert_yul_leave,
    "YulTypedName": convert_yul_typed_name,
}

# endregion
###################################################################################
###################################################################################

###################################################################################
###################################################################################
# region Expression parsing
###################################################################################
###################################################################################

"""
The functions in this region parse the AST into expressions.

Each function takes three parameters:
    1)  root is the same root as above
    2)  node is the CFG node which stores this expression
    3)  ast is the same ast as above

Each function must return a single parameter:
    1) The operation that was parsed, or None

The entrypoint is the function at the end of this region, `parse_yul`, which
dispatches to a specialized function based on a lookup dictionary.
"""


def _parse_yul_assignment_common(
    root: YulScope, node: YulNode, ast: Dict, key: str
) -> Optional[Expression]:
    lhs = [parse_yul(root, node, arg) for arg in ast[key]]
    rhs = parse_yul(root, node, ast["value"])

    return AssignmentOperation(
        vars_to_val(lhs), rhs, AssignmentOperationType.ASSIGN, vars_to_typestr(lhs)
    )


def parse_yul_variable_declaration(
    root: YulScope, node: YulNode, ast: Dict
) -> Optional[Expression]:
    """
    We already created variables in the conversion phase, so just do
    the assignment
    """

    if not ast["value"]:
        return None

    return _parse_yul_assignment_common(root, node, ast, "variables")


def parse_yul_assignment(root: YulScope, node: YulNode, ast: Dict) -> Optional[Expression]:
    return _parse_yul_assignment_common(root, node, ast, "variableNames")


def parse_yul_function_call(root: YulScope, node: YulNode, ast: Dict) -> Optional[Expression]:
    args = [parse_yul(root, node, arg) for arg in ast["arguments"]]
    ident = parse_yul(root, node, ast["functionName"])

    if not isinstance(ident, Identifier):
        raise SlitherException("expected identifier from parsing function name")

    if isinstance(ident.value, YulBuiltin):
        name = ident.value.name
        if name in binary_ops:
            if name in ["shl", "shr", "sar"]:
                # lmao ok
                return BinaryOperation(args[1], args[0], binary_ops[name])

            return BinaryOperation(args[0], args[1], binary_ops[name])

        if name in unary_ops:
            return UnaryOperation(args[0], unary_ops[name])

        ident = Identifier(SolidityFunction(format_function_descriptor(ident.value.name)))

    if isinstance(ident.value, Function):
        return CallExpression(ident, args, vars_to_typestr(ident.value.returns))
    if isinstance(ident.value, SolidityFunction):
        return CallExpression(ident, args, vars_to_typestr(ident.value.return_type))

    raise SlitherException(f"unexpected function call target type {str(type(ident.value))}")


def parse_yul_identifier(root: YulScope, _node: YulNode, ast: Dict) -> Optional[Expression]:
    name = ast["name"]

    if name in builtins:
        return Identifier(YulBuiltin(name))

    # check function-scoped variables
    if root.parent_func:
        variable = root.parent_func.get_local_variable_from_name(name)
        if variable:
            return Identifier(variable)

        variable = root.parent_func.contract.get_state_variable_from_name(name)
        if variable:
            return Identifier(variable)

    # check yul-scoped variable
    variable = root.get_yul_local_variable_from_name(name)
    if variable:
        return Identifier(variable.underlying)

    # check yul-scoped function

    func = root.get_yul_local_function_from_name(name)
    if func:
        return Identifier(func.underlying)

    # check for magic suffixes
    if name.endswith("_slot"):
        potential_name = name[:-5]
        var = root.function.contract.get_state_variable_from_name(potential_name)
        if var:
            return Identifier(var)
        var = root.function.get_local_variable_from_name(potential_name)
        if var and var.is_storage:
            return Identifier(var)
    if name.endswith("_offset"):
        potential_name = name[:-7]
        var = root.function.contract.get_state_variable_from_name(potential_name)
        if var:
            return Identifier(var)

    raise SlitherException(f"unresolved reference to identifier {name}")


def parse_yul_literal(_root: YulScope, _node: YulNode, ast: Dict) -> Optional[Expression]:
    kind = ast["kind"]
    value = ast["value"]

    if not kind:
        kind = "bool" if value in ["true", "false"] else "uint256"

    if kind == "number":
        kind = "uint256"

    return Literal(value, ElementaryType(kind))


def parse_yul_typed_name(root: YulScope, _node: YulNode, ast: Dict) -> Optional[Expression]:
    var = root.get_yul_local_variable_from_name(ast["name"])

    i = Identifier(var.underlying)
    i.type = var.underlying.type
    return i


def parse_yul_unsupported(_root: YulScope, _node: YulNode, ast: Dict) -> Optional[Expression]:
    raise SlitherException(f"no parser available for {ast['nodeType']} {json.dumps(ast, indent=2)}")


def parse_yul(root: YulScope, node: YulNode, ast: Dict) -> Optional[Expression]:
    op = parsers.get(ast["nodeType"], parse_yul_unsupported)(root, node, ast)
    if op:
        op.set_offset(ast["src"], root.slither)
    return op


parsers = {
    "YulVariableDeclaration": parse_yul_variable_declaration,
    "YulAssignment": parse_yul_assignment,
    "YulFunctionCall": parse_yul_function_call,
    "YulIdentifier": parse_yul_identifier,
    "YulTypedName": parse_yul_typed_name,
    "YulLiteral": parse_yul_literal,
}


# endregion
###################################################################################
###################################################################################


def vars_to_typestr(rets: List[Expression]) -> str:
    if len(rets) == 0:
        return ""
    if len(rets) == 1:
        return str(rets[0].type)
    return "tuple({})".format(",".join(str(ret.type) for ret in rets))


def vars_to_val(vars_to_convert):
    if len(vars_to_convert) == 1:
        return vars_to_convert[0]
    return TupleExpression(vars_to_convert)
