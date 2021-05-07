import logging
import re
from typing import Dict, TYPE_CHECKING, Optional, Union, List, Tuple

from slither.core.declarations import Event, Enum, Structure
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations.solidity_variables import (
    SOLIDITY_FUNCTIONS,
    SOLIDITY_VARIABLES,
    SOLIDITY_VARIABLES_COMPOSED,
    SolidityFunction,
    SolidityVariable,
    SolidityVariableComposed,
    SolidityImportPlaceHolder,
)
from slither.core.expressions.assignment_operation import (
    AssignmentOperation,
    AssignmentOperationType,
)
from slither.core.expressions.binary_operation import (
    BinaryOperation,
    BinaryOperationType,
)
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.conditional_expression import ConditionalExpression
from slither.core.expressions.elementary_type_name_expression import ElementaryTypeNameExpression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.index_access import IndexAccess
from slither.core.expressions.literal import Literal
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.new_array import NewArray
from slither.core.expressions.new_contract import NewContract
from slither.core.expressions.new_elementary_type import NewElementaryType
from slither.core.expressions.super_call_expression import SuperCallExpression
from slither.core.expressions.super_identifier import SuperIdentifier
from slither.core.expressions.tuple_expression import TupleExpression
from slither.core.expressions.type_conversion import TypeConversion
from slither.core.expressions.unary_operation import UnaryOperation, UnaryOperationType
from slither.core.solidity_types import (
    ArrayType,
    ElementaryType,
    FunctionType,
    MappingType,
)
from slither.core.variables.variable import Variable
from slither.exceptions import SlitherError
from slither.solc_parsing.exceptions import ParsingError, VariableNotFound
from slither.solc_parsing.solidity_types.type_parsing import UnknownType, parse_type

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression
    from slither.solc_parsing.declarations.function import FunctionSolc
    from slither.solc_parsing.declarations.contract import ContractSolc
    from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc
    from slither.core.compilation_unit import SlitherCompilationUnit

logger = logging.getLogger("ExpressionParsing")

# pylint: disable=anomalous-backslash-in-string,import-outside-toplevel,too-many-branches,too-many-locals

###################################################################################
###################################################################################
# region Helpers
###################################################################################
###################################################################################

CallerContext = Union["ContractSolc", "FunctionSolc"]


def get_pointer_name(variable: Variable):
    curr_type = variable.type
    while isinstance(curr_type, (ArrayType, MappingType)):
        if isinstance(curr_type, ArrayType):
            curr_type = curr_type.type
        else:
            assert isinstance(curr_type, MappingType)
            curr_type = curr_type.type_to

    if isinstance(curr_type, FunctionType):
        return variable.name + curr_type.parameters_signature
    return None


def _find_variable_from_ref_declaration(
    referenced_declaration: Optional[int],
    all_contracts: List["Contract"],
    all_functions_parser: List["FunctionSolc"],
) -> Optional[Union[Contract, Function]]:
    if referenced_declaration is None:
        return None
    # id of the contracts is the referenced declaration
    # This is not true for the functions, as we dont always have the referenced_declaration
    # But maybe we could? (TODO)
    for contract_candidate in all_contracts:
        if contract_candidate.id == referenced_declaration:
            return contract_candidate
    for function_candidate in all_functions_parser:
        if (
            function_candidate.referenced_declaration == referenced_declaration
            and not function_candidate.underlying_function.is_shadowed
        ):
            return function_candidate.underlying_function
    return None


def _find_variable_in_function_parser(
    var_name: str,
    function_parser: Optional["FunctionSolc"],
    referenced_declaration: Optional[int] = None,
) -> Optional[Variable]:
    if function_parser is None:
        return None
    # We look for variable declared with the referencedDeclaration attr
    func_variables_renamed = function_parser.variables_renamed
    if referenced_declaration and referenced_declaration in func_variables_renamed:
        return func_variables_renamed[referenced_declaration].underlying_variable
    # If not found, check for name
    func_variables = function_parser.underlying_function.variables_as_dict
    if var_name in func_variables:
        return func_variables[var_name]
    # A local variable can be a pointer
    # for example
    # function test(function(uint) internal returns(bool) t) interna{
    # Will have a local variable t which will match the signature
    # t(uint256)
    func_variables_ptr = {
        get_pointer_name(f): f for f in function_parser.underlying_function.variables
    }
    if var_name and var_name in func_variables_ptr:
        return func_variables_ptr[var_name]

    return None


def _find_top_level(
    var_name: str, sl: "SlitherCompilationUnit"
) -> Optional[Union[Enum, Structure, SolidityVariable]]:
    structures_top_level = sl.structures_top_level
    for st in structures_top_level:
        if st.name == var_name:
            return st

    enums_top_level = sl.enums_top_level
    for enum in enums_top_level:
        if enum.name == var_name:
            return enum

    for import_directive in sl.import_directives:
        if import_directive.alias == var_name:
            return SolidityImportPlaceHolder(import_directive)

    return None


def _find_in_contract(
    var_name: str,
    contract: Optional[Contract],
    contract_declarer: Optional[Contract],
    is_super: bool,
) -> Optional[Union[Variable, Function, Contract, Event, Enum, Structure,]]:
    if contract is None or contract_declarer is None:
        return None

    # variable are looked from the contract declarer
    contract_variables = contract_declarer.variables_as_dict
    if var_name in contract_variables:
        return contract_variables[var_name]

    # A state variable can be a pointer
    conc_variables_ptr = {get_pointer_name(f): f for f in contract_declarer.variables}
    if var_name and var_name in conc_variables_ptr:
        return conc_variables_ptr[var_name]

    if is_super:
        getter_available = lambda f: f.functions_declared
        d = {f.canonical_name: f for f in contract.functions}
        functions = {
            f.full_name: f
            for f in contract_declarer.available_elements_from_inheritances(
                d, getter_available
            ).values()
        }
    else:
        functions = contract.available_functions_as_dict()
    if var_name in functions:
        return functions[var_name]

    if is_super:
        getter_available = lambda m: m.modifiers_declared
        d = {m.canonical_name: m for m in contract.modifiers}
        modifiers = {
            m.full_name: m
            for m in contract_declarer.available_elements_from_inheritances(
                d, getter_available
            ).values()
        }
    else:
        modifiers = contract.available_modifiers_as_dict()
    if var_name in modifiers:
        return modifiers[var_name]

    # structures are looked on the contract declarer
    structures = contract.structures_as_dict
    if var_name in structures:
        return structures[var_name]

    events = contract.events_as_dict
    if var_name in events:
        return events[var_name]

    enums = contract.enums_as_dict
    if var_name in enums:
        return enums[var_name]

    # If the enum is refered as its name rather than its canonicalName
    enums = {e.name: e for e in contract.enums}
    if var_name in enums:
        return enums[var_name]

    return None


def _find_variable_init(
    caller_context: CallerContext,
) -> Tuple[
    List[Contract],
    Union[List["FunctionSolc"]],
    "SlitherCompilationUnit",
    "SlitherCompilationUnitSolc",
]:
    from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc
    from slither.solc_parsing.declarations.contract import ContractSolc
    from slither.solc_parsing.declarations.function import FunctionSolc

    direct_contracts: List[Contract]
    direct_functions_parser: List[FunctionSolc]

    if isinstance(caller_context, SlitherCompilationUnitSolc):
        direct_contracts = []
        direct_functions_parser = []
        sl = caller_context.compilation_unit
        sl_parser = caller_context
    elif isinstance(caller_context, ContractSolc):
        direct_contracts = [caller_context.underlying_contract]
        direct_functions_parser = caller_context.functions_parser + caller_context.modifiers_parser
        sl = caller_context.slither_parser.compilation_unit
        sl_parser = caller_context.slither_parser
    elif isinstance(caller_context, FunctionSolc):
        if caller_context.contract_parser:
            direct_contracts = [caller_context.contract_parser.underlying_contract]
            direct_functions_parser = (
                caller_context.contract_parser.functions_parser
                + caller_context.contract_parser.modifiers_parser
            )
        else:
            # Top level functions
            direct_contracts = []
            direct_functions_parser = []
        sl = caller_context.underlying_function.compilation_unit
        sl_parser = caller_context.slither_parser
    else:
        raise SlitherError(
            f"{type(caller_context)} ({caller_context} is not valid for find_variable"
        )

    return direct_contracts, direct_functions_parser, sl, sl_parser


def find_variable(
    var_name: str,
    caller_context: CallerContext,
    referenced_declaration: Optional[int] = None,
    is_super=False,
) -> Union[
    Variable,
    Function,
    Contract,
    SolidityVariable,
    SolidityFunction,
    Event,
    Enum,
    Structure,
]:
    from slither.solc_parsing.declarations.function import FunctionSolc
    from slither.solc_parsing.declarations.contract import ContractSolc

    # variable are looked from the contract declarer
    # functions can be shadowed, but are looked from the contract instance, rather than the contract declarer
    # the difference between function and variable come from the fact that an internal call, or an variable access
    # in a function does not behave similariy, for example in:
    # contract C{
    #   function f(){
    #     state_var = 1
    #     f2()
    #  }
    # state_var will refer to C.state_var, no mater if C is inherited
    # while f2() will refer to the function definition of the inherited contract (C.f2() in the context of C, or
    # the contract inheriting from C)
    # for events it's unclear what should be the behavior, as they can be shadowed, but there is not impact
    # structure/enums cannot be shadowed

    direct_contracts, direct_functions_parser, sl, sl_parser = _find_variable_init(caller_context)

    all_contracts = sl.contracts
    all_functions_parser = sl_parser.all_functions_and_modifiers_parser

    # Only look for reference declaration in the direct contract, see comment at the end
    # Reference looked are split between direct and all
    # Because functions are copied between contracts, two functions can have the same ref
    # So we need to first look with respect to the direct context

    ret = _find_variable_from_ref_declaration(
        referenced_declaration, direct_contracts, direct_functions_parser
    )
    if ret:
        return ret

    function_parser: Optional[FunctionSolc] = (
        caller_context if isinstance(caller_context, FunctionSolc) else None
    )
    ret = _find_variable_in_function_parser(var_name, function_parser, referenced_declaration)
    if ret:
        return ret

    contract: Optional[Contract] = None
    contract_declarer: Optional[Contract] = None
    if isinstance(caller_context, ContractSolc):
        contract = caller_context.underlying_contract
        contract_declarer = caller_context.underlying_contract
    elif isinstance(caller_context, FunctionSolc):
        underlying_func = caller_context.underlying_function
        # If contract_parser is set to None, then underlying_function is a functionContract
        assert isinstance(underlying_func, FunctionContract)
        contract = underlying_func.contract
        contract_declarer = underlying_func.contract_declarer

    ret = _find_in_contract(var_name, contract, contract_declarer, is_super)
    if ret:
        return ret

    # Could refer to any enum
    all_enumss = [c.enums_as_dict for c in sl.contracts]
    all_enums = {k: v for d in all_enumss for k, v in d.items()}
    if var_name in all_enums:
        return all_enums[var_name]

    contracts = sl.contracts_as_dict
    if var_name in contracts:
        return contracts[var_name]

    if var_name in SOLIDITY_VARIABLES:
        return SolidityVariable(var_name)

    if var_name in SOLIDITY_FUNCTIONS:
        return SolidityFunction(var_name)

    # Top level must be at the end, if nothing else was found
    ret = _find_top_level(var_name, sl)
    if ret:
        return ret

    # Look from reference declaration in all the contracts at the end
    # Because they are many instances where this can't be trusted
    # For example in
    # contract A{
    #     function _f() internal view returns(uint){
    #         return 1;
    #     }
    #
    #     function get() public view returns(uint){
    #         return _f();
    #     }
    # }
    #
    # contract B is A{
    #     function _f() internal view returns(uint){
    #         return 2;
    #     }
    #
    # }
    # get's AST will say that the ref declaration for _f() is A._f(), but in the context of B, its not

    ret = _find_variable_from_ref_declaration(
        referenced_declaration, all_contracts, all_functions_parser
    )
    if ret:
        return ret

    raise VariableNotFound("Variable not found: {} (context {})".format(var_name, caller_context))


# endregion
###################################################################################
###################################################################################
# region Filtering
###################################################################################
###################################################################################


def filter_name(value: str) -> str:
    value = value.replace(" memory", "")
    value = value.replace(" storage", "")
    value = value.replace(" external", "")
    value = value.replace(" internal", "")
    value = value.replace("struct ", "")
    value = value.replace("contract ", "")
    value = value.replace("enum ", "")
    value = value.replace(" ref", "")
    value = value.replace(" pointer", "")
    value = value.replace(" pure", "")
    value = value.replace(" view", "")
    value = value.replace(" constant", "")
    value = value.replace(" payable", "")
    value = value.replace("function (", "function(")
    value = value.replace("returns (", "returns(")

    # remove the text remaining after functio(...)
    # which should only be ..returns(...)
    # nested parenthesis so we use a system of counter on parenthesis
    idx = value.find("(")
    if idx:
        counter = 1
        max_idx = len(value)
        while counter:
            assert idx < max_idx
            idx = idx + 1
            if value[idx] == "(":
                counter += 1
            elif value[idx] == ")":
                counter -= 1
        value = value[: idx + 1]
    return value


# endregion

###################################################################################
###################################################################################
# region Parsing
###################################################################################
###################################################################################


def parse_call(expression: Dict, caller_context):  # pylint: disable=too-many-statements
    src = expression["src"]
    if caller_context.is_compact_ast:
        attributes = expression
        type_conversion = expression["kind"] == "typeConversion"
        type_return = attributes["typeDescriptions"]["typeString"]

    else:
        attributes = expression["attributes"]
        type_conversion = attributes["type_conversion"]
        type_return = attributes["type"]

    if type_conversion:
        type_call = parse_type(UnknownType(type_return), caller_context)

        if caller_context.is_compact_ast:
            assert len(expression["arguments"]) == 1
            expression_to_parse = expression["arguments"][0]
        else:
            children = expression["children"]
            assert len(children) == 2
            type_info = children[0]
            expression_to_parse = children[1]
            assert type_info["name"] in [
                "ElementaryTypenameExpression",
                "ElementaryTypeNameExpression",
                "Identifier",
                "TupleExpression",
                "IndexAccess",
                "MemberAccess",
            ]

        expression = parse_expression(expression_to_parse, caller_context)
        t = TypeConversion(expression, type_call)
        t.set_offset(src, caller_context.compilation_unit)
        return t

    call_gas = None
    call_value = None
    call_salt = None
    if caller_context.is_compact_ast:
        called = parse_expression(expression["expression"], caller_context)
        # If the next expression is a FunctionCallOptions
        # We can here the gas/value information
        # This is only available if the syntax is {gas: , value: }
        # For the .gas().value(), the member are considered as function call
        # And converted later to the correct info (convert.py)
        if expression["expression"][caller_context.get_key()] == "FunctionCallOptions":
            call_with_options = expression["expression"]
            for idx, name in enumerate(call_with_options.get("names", [])):
                option = parse_expression(call_with_options["options"][idx], caller_context)
                if name == "value":
                    call_value = option
                if name == "gas":
                    call_gas = option
                if name == "salt":
                    call_salt = option
        arguments = []
        if expression["arguments"]:
            arguments = [parse_expression(a, caller_context) for a in expression["arguments"]]
    else:
        children = expression["children"]
        called = parse_expression(children[0], caller_context)
        arguments = [parse_expression(a, caller_context) for a in children[1::]]

    if isinstance(called, SuperCallExpression):
        sp = SuperCallExpression(called, arguments, type_return)
        sp.set_offset(expression["src"], caller_context.compilation_unit)
        return sp
    call_expression = CallExpression(called, arguments, type_return)
    call_expression.set_offset(src, caller_context.compilation_unit)

    # Only available if the syntax {gas:, value:} was used
    call_expression.call_gas = call_gas
    call_expression.call_value = call_value
    call_expression.call_salt = call_salt
    return call_expression


def parse_super_name(expression: Dict, is_compact_ast: bool) -> str:
    if is_compact_ast:
        assert expression["nodeType"] == "MemberAccess"
        base_name = expression["memberName"]
        arguments = expression["typeDescriptions"]["typeString"]
    else:
        assert expression["name"] == "MemberAccess"
        attributes = expression["attributes"]
        base_name = attributes["member_name"]
        arguments = attributes["type"]

    assert arguments.startswith("function ")
    # remove function (...()
    arguments = arguments[len("function ") :]

    arguments = filter_name(arguments)
    if " " in arguments:
        arguments = arguments[: arguments.find(" ")]

    return base_name + arguments


def _parse_elementary_type_name_expression(
    expression: Dict, is_compact_ast: bool, caller_context
) -> ElementaryTypeNameExpression:
    # nop exression
    # uint;
    if is_compact_ast:
        value = expression["typeName"]
    else:
        if "children" in expression:
            value = expression["children"][0]["attributes"]["name"]
        else:
            value = expression["attributes"]["value"]
    if isinstance(value, dict):
        t = parse_type(value, caller_context)
    else:
        t = parse_type(UnknownType(value), caller_context)
    e = ElementaryTypeNameExpression(t)
    e.set_offset(expression["src"], caller_context.compilation_unit)
    return e


def parse_expression(expression: Dict, caller_context: CallerContext) -> "Expression":
    # pylint: disable=too-many-nested-blocks,too-many-statements
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
    name = expression[caller_context.get_key()]
    is_compact_ast = caller_context.is_compact_ast
    src = expression["src"]

    if name == "UnaryOperation":
        if is_compact_ast:
            attributes = expression
        else:
            attributes = expression["attributes"]
        assert "prefix" in attributes
        operation_type = UnaryOperationType.get_type(attributes["operator"], attributes["prefix"])

        if is_compact_ast:
            expression = parse_expression(expression["subExpression"], caller_context)
        else:
            assert len(expression["children"]) == 1
            expression = parse_expression(expression["children"][0], caller_context)
        unary_op = UnaryOperation(expression, operation_type)
        unary_op.set_offset(src, caller_context.compilation_unit)
        return unary_op

    if name == "BinaryOperation":
        if is_compact_ast:
            attributes = expression
        else:
            attributes = expression["attributes"]
        operation_type = BinaryOperationType.get_type(attributes["operator"])

        if is_compact_ast:
            left_expression = parse_expression(expression["leftExpression"], caller_context)
            right_expression = parse_expression(expression["rightExpression"], caller_context)
        else:
            assert len(expression["children"]) == 2
            left_expression = parse_expression(expression["children"][0], caller_context)
            right_expression = parse_expression(expression["children"][1], caller_context)
        binary_op = BinaryOperation(left_expression, right_expression, operation_type)
        binary_op.set_offset(src, caller_context.compilation_unit)
        return binary_op

    if name in "FunctionCall":
        return parse_call(expression, caller_context)

    if name == "FunctionCallOptions":
        # call/gas info are handled in parse_call
        if is_compact_ast:
            called = parse_expression(expression["expression"], caller_context)
        else:
            called = parse_expression(expression["children"][0], caller_context)
        assert isinstance(called, (MemberAccess, NewContract, Identifier, TupleExpression))
        return called

    if name == "TupleExpression":
        #     For expression like
        #     (a,,c) = (1,2,3)
        #     the AST provides only two children in the left side
        #     We check the type provided (tuple(uint256,,uint256))
        #     To determine that there is an empty variable
        #     Otherwhise we would not be able to determine that
        #     a = 1, c = 3, and 2 is lost
        #
        #     Note: this is only possible with Solidity >= 0.4.12
        if is_compact_ast:
            expressions = [
                parse_expression(e, caller_context) if e else None for e in expression["components"]
            ]
        else:
            if "children" not in expression:
                attributes = expression["attributes"]
                components = attributes["components"]
                expressions = [
                    parse_expression(c, caller_context) if c else None for c in components
                ]
            else:
                expressions = [parse_expression(e, caller_context) for e in expression["children"]]
        # Add none for empty tuple items
        if "attributes" in expression:
            if "type" in expression["attributes"]:
                t = expression["attributes"]["type"]
                if ",," in t or "(," in t or ",)" in t:
                    t = t[len("tuple(") : -1]
                    elems = t.split(",")
                    for idx, _ in enumerate(elems):
                        if elems[idx] == "":
                            expressions.insert(idx, None)
        t = TupleExpression(expressions)
        t.set_offset(src, caller_context.compilation_unit)
        return t

    if name == "Conditional":
        if is_compact_ast:
            if_expression = parse_expression(expression["condition"], caller_context)
            then_expression = parse_expression(expression["trueExpression"], caller_context)
            else_expression = parse_expression(expression["falseExpression"], caller_context)
        else:
            children = expression["children"]
            assert len(children) == 3
            if_expression = parse_expression(children[0], caller_context)
            then_expression = parse_expression(children[1], caller_context)
            else_expression = parse_expression(children[2], caller_context)
        conditional = ConditionalExpression(if_expression, then_expression, else_expression)
        conditional.set_offset(src, caller_context.compilation_unit)
        return conditional

    if name == "Assignment":
        if is_compact_ast:
            left_expression = parse_expression(expression["leftHandSide"], caller_context)
            right_expression = parse_expression(expression["rightHandSide"], caller_context)

            operation_type = AssignmentOperationType.get_type(expression["operator"])

            operation_return_type = expression["typeDescriptions"]["typeString"]
        else:
            attributes = expression["attributes"]
            children = expression["children"]
            assert len(expression["children"]) == 2
            left_expression = parse_expression(children[0], caller_context)
            right_expression = parse_expression(children[1], caller_context)

            operation_type = AssignmentOperationType.get_type(attributes["operator"])
            operation_return_type = attributes["type"]

        assignement = AssignmentOperation(
            left_expression, right_expression, operation_type, operation_return_type
        )
        assignement.set_offset(src, caller_context.compilation_unit)
        return assignement

    if name == "Literal":

        subdenomination = None

        assert "children" not in expression

        if is_compact_ast:
            value = expression.get("value", None)
            if value:
                if "subdenomination" in expression and expression["subdenomination"]:
                    subdenomination = expression["subdenomination"]
            elif not value and value != "":
                value = "0x" + expression["hexValue"]
            type_candidate = expression["typeDescriptions"]["typeString"]

            # Length declaration for array was None until solc 0.5.5
            if type_candidate is None:
                if expression["kind"] == "number":
                    type_candidate = "int_const"
        else:
            value = expression["attributes"].get("value", None)
            if value:
                if (
                    "subdenomination" in expression["attributes"]
                    and expression["attributes"]["subdenomination"]
                ):
                    subdenomination = expression["attributes"]["subdenomination"]
            elif value is None:
                # for literal declared as hex
                # see https://solidity.readthedocs.io/en/v0.4.25/types.html?highlight=hex#hexadecimal-literals
                assert "hexvalue" in expression["attributes"]
                value = "0x" + expression["attributes"]["hexvalue"]
            type_candidate = expression["attributes"]["type"]

        if type_candidate is None:
            if value.isdecimal():
                type_candidate = ElementaryType("uint256")
            else:
                type_candidate = ElementaryType("string")
        elif type_candidate.startswith("int_const "):
            type_candidate = ElementaryType("uint256")
        elif type_candidate.startswith("bool"):
            type_candidate = ElementaryType("bool")
        elif type_candidate.startswith("address"):
            type_candidate = ElementaryType("address")
        else:
            type_candidate = ElementaryType("string")
        literal = Literal(value, type_candidate, subdenomination)
        literal.set_offset(src, caller_context.compilation_unit)
        return literal

    if name == "Identifier":
        assert "children" not in expression

        t = None

        if caller_context.is_compact_ast:
            value = expression["name"]
            t = expression["typeDescriptions"]["typeString"]
        else:
            value = expression["attributes"]["value"]
            if "type" in expression["attributes"]:
                t = expression["attributes"]["type"]

        if t:
            found = re.findall("[struct|enum|function|modifier] \(([\[\] ()a-zA-Z0-9\.,_]*)\)", t)
            assert len(found) <= 1
            if found:
                value = value + "(" + found[0] + ")"
                value = filter_name(value)

        if "referencedDeclaration" in expression:
            referenced_declaration = expression["referencedDeclaration"]
        else:
            referenced_declaration = None

        var = find_variable(value, caller_context, referenced_declaration)

        identifier = Identifier(var)
        identifier.set_offset(src, caller_context.compilation_unit)
        return identifier

    if name == "IndexAccess":
        if is_compact_ast:
            index_type = expression["typeDescriptions"]["typeString"]
            left = expression["baseExpression"]
            right = expression.get("indexExpression", None)
        else:
            index_type = expression["attributes"]["type"]
            children = expression["children"]
            left = children[0]
            right = children[1] if len(children) > 1 else None
        # IndexAccess is used to describe ElementaryTypeNameExpression
        # if abi.decode is used
        # For example, abi.decode(data, ...(uint[]) )
        if right is None:
            ret = parse_expression(left, caller_context)
            # Nested array are not yet available in abi.decode
            if isinstance(ret, ElementaryTypeNameExpression):
                old_type = ret.type
                ret.type = ArrayType(old_type, None)
            return ret

        left_expression = parse_expression(left, caller_context)
        right_expression = parse_expression(right, caller_context)
        index = IndexAccess(left_expression, right_expression, index_type)
        index.set_offset(src, caller_context.compilation_unit)
        return index

    if name == "MemberAccess":
        if caller_context.is_compact_ast:
            member_name = expression["memberName"]
            member_type = expression["typeDescriptions"]["typeString"]
            # member_type = parse_type(
            #     UnknownType(expression["typeDescriptions"]["typeString"]), caller_context
            # )
            member_expression = parse_expression(expression["expression"], caller_context)
        else:
            member_name = expression["attributes"]["member_name"]
            member_type = expression["attributes"]["type"]
            # member_type = parse_type(UnknownType(expression["attributes"]["type"]), caller_context)
            children = expression["children"]
            assert len(children) == 1
            member_expression = parse_expression(children[0], caller_context)
        if str(member_expression) == "super":
            super_name = parse_super_name(expression, is_compact_ast)
            var = find_variable(super_name, caller_context, is_super=True)
            if var is None:
                raise VariableNotFound("Variable not found: {}".format(super_name))
            sup = SuperIdentifier(var)
            sup.set_offset(src, caller_context.compilation_unit)
            return sup
        member_access = MemberAccess(member_name, member_type, member_expression)
        member_access.set_offset(src, caller_context.compilation_unit)
        if str(member_access) in SOLIDITY_VARIABLES_COMPOSED:
            id_idx = Identifier(SolidityVariableComposed(str(member_access)))
            id_idx.set_offset(src, caller_context.compilation_unit)
            return id_idx
        return member_access

    if name == "ElementaryTypeNameExpression":
        return _parse_elementary_type_name_expression(expression, is_compact_ast, caller_context)

    # NewExpression is not a root expression, it's always the child of another expression
    if name == "NewExpression":

        if is_compact_ast:
            type_name = expression["typeName"]
        else:
            children = expression["children"]
            assert len(children) == 1
            type_name = children[0]

        if type_name[caller_context.get_key()] == "ArrayTypeName":
            depth = 0
            while type_name[caller_context.get_key()] == "ArrayTypeName":
                # Note: dont conserve the size of the array if provided
                # We compute it directly
                if is_compact_ast:
                    type_name = type_name["baseType"]
                else:
                    type_name = type_name["children"][0]
                depth += 1
            if type_name[caller_context.get_key()] == "ElementaryTypeName":
                if is_compact_ast:
                    array_type = ElementaryType(type_name["name"])
                else:
                    array_type = ElementaryType(type_name["attributes"]["name"])
            elif type_name[caller_context.get_key()] == "UserDefinedTypeName":
                if is_compact_ast:
                    array_type = parse_type(UnknownType(type_name["name"]), caller_context)
                else:
                    array_type = parse_type(
                        UnknownType(type_name["attributes"]["name"]), caller_context
                    )
            elif type_name[caller_context.get_key()] == "FunctionTypeName":
                array_type = parse_type(type_name, caller_context)
            else:
                raise ParsingError("Incorrect type array {}".format(type_name))
            array = NewArray(depth, array_type)
            array.set_offset(src, caller_context.compilation_unit)
            return array

        if type_name[caller_context.get_key()] == "ElementaryTypeName":
            if is_compact_ast:
                elem_type = ElementaryType(type_name["name"])
            else:
                elem_type = ElementaryType(type_name["attributes"]["name"])
            new_elem = NewElementaryType(elem_type)
            new_elem.set_offset(src, caller_context.compilation_unit)
            return new_elem

        assert type_name[caller_context.get_key()] == "UserDefinedTypeName"

        if is_compact_ast:

            # Changed introduced in Solidity 0.8
            # see https://github.com/crytic/slither/issues/794

            # TODO explore more the changes introduced in 0.8 and the usage of pathNode/IdentifierPath
            if "name" not in type_name:
                assert "pathNode" in type_name and "name" in type_name["pathNode"]
                contract_name = type_name["pathNode"]["name"]
            else:
                contract_name = type_name["name"]
        else:
            contract_name = type_name["attributes"]["name"]
        new = NewContract(contract_name)
        new.set_offset(src, caller_context.compilation_unit)
        return new

    if name == "ModifierInvocation":

        if is_compact_ast:
            called = parse_expression(expression["modifierName"], caller_context)
            arguments = []
            if expression.get("arguments", None):
                arguments = [parse_expression(a, caller_context) for a in expression["arguments"]]
        else:
            children = expression["children"]
            called = parse_expression(children[0], caller_context)
            arguments = [parse_expression(a, caller_context) for a in children[1::]]

        call = CallExpression(called, arguments, "Modifier")
        call.set_offset(src, caller_context.compilation_unit)
        return call

    if name == "IndexRangeAccess":
        # For now, we convert array slices to a direct array access
        # As a result the generated IR will lose the slices information
        # As far as I understand, array slice are only used in abi.decode
        # https://solidity.readthedocs.io/en/v0.6.12/types.html
        # TODO: Investigate array slices usage and implication for the IR
        base = parse_expression(expression["baseExpression"], caller_context)
        return base

    # Introduced with solc 0.8
    if name == "IdentifierPath":

        if caller_context.is_compact_ast:
            value = expression["name"]

            if "referencedDeclaration" in expression:
                referenced_declaration = expression["referencedDeclaration"]
            else:
                referenced_declaration = None

            var = find_variable(value, caller_context, referenced_declaration)

            identifier = Identifier(var)
            identifier.set_offset(src, caller_context.compilation_unit)
            return identifier

        raise ParsingError("IdentifierPath not currently supported for the legacy ast")

    raise ParsingError("Expression not parsed %s" % name)
