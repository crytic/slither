import logging
import re
from slither.core.expressions.unaryOperation import UnaryOperation, UnaryOperationType
from slither.core.expressions.binaryOperation import BinaryOperation, BinaryOperationType
from slither.core.expressions.literal import Literal
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.superIdentifier import SuperIdentifier
from slither.core.expressions.indexAccess import IndexAccess
from slither.core.expressions.memberAccess import MemberAccess
from slither.core.expressions.tupleExpression import TupleExpression
from slither.core.expressions.conditionalExpression import ConditionalExpression
from slither.core.expressions.assignmentOperation import AssignmentOperation, AssignmentOperationType
from slither.core.expressions.typeConversion import TypeConversion
from slither.core.expressions.callExpression import CallExpression
from slither.core.expressions.superCallExpression import SuperCallExpression
from slither.core.expressions.newArray import NewArray
from slither.core.expressions.newContract import NewContract
from slither.core.expressions.newElementaryType import NewElementaryType
from slither.core.expressions.elementaryTypeNameExpression import ElementaryTypeNameExpression

from slither.solcParsing.solidityTypes.typeParsing import parse_type, UnknownType

from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function

from slither.core.declarations.solidityVariables import SOLIDITY_VARIABLES, SOLIDITY_FUNCTIONS, SOLIDITY_VARIABLES_COMPOSED
from slither.core.declarations.solidityVariables import SolidityVariable, SolidityFunction, SolidityVariableComposed, solidity_function_signature

from slither.core.solidityTypes.elementaryType import ElementaryType
from slither.core.solidityTypes.functionType import FunctionType

logger = logging.getLogger("ExpressionParsing")

class VariableNotFound(Exception): pass

def find_variable(var_name, caller_context):

    if isinstance(caller_context, Contract):
        function = None
        contract = caller_context
    elif isinstance(caller_context, Function):
        function = caller_context
        contract = function.contract
    else:
        logger.error('Incorrect caller context')
        exit(-1)

    if function:
        func_variables = function.variables_as_dict()
        if var_name in func_variables:
            return func_variables[var_name]
        # A local variable can be a pointer
        # for example
        # function test(function(uint) internal returns(bool) t) interna{
        # Will have a local variable t which will match the signature
        # t(uint256)
        func_variables_ptr = {f.name + f.type.parameters_signature : f for f in function.variables
                              if isinstance(f.type, FunctionType)}
        if var_name in func_variables_ptr:
            return func_variables_ptr[var_name]

    contract_variables = contract.variables_as_dict()
    if var_name in contract_variables:
        return contract_variables[var_name]

    functions = contract.functions_as_dict()
    if var_name in functions:
        return functions[var_name]

    modifiers = contract.modifiers_as_dict()
    if var_name in modifiers:
        return modifiers[var_name]

    structures = contract.structures_as_dict()
    if var_name in structures:
        return structures[var_name]

    events = contract.events_as_dict()
    if var_name in events:
        return events[var_name]

    enums = contract.enums_as_dict()
    if var_name in enums:
        return enums[var_name]

    # If the enum is refered as its name rather than its canonicalName
    enums = {e.name: e for e in contract.enums}
    if var_name in enums:
        return enums[var_name]

    # Could refer to any enum
    all_enums = [c.enums_as_dict() for c in contract.slither.contracts]
    all_enums = {k: v for d in all_enums for k, v in d.items()}
    if var_name in all_enums:
        return all_enums[var_name]

    if var_name in SOLIDITY_VARIABLES:
        return SolidityVariable(var_name)

    if var_name in SOLIDITY_FUNCTIONS:
        return SolidityFunction(var_name)

    contracts = contract.slither.contracts_as_dict()
    if var_name in contracts:
        return contracts[var_name]

    raise VariableNotFound('Variable not found: {}'.format(var_name))


def parse_call(expression, caller_context):
    attributes = expression['attributes']

    type_conversion = attributes['type_conversion']

    children = expression['children']
    if type_conversion:
        assert len(children) == 2

        type_call = parse_type(UnknownType(attributes['type']), caller_context)
        type_info = children[0]
        assert type_info['name'] in ['ElementaryTypenameExpression',
                                     'ElementaryTypeNameExpression',
                                     'Identifier',
                                     'TupleExpression',
                                     'IndexAccess',
                                     'MemberAccess']

        expression = parse_expression(children[1], caller_context)
        t = TypeConversion(expression, type_call)
        return t

    assert children

    type_call = attributes['type']
    called = parse_expression(children[0], caller_context)
    arguments = [parse_expression(a, caller_context) for a in children[1::]]

    if isinstance(called, SuperCallExpression):
        return SuperCallExpression(called, arguments, type_call)
    return CallExpression(called, arguments, type_call)

def parse_super_name(expression):
    assert expression['name'] == 'MemberAccess'
    attributes = expression['attributes']
    base_name = attributes['member_name']

    arguments = attributes['type']
    assert arguments.startswith('function ')
    # remove function (...()
    arguments = arguments[len('function '):]

    arguments = filter_name(arguments)
    if ' ' in arguments:
        arguments = arguments[:arguments.find(' ')]

    return base_name+arguments

def filter_name(value):
    value = value.replace(' memory', '')
    value = value.replace(' storage', '')
    value = value.replace(' external', '')
    value = value.replace(' internal', '')
    value = value.replace('struct ', '')
    value = value.replace('contract ', '')
    value = value.replace('enum ', '')
    value = value.replace(' ref', '')
    value = value.replace(' pointer', '')
    value = value.replace(' pure', '')
    value = value.replace(' view', '')
    value = value.replace(' constant', '')
    value = value.replace('function (', 'function(')
    value = value.replace('returns (', 'returns(')

    # remove the text remaining after functio(...)
    # which should only be ..returns(...)
    # nested parenthesis so we use a system of counter on parenthesis
    idx = value.find('(')
    if idx:
        counter = 1
        max_idx = len(value)
        while counter:
            assert idx < max_idx
            idx = idx +1
            if value[idx] == '(':
                counter += 1
            elif value[idx] == ')':
                counter -= 1
        value = value[:idx+1]
    return value

def parse_expression(expression, caller_context):
    """

    Returns:
        str: expression
    """
    #  Expression
    #    = Expression ('++' | '--')
    #    | NewExpression
    #    | IndexAccess
    #    | MemberAccess
    #    | FunctionCall
    #    | '(' Expression ')'
    #    | ('!' | '~' | 'delete' | '++' | '--' | '+' | '-') Expression
    #    | Expression '**' Expression
    #    | Expression ('*' | '/' | '%') Expression
    #    | Expression ('+' | '-') Expression
    #    | Expression ('<<' | '>>') Expression
    #    | Expression '&' Expression
    #    | Expression '^' Expression
    #    | Expression '|' Expression
    #    | Expression ('<' | '>' | '<=' | '>=') Expression
    #    | Expression ('==' | '!=') Expression
    #    | Expression '&&' Expression
    #    | Expression '||' Expression
    #    | Expression '?' Expression ':' Expression
    #    | Expression ('=' | '|=' | '^=' | '&=' | '<<=' | '>>=' | '+=' | '-=' | '*=' | '/=' | '%=') Expression
    #    | PrimaryExpression

    # The AST naming does not follow the spec 
    name = expression['name']

    if name == 'UnaryOperation':
        attributes = expression['attributes']
        assert 'prefix' in attributes
        operation_type = UnaryOperationType.get_type(attributes['operator'], attributes['prefix'])

        assert len(expression['children']) == 1
        expression = parse_expression(expression['children'][0], caller_context)
        unary_op = UnaryOperation(expression, operation_type)
        return unary_op

    elif name == 'BinaryOperation':
        attributes = expression['attributes']
        operation_type = BinaryOperationType.get_type(attributes['operator'])

        assert len(expression['children']) == 2
        left_expression = parse_expression(expression['children'][0], caller_context)
        right_expression = parse_expression(expression['children'][1], caller_context)
        binary_op = BinaryOperation(left_expression, right_expression, operation_type)
        return binary_op

    elif name == 'FunctionCall':
        return  parse_call(expression, caller_context)

    elif name == 'TupleExpression':
        if 'children' not in expression :
            attributes = expression['attributes']
            components = attributes['components']
            expressions = [parse_expression(c, caller_context) if c else None for c in components]
        else:
            expressions = [parse_expression(e, caller_context) for e in expression['children']]
        t = TupleExpression(expressions)
        return t

    elif name == 'Conditional':
        children = expression['children']
        assert len(children) == 3
        if_expression = parse_expression(children[0], caller_context)
        then_expression = parse_expression(children[1], caller_context)
        else_expression = parse_expression(children[2], caller_context)
        conditional = ConditionalExpression(if_expression, then_expression, else_expression)
        return conditional

    elif name == 'Assignment':
        attributes = expression['attributes']
        children = expression['children']
        assert len(expression['children']) == 2

        left_expression = parse_expression(children[0], caller_context)
        right_expression = parse_expression(children[1], caller_context)
        operation_type = AssignmentOperationType.get_type(attributes['operator'])
        operation_return_type = attributes['type']

        assignement = AssignmentOperation(left_expression, right_expression, operation_type, operation_return_type)
        return assignement

    elif name == 'Literal':
        assert 'children' not in expression
        value = expression['attributes']['value']
        literal = Literal(value)
        return literal

    elif name == 'Identifier':
        assert 'children' not in expression
        value = expression['attributes']['value']
        if 'type' in expression['attributes']:
            t = expression['attributes']['type']
            if t:
                found = re.findall('[struct|enum|function|modifier] \(([\[\] ()a-zA-Z0-9\.,_]*)\)', t)
                assert len(found) <= 1
                if found:
                    value = value+'('+found[0]+')'
                    value = filter_name(value)

        var = find_variable(value, caller_context)

        identifier = Identifier(var)
        return identifier

    elif name == 'IndexAccess':
        index_type = expression['attributes']['type']
        children = expression['children']
        assert len(children) == 2
        left_expression = parse_expression(children[0], caller_context)
        right_expression = parse_expression(children[1], caller_context)
        index = IndexAccess(left_expression, right_expression, index_type)
        return index

    elif name == 'MemberAccess':
        member_name = expression['attributes']['member_name']
        member_type = expression['attributes']['type']
        children = expression['children']
        assert len(children) == 1
        member_expression = parse_expression(children[0], caller_context)
        if str(member_expression) == 'super':
            super_name = parse_super_name(expression)
            if isinstance(caller_context, Contract):
                inheritances = caller_context.inheritances
            else:
                assert isinstance(caller_context, Function)
                inheritances = caller_context.contract.inheritances
            var = None
            for father in inheritances:
                try:
                    var = find_variable(super_name, father)
                    break
                except VariableNotFound:
                    continue
            if var is None:
                raise VariableNotFound('Variable not found: {}'.format(super_name))
            return SuperIdentifier(var)
        member_access = MemberAccess(member_name, member_type, member_expression)
        if str(member_access) in SOLIDITY_VARIABLES_COMPOSED:
            return Identifier(SolidityVariableComposed(str(member_access)))
        return member_access

    elif name == 'ElementaryTypeNameExpression':
        # nop exression
        # uint;
        assert 'children' not in expression
        value = expression['attributes']['value']
        t = parse_type(UnknownType(value), caller_context)

        return ElementaryTypeNameExpression(t)


    # NewExpression is not a root expression, it's always the child of another expression
    elif name == 'NewExpression':
        new_type = expression['attributes']['type']

        children = expression['children']
        assert len(children) == 1
        #new_expression = parse_expression(children[0])

        child = children[0]

        if child['name'] == 'ArrayTypeName':
            depth = 0
            while child['name'] == 'ArrayTypeName':
                # Note: dont conserve the size of the array if provided
                #assert len(child['children']) == 1
                child = child['children'][0]
                depth += 1

            if child['name'] == 'ElementaryTypeName':
                array_type = ElementaryType(child['attributes']['name'])
            elif child['name'] == 'UserDefinedTypeName':
                array_type = parse_type(UnknownType(child['attributes']['name']), caller_context)
            else:
                logger.error('Incorrect type array {}'.format(child))
                exit(-1)
            array = NewArray(depth, array_type)
            return array

        if child['name'] == 'ElementaryTypeName':
            elem_type = ElementaryType(child['attributes']['name'])
            new_elem = NewElementaryType(elem_type)
            return new_elem

        assert child['name'] == 'UserDefinedTypeName'

        contract_name = child['attributes']['name']
        new = NewContract(contract_name)
        return new

    elif name == 'ModifierInvocation':

        children = expression['children']
        called = parse_expression(children[0], caller_context)
        arguments = [parse_expression(a, caller_context) for a in children[1::]]

        call = CallExpression(called, arguments, 'Modifier')
        return call

    logger.error('Expression not parsed %s'%name)
    exit(-1)
