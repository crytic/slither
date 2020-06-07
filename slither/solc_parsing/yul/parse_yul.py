import json

from slither.core.cfg.node import NodeType, link_nodes
from slither.core.declarations import Function, SolidityFunction, SolidityVariable
from slither.core.expressions import (
    Literal,
    AssignmentOperation,
    AssignmentOperationType,
    Identifier, CallExpression, TupleExpression, BinaryOperation, UnaryOperation,
)
from slither.core.solidity_types import ElementaryType
from slither.core.variables.local_variable import LocalVariable
from slither.exceptions import SlitherException
from slither.solc_parsing.yul.evm_functions import *


class YulLocalVariable(LocalVariable):

    def __init__(self, ast):
        super(LocalVariable, self).__init__()

        assert (ast['nodeType'] == 'YulTypedName')
        self._name = ast['name']
        self._type = ElementaryType('uint256')

        self._location = 'memory'


class YulFunction(Function):

    def __init__(self, ast, root):
        super(YulFunction, self).__init__()

        assert (ast['nodeType'] == 'YulFunctionDefinition')

        self._contract = root.function.contract
        self._contract_declarer = root.function.contract_declarer

        self._name = ast['name']
        self._scope = root.yul_path
        self._counter_nodes = 0

        self._is_implemented = True
        self._contains_assembly = True

        self._node_solc = root.function.node_solc()

        self._entry_point = self.new_node(NodeType.ASSEMBLY, ast['src'])
        self._entry_point.set_yul_child(root, ast['name'])

        self._ast = ast
        self.set_offset(ast['src'], root.function.slither)

    def convert_body(self):
        node = self.new_node(NodeType.ENTRYPOINT, self._ast['src'])
        link_nodes(self.entry_point, node)

        for param in self._ast.get('parameters', []):
            node = convert_yul(self.entry_point, node, param)
            self._parameters.append(self.entry_point.get_yul_local_variable_from_name(param['name']))

        for ret in self._ast.get('returnVariables', []):
            node = convert_yul(self.entry_point, node, ret)
            self._returns.append(self.entry_point.get_yul_local_variable_from_name(ret['name']))

        convert_yul(self.entry_point, node, self._ast['body'])

    def parse_body(self):
        for node in self.nodes:
            node.analyze_expressions(self)

    def node_solc(self):
        return self._node_solc

    def new_node(self, node_type, src):
        node = self._node_solc(node_type, self._counter_nodes)
        node.set_offset(src, self.slither)
        node.set_function(self)
        self._counter_nodes += 1
        self._nodes.append(node)
        return node


###################################################################################
###################################################################################
# region Block conversion
###################################################################################
###################################################################################

"""
The functions in this region, at a high level, will extract the control flow
structures and metadata from the input AST. These include things like function
definitions and local variables.

Each function takes three parameters:
    1)  root is a NodeSolc of NodeType.ASSEMBLY, and stores information at the
        local scope. In Yul, variables are scoped to the function they're
        declared in (except for variables outside the assembly block)
    2)  parent is the last node in the CFG. new nodes should be linked against
        this node
    3)  ast is a dictionary and is the current node in the Yul ast being converted
    
Each function must return a single parameter:
    1) A NodeSolc representing the new end of the CFG

The entrypoint is the function at the end of this region, `convert_yul`, which
dispatches to a specialized function based on a lookup dictionary.
"""


def convert_yul_block(root, parent, ast):
    for statement in ast["statements"]:
        parent = convert_yul(root, parent, statement)
    return parent


def convert_yul_function_definition(root, parent, ast):
    f = YulFunction(ast, root)

    root.function.contract._functions[root.format_canonical_yul_name(f.name)] = f

    f.convert_body()
    f.parse_body()

    return parent


def convert_yul_variable_declaration(root, parent, ast):
    for variable_ast in ast['variables']:
        parent = convert_yul(root, parent, variable_ast)

    node = parent.function.new_node(NodeType.EXPRESSION, ast["src"])
    node.add_unparsed_yul_expression(root, ast)
    link_nodes(parent, node)

    return node


def convert_yul_assignment(root, parent, ast):
    node = parent.function.new_node(NodeType.EXPRESSION, ast["src"])
    node.add_unparsed_yul_expression(root, ast)
    link_nodes(parent, node)
    return node


def convert_yul_expression_statement(root, parent, ast):
    src = ast['src']
    expression_ast = ast['expression']

    expression = parent.function.new_node(NodeType.EXPRESSION, src)
    expression.add_unparsed_yul_expression(root, expression_ast)
    link_nodes(parent, expression)

    return expression


def convert_yul_if(root, parent, ast):
    # we're cheating and pretending that yul supports if/else so we can convert switch cleaner

    src = ast['src']
    condition_ast = ast['condition']
    true_body_ast = ast['body']
    false_body_ast = ast['false_body'] if 'false_body' in ast else None

    condition = parent.function.new_node(NodeType.IF, src)
    end = parent.function.new_node(NodeType.ENDIF, src)

    condition.add_unparsed_yul_expression(root, condition_ast)

    true_body = convert_yul(root, condition, true_body_ast)

    if false_body_ast:
        false_body = convert_yul(root, condition, false_body_ast)
        link_nodes(false_body, end)
    else:
        link_nodes(condition, end)

    link_nodes(parent, condition)
    link_nodes(true_body, end)

    return end


def convert_yul_switch(root, parent, ast):
    """
    This is unfortunate. We don't really want a switch in our IR so we're going to
    translate it into a series of if/else statements.
    """
    cases_ast = ast['cases']
    expression_ast = ast['expression']

    # this variable stores the result of the expression so we don't accidentally compute it more than once
    switch_expr_var = 'switch_expr_{}'.format(ast['src'].replace(':', '_'))

    rewritten_switch = {
        'nodeType': 'YulBlock',
        'src': ast['src'],
        'statements': [
            {
                'nodeType': 'YulVariableDeclaration',
                'src': expression_ast['src'],
                'variables': [
                    {
                        'nodeType': 'YulTypedName',
                        'src': expression_ast['src'],
                        'name': switch_expr_var,
                        'type': '',
                    },
                ],
                'value': expression_ast,
            },
        ],
    }

    last_if = None

    default_ast = None

    for case_ast in cases_ast:
        body_ast = case_ast['body']
        value_ast = case_ast['value']

        if value_ast == 'default':
            default_ast = case_ast
            continue

        current_if = {
            'nodeType': 'YulIf',
            'src': case_ast['src'],
            'condition': {
                'nodeType': 'YulFunctionCall',
                'src': case_ast['src'],
                'functionName': {
                    'nodeType': 'YulIdentifier',
                    'src': case_ast['src'],
                    'name': 'eq',
                },
                'arguments': [
                    {
                        'nodeType': 'YulIdentifier',
                        'src': case_ast['src'],
                        'name': switch_expr_var,
                    },
                    value_ast,
                ]
            },
            'body': body_ast,
        }

        if last_if:
            last_if['false_body'] = current_if
        else:
            rewritten_switch['statements'].append(current_if)

        last_if = current_if

    if default_ast:
        body_ast = default_ast['body']

        if last_if:
            last_if['false_body'] = body_ast
        else:
            rewritten_switch['statements'].append(body_ast)

    return convert_yul(root, parent, rewritten_switch)


def convert_yul_for_loop(root, parent, ast):
    pre_ast = ast['pre']
    condition_ast = ast['condition']
    post_ast = ast['post']
    body_ast = ast['body']

    start_loop = parent.function.new_node(NodeType.STARTLOOP, ast['src'])
    end_loop = parent.function.new_node(NodeType.ENDLOOP, ast['src'])

    link_nodes(parent, start_loop)

    pre = convert_yul(root, start_loop, pre_ast)

    condition = parent.function.new_node(NodeType.IFLOOP, condition_ast['src'])
    condition.add_unparsed_yul_expression(root, condition_ast)
    link_nodes(pre, condition)

    link_nodes(condition, end_loop)

    body = convert_yul(root, condition, body_ast)

    post = convert_yul(root, body, post_ast)

    link_nodes(post, condition)

    return end_loop


def convert_yul_break(root, parent, ast):
    break_ = parent.function.new_node(NodeType.BREAK, ast['src'])
    link_nodes(parent, break_)
    return break_


def convert_yul_continue(root, parent, ast):
    continue_ = parent.function.new_node(NodeType.CONTINUE, ast['src'])
    link_nodes(parent, continue_)
    return continue_


def convert_yul_leave(root, parent, ast):
    leave = parent.function.new_node(NodeType.RETURN, ast['src'])
    link_nodes(parent, leave)
    return leave


def convert_yul_typed_name(root, parent, ast):
    var = YulLocalVariable(ast)
    var.set_function(root.function)
    var.set_offset(ast['src'], root.slither)

    root.add_yul_local_variable(var)

    node = parent.function.new_node(NodeType.VARIABLE, ast['src'])
    node.add_variable_declaration(var)
    link_nodes(parent, node)

    return node


def convert_yul_unsupported(root, parent, ast):
    raise SlitherException(f"no converter available for {ast['nodeType']} {json.dumps(ast, indent=2)}")


def convert_yul(root, parent, ast):
    return converters.get(ast['nodeType'], convert_yul_unsupported)(root, parent, ast)


converters = {
    'YulBlock': convert_yul_block,
    'YulFunctionDefinition': convert_yul_function_definition,
    'YulVariableDeclaration': convert_yul_variable_declaration,
    'YulAssignment': convert_yul_assignment,
    'YulExpressionStatement': convert_yul_expression_statement,
    'YulIf': convert_yul_if,
    'YulSwitch': convert_yul_switch,
    'YulForLoop': convert_yul_for_loop,
    'YulBreak': convert_yul_break,
    'YulContinue': convert_yul_continue,
    'YulLeave': convert_yul_leave,
    'YulTypedName': convert_yul_typed_name,
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


def _parse_yul_assignment_common(root, node, ast, key):
    lhs = [parse_yul(root, node, arg) for arg in ast[key]]
    rhs = parse_yul(root, node, ast['value'])

    return AssignmentOperation(vars_to_val(lhs), rhs, AssignmentOperationType.ASSIGN, vars_to_typestr(lhs))


def parse_yul_variable_declaration(root, node, ast):
    """
    We already created variables in the conversion phase, so just do
    the assignment
    """

    if not ast['value']:
        return None

    return _parse_yul_assignment_common(root, node, ast, 'variables')


def parse_yul_assignment(root, node, ast):
    return _parse_yul_assignment_common(root, node, ast, 'variableNames')


def parse_yul_function_call(root, node, ast):
    args = [parse_yul(root, node, arg) for arg in ast['arguments']]
    ident = parse_yul(root, node, ast['functionName'])

    if isinstance(ident.value, YulBuiltin):
        name = ident.value.name
        if name in binary_ops:
            if name in ['shl', 'shr', 'sar']:
                # lmao ok
                return BinaryOperation(args[1], args[0], binary_ops[name])

            return BinaryOperation(args[0], args[1], binary_ops[name])

        if name in unary_ops:
            return UnaryOperation(args[0], unary_ops[name])

        ident = Identifier(SolidityFunction(format_function_descriptor(ident.value.name)))

    if isinstance(ident.value, Function):
        return CallExpression(ident, args, vars_to_typestr(ident.value.returns))
    elif isinstance(ident.value, SolidityFunction):
        return CallExpression(ident, args, vars_to_typestr(ident.value.return_type))
    else:
        raise SlitherException(f"unexpected function call target type {str(type(ident.value))}")


def parse_yul_identifier(root, node, ast):
    name = ast['name']

    if name in builtins:
        return Identifier(YulBuiltin(name))

    # check function-scoped variables
    variable = root.function.get_local_variable_from_name(name)
    if variable:
        return Identifier(variable)

    # check yul-scoped variable
    variable = root.get_yul_local_variable_from_name(name)
    if variable:
        return Identifier(variable)

    # check yul-scoped function
    # note that a function can recurse into itself, so we have two canonical names
    # to check (but only one of them can be valid)

    functions = root.function.contract_declarer._functions

    canonical_name = root.format_canonical_yul_name(name)
    if canonical_name in functions:
        return Identifier(functions[canonical_name])

    canonical_name = root.format_canonical_yul_name(name, -1)
    if canonical_name in functions:
        return Identifier(functions[canonical_name])

    # check for magic suffixes
    if name.endswith("_slot"):
        potential_name = name[:-5]
        var = root.function.contract.get_state_variable_from_name(potential_name)
        if var:
            return Identifier(SolidityVariable(name))
    if name.endswith("_offset"):
        potential_name = name[:-7]
        var = root.function.contract.get_state_variable_from_name(potential_name)
        if var:
            return Identifier(SolidityVariable(name))

    raise SlitherException(f"unresolved reference to identifier {name}")


def parse_yul_literal(root, node, ast):
    type_ = ast['type']
    value = ast['value']

    if not type_:
        type_ = 'bool' if value in ['true', 'false'] else 'uint256'

    return Literal(value, ElementaryType(type_))


def parse_yul_typed_name(root, node, ast):
    var = root.get_yul_local_variable_from_name(ast['name'])

    i = Identifier(var)
    i._type = var.type
    return i


def parse_yul_unsupported(root, node, ast):
    raise SlitherException(f"no parser available for {ast['nodeType']} {json.dumps(ast, indent=2)}")


def parse_yul(root, node, ast):
    op = parsers.get(ast['nodeType'], parse_yul_unsupported)(root, node, ast)
    if op:
        op.set_offset(ast["src"], root.slither)
    return op


parsers = {
    'YulVariableDeclaration': parse_yul_variable_declaration,
    'YulAssignment': parse_yul_assignment,
    'YulFunctionCall': parse_yul_function_call,
    'YulIdentifier': parse_yul_identifier,
    'YulTypedName': parse_yul_typed_name,
    'YulLiteral': parse_yul_literal,
}


# endregion
###################################################################################
###################################################################################

def vars_to_typestr(rets):
    if len(rets) == 0:
        return ""
    if len(rets) == 1:
        return str(rets[0].type)
    return "tuple({})".format(",".join(str(ret.type) for ret in rets))


def vars_to_val(vars):
    if len(vars) == 1:
        return vars[0]
    return TupleExpression(vars)
