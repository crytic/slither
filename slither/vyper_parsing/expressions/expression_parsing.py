from typing import Optional, List, Union, TYPE_CHECKING
from collections import deque
from slither.core.declarations.solidity_variables import (
    SOLIDITY_VARIABLES_COMPOSED,
    SolidityVariableComposed,
)
from slither.core.declarations import SolidityFunction, FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.core.expressions import (
    CallExpression,
    ElementaryTypeNameExpression,
    Identifier,
    IndexAccess,
    Literal,
    MemberAccess,
    SelfIdentifier,
    TupleExpression,
    TypeConversion,
    UnaryOperation,
    UnaryOperationType,
)
from slither.core.expressions.assignment_operation import (
    AssignmentOperation,
    AssignmentOperationType,
)
from slither.core.expressions.binary_operation import (
    BinaryOperation,
    BinaryOperationType,
)
from slither.core.solidity_types import (
    ArrayType,
    ElementaryType,
    UserDefinedType,
)
from slither.core.declarations.contract import Contract
from slither.vyper_parsing.expressions.find_variable import find_variable
from slither.vyper_parsing.type_parsing import parse_type
from slither.all_exceptions import ParsingError
from slither.vyper_parsing.ast.types import (
    Int,
    Call,
    Attribute,
    Name,
    Tuple,
    Hex,
    BinOp,
    Str,
    Assert,
    Compare,
    UnaryOp,
    Subscript,
    NameConstant,
    VyDict,
    Bytes,
    BoolOp,
    Assign,
    AugAssign,
    VyList,
    Raise,
    ASTNode,
)

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression


def vars_to_typestr(rets: Optional[List["Expression"]]) -> str:
    if rets is None:
        return "tuple()"
    if len(rets) == 1:
        return str(rets[0].type)
    return f"tuple({','.join(str(ret.type) for ret in rets)})"


# pylint: disable=too-many-branches,too-many-statements,too-many-locals
def parse_expression(
    expression: ASTNode, caller_context: Union[FunctionContract, Contract]
) -> "Expression":

    if isinstance(expression, Int):
        literal = Literal(str(expression.value), ElementaryType("uint256"))
        literal.set_offset(expression.src, caller_context.compilation_unit)
        return literal

    if isinstance(expression, Hex):
        # TODO this is an implicit conversion and could potentially be bytes20 or other? https://github.com/vyperlang/vyper/issues/3580
        literal = Literal(str(expression.value), ElementaryType("address"))
        literal.set_offset(expression.src, caller_context.compilation_unit)
        return literal

    if isinstance(expression, Str):
        literal = Literal(str(expression.value), ElementaryType("string"))
        literal.set_offset(expression.src, caller_context.compilation_unit)
        return literal

    if isinstance(expression, Bytes):
        literal = Literal(str(expression.value), ElementaryType("bytes"))
        literal.set_offset(expression.src, caller_context.compilation_unit)
        return literal

    if isinstance(expression, NameConstant):
        assert str(expression.value) in ["True", "False"]
        literal = Literal(str(expression.value), ElementaryType("bool"))
        literal.set_offset(expression.src, caller_context.compilation_unit)
        return literal

    if isinstance(expression, Call):
        called = parse_expression(expression.func, caller_context)
        if isinstance(called, Identifier) and isinstance(called.value, SolidityFunction):
            if called.value.name == "empty()":
                type_to = parse_type(expression.args[0], caller_context)
                # TODO figure out how to represent this type argument
                parsed_expr = CallExpression(called, [], str(type_to))
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                return parsed_expr

            if called.value.name == "convert()":
                arg = parse_expression(expression.args[0], caller_context)
                type_to = parse_type(expression.args[1], caller_context)
                parsed_expr = TypeConversion(arg, type_to)
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                return parsed_expr

            if called.value.name == "min_value()":
                type_to = parse_type(expression.args[0], caller_context)
                member_type = str(type_to)
                # TODO return Literal
                parsed_expr = MemberAccess(
                    "min",
                    member_type,
                    CallExpression(
                        Identifier(SolidityFunction("type()")),
                        [ElementaryTypeNameExpression(type_to)],
                        member_type,
                    ),
                )
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                return parsed_expr

            if called.value.name == "max_value()":
                type_to = parse_type(expression.args[0], caller_context)
                member_type = str(type_to)
                # TODO return Literal
                parsed_expr = MemberAccess(
                    "max",
                    member_type,
                    CallExpression(
                        Identifier(SolidityFunction("type()")),
                        [ElementaryTypeNameExpression(type_to)],
                        member_type,
                    ),
                )
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                return parsed_expr

            if called.value.name == "raw_call()":
                args = [parse_expression(a, caller_context) for a in expression.args]
                # This is treated specially in order to force `extract_tmp_call` to treat this as a `HighLevelCall` which will be converted
                # to a `LowLevelCall` by `convert_to_low_level`. This is an artifact of the late conversion of Solidity...
                call = CallExpression(
                    MemberAccess("raw_call", "tuple(bool,bytes32)", args[0]),
                    args[1:],
                    "tuple(bool,bytes32)",
                )
                call.set_offset(expression.src, caller_context.compilation_unit)
                call.call_value = next(
                    iter(
                        parse_expression(x.value, caller_context)
                        for x in expression.keywords
                        if x.arg == "value"
                    ),
                    None,
                )
                call.call_gas = next(
                    iter(
                        parse_expression(x.value, caller_context)
                        for x in expression.keywords
                        if x.arg == "gas"
                    ),
                    None,
                )
                # TODO handle `max_outsize` keyword

                return call

        if expression.args and isinstance(expression.args[0], VyDict):
            arguments = []
            for val in expression.args[0].values:
                arguments.append(parse_expression(val, caller_context))
        else:
            arguments = [parse_expression(a, caller_context) for a in expression.args]

        rets = None
        # Since the AST lacks the type of the return values, we recover it. https://github.com/vyperlang/vyper/issues/3581
        if isinstance(called, Identifier):
            if isinstance(called.value, FunctionContract):
                rets = called.value.returns
                # Default arguments are not represented in the AST, so we recover them as well.
                # pylint: disable=protected-access
                if called.value._default_args_as_expressions and len(arguments) < len(
                    called.value.parameters
                ):
                    arguments.extend(
                        [
                            parse_expression(x, caller_context)
                            for x in called.value._default_args_as_expressions
                        ]
                    )

            elif isinstance(called.value, SolidityFunction):
                rets = called.value.return_type

            elif isinstance(called.value, Contract):
                # Type conversions are not explicitly represented in the AST e.g. converting address to contract/ interface,
                # so we infer that a type conversion is occurring if `called` is a `Contract` type. https://github.com/vyperlang/vyper/issues/3580
                type_to = parse_type(expression.func, caller_context)
                parsed_expr = TypeConversion(arguments[0], type_to)
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                return parsed_expr

        elif isinstance(called, MemberAccess) and called.type is not None:
            # (recover_type_2) Propagate the type collected to the `CallExpression`
            # see recover_type_1
            rets = [called]

        type_str = vars_to_typestr(rets)
        parsed_expr = CallExpression(called, arguments, type_str)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, Attribute):
        member_name = expression.attr
        if isinstance(expression.value, Name):
            # TODO this is ambiguous because it could be a state variable or a call to balance https://github.com/vyperlang/vyper/issues/3582
            if expression.value.id == "self" and member_name != "balance":
                var = find_variable(member_name, caller_context, is_self=True)
                parsed_expr = SelfIdentifier(var)
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                var.references.append(parsed_expr.source_mapping)
                return parsed_expr

            expr = parse_expression(expression.value, caller_context)
            # TODO this is ambiguous because it could be a type conversion of an interface or a member access
            # see https://github.com/vyperlang/vyper/issues/3580 and ttps://github.com/vyperlang/vyper/issues/3582
            if expression.attr == "address":
                parsed_expr = TypeConversion(expr, ElementaryType("address"))
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                return parsed_expr

            member_access = MemberAccess(member_name, None, expr)

            if str(member_access) in SOLIDITY_VARIABLES_COMPOSED:
                parsed_expr = Identifier(SolidityVariableComposed(str(member_access)))
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                return parsed_expr

        else:
            expr = parse_expression(expression.value, caller_context)
            member_name_ret_type = None
            # (recover_type_1) This may be a call to an interface and we don't have the return types,
            # so we see if there's a function identifier with `member_name` and propagate the type to
            # its enclosing `CallExpression`. https://github.com/vyperlang/vyper/issues/3581
            if (
                isinstance(expr, Identifier)
                and isinstance(expr.value, StateVariable)
                and isinstance(expr.value.type, UserDefinedType)
                and isinstance(expr.value.type.type, Contract)
            ):
                # If we access a member of an interface, needs to be interface instead of self namespace
                var = find_variable(member_name, expr.value.type.type)
                if isinstance(var, FunctionContract):
                    rets = var.returns
                    member_name_ret_type = vars_to_typestr(rets)

            if (
                isinstance(expr, TypeConversion)
                and isinstance(expr.type, UserDefinedType)
                and isinstance(expr.type.type, Contract)
            ):
                # If we access a member of an interface, needs to be interface instead of self namespace
                var = find_variable(member_name, expr.type.type)
                if isinstance(var, FunctionContract):
                    rets = var.returns
                    member_name_ret_type = vars_to_typestr(rets)

            member_access = MemberAccess(member_name, member_name_ret_type, expr)

        member_access.set_offset(expression.src, caller_context.compilation_unit)
        return member_access

    if isinstance(expression, Name):
        var = find_variable(expression.id, caller_context)
        parsed_expr = Identifier(var)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, Assign):
        lhs = parse_expression(expression.target, caller_context)
        rhs = parse_expression(expression.value, caller_context)
        parsed_expr = AssignmentOperation(lhs, rhs, AssignmentOperationType.ASSIGN, None)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, AugAssign):
        lhs = parse_expression(expression.target, caller_context)
        rhs = parse_expression(expression.value, caller_context)

        op = AssignmentOperationType.get_type(expression.op)
        parsed_expr = AssignmentOperation(lhs, rhs, op, None)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, (Tuple, VyList)):
        tuple_vars = [parse_expression(x, caller_context) for x in expression.elements]
        parsed_expr = TupleExpression(tuple_vars)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, UnaryOp):
        operand = parse_expression(expression.operand, caller_context)
        op = UnaryOperationType.get_type(
            expression.op, isprefix=True
        )  # TODO does vyper have postfix?

        parsed_expr = UnaryOperation(operand, op)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, Compare):
        lhs = parse_expression(expression.left, caller_context)

        # We assume left operand in membership comparison cannot be Array type
        if expression.op in ["In", "NotIn"]:
            # If we see a membership operator e.g. x in [foo(), bar()], we convert it to logical operations
            # like (x == foo() || x == bar()) or (x != foo() && x != bar()) for "not in"
            # TODO consider rewriting as if-else to accurately represent the precedence of potential side-effects

            conditions = deque()
            rhs = parse_expression(expression.right, caller_context)
            is_tuple = isinstance(rhs, TupleExpression)
            is_array = isinstance(rhs, Identifier) and isinstance(rhs.value.type, ArrayType)
            if is_array:
                assert (
                    rhs.value.type.is_fixed_array
                ), "Dynamic arrays are not supported in comparison operators"
            if is_tuple or is_array:
                length = len(rhs.expressions) if is_tuple else rhs.value.type.length_value.value
                inner_op = (
                    BinaryOperationType.get_type("!=")
                    if expression.op == "NotIn"
                    else BinaryOperationType.get_type("==")
                )
                for i in range(length):
                    elem_expr = (
                        rhs.expressions[i]
                        if is_tuple
                        else IndexAccess(rhs, Literal(str(i), ElementaryType("uint256")))
                    )
                    elem_expr.set_offset(rhs.source_mapping, caller_context.compilation_unit)
                    parsed_expr = BinaryOperation(lhs, elem_expr, inner_op)
                    parsed_expr.set_offset(lhs.source_mapping, caller_context.compilation_unit)
                    conditions.append(parsed_expr)

                outer_op = (
                    BinaryOperationType.get_type("&&")
                    if expression.op == "NotIn"
                    else BinaryOperationType.get_type("||")
                )
                while len(conditions) > 1:
                    lhs = conditions.pop()
                    rhs = conditions.pop()

                    conditions.appendleft(BinaryOperation(lhs, rhs, outer_op))

                return conditions.pop()

            # enum type membership check https://docs.vyperlang.org/en/stable/types.html?h#id18
            is_member_op = (
                BinaryOperationType.get_type("==")
                if expression.op == "NotIn"
                else BinaryOperationType.get_type("!=")
            )
            # If all bits are cleared, then the lhs is not a member of the enum
            # This allows representing membership in multiple enum members
            # For example, if enum Foo has members A (1), B (2), and C (4), then
            # (x in [Foo.A, Foo.B]) is equivalent to (x & (Foo.A | Foo.B) != 0),
            # where (Foo.A | Foo.B) evaluates to 3.
            # Thus, when x is 3, (x & (Foo.A | Foo.B) != 0) is true.
            enum_bit_mask = BinaryOperation(
                TypeConversion(lhs, ElementaryType("uint256")),
                TypeConversion(rhs, ElementaryType("uint256")),
                BinaryOperationType.get_type("&"),
            )
            membership_check = BinaryOperation(
                enum_bit_mask, Literal("0", ElementaryType("uint256")), is_member_op
            )
            membership_check.set_offset(lhs.source_mapping, caller_context.compilation_unit)
            return membership_check

        # a regular logical operator
        rhs = parse_expression(expression.right, caller_context)
        op = BinaryOperationType.get_type(expression.op)

        parsed_expr = BinaryOperation(lhs, rhs, op)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, BinOp):
        lhs = parse_expression(expression.left, caller_context)
        rhs = parse_expression(expression.right, caller_context)

        op = BinaryOperationType.get_type(expression.op)
        parsed_expr = BinaryOperation(lhs, rhs, op)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, Assert):
        # Treat assert the same as a Solidity `require`.
        # TODO rename from `SolidityFunction` to `Builtin`?
        type_str = "tuple()"
        if expression.msg is None:
            func = SolidityFunction("require(bool)")
            args = [parse_expression(expression.test, caller_context)]
        else:
            func = SolidityFunction("require(bool,string)")
            args = [
                parse_expression(expression.test, caller_context),
                parse_expression(expression.msg, caller_context),
            ]

        parsed_expr = CallExpression(Identifier(func), args, type_str)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, Subscript):
        left_expression = parse_expression(expression.value, caller_context)
        right_expression = parse_expression(expression.slice.value, caller_context)
        parsed_expr = IndexAccess(left_expression, right_expression)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, BoolOp):
        lhs = parse_expression(expression.values[0], caller_context)
        rhs = parse_expression(expression.values[1], caller_context)

        op = BinaryOperationType.get_type(expression.op)
        parsed_expr = BinaryOperation(lhs, rhs, op)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, Raise):
        type_str = "tuple()"
        func = (
            SolidityFunction("revert()")
            if expression.exc is None
            else SolidityFunction("revert(string)")
        )
        args = [] if expression.exc is None else [parse_expression(expression.exc, caller_context)]

        parsed_expr = CallExpression(Identifier(func), args, type_str)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    raise ParsingError(f"Expression not parsed {expression}")
