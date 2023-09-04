import logging
import re
from typing import Union, Dict, TYPE_CHECKING, List, Any

import slither.core.expressions.type_conversion
from slither.core.declarations.solidity_variables import (
    SOLIDITY_VARIABLES_COMPOSED,
    SolidityVariableComposed,
)
from slither.core.declarations import SolidityFunction, Function
from slither.core.expressions import (
    CallExpression,
    ConditionalExpression,
    ElementaryTypeNameExpression,
    Identifier,
    IndexAccess,
    Literal,
    MemberAccess,
    NewArray,
    NewContract,
    NewElementaryType,
    SuperCallExpression,
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

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression


from collections import deque
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
)


def parse_expression(expression: Dict, caller_context) -> "Expression":
    print("parse_expression")
    print(expression, "\n")
    # assert False

    if isinstance(expression, Int):
        literal = Literal(str(expression.value), ElementaryType("uint256"))
        literal.set_offset(expression.src, caller_context.compilation_unit)
        return literal

    if isinstance(expression, Hex):
        # TODO this is an implicit conversion and could potentially be bytes20 or other?
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
        print("Call")
        print(expression)
        called = parse_expression(expression.func, caller_context)
        if isinstance(called, Identifier) and isinstance(called.value, SolidityFunction):
            if called.value.name == "empty()":
                type_to = parse_type(expression.args[0], caller_context)
                # TODO figure out how to represent this type argument
                parsed_expr = CallExpression(called, [], str(type_to))
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                return parsed_expr

            elif called.value.name == "convert()":
                arg = parse_expression(expression.args[0], caller_context)
                type_to = parse_type(expression.args[1], caller_context)
                parsed_expr = TypeConversion(arg, type_to)
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                return parsed_expr

            elif called.value.name == "min_value()":
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

            elif called.value.name == "max_value()":
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

            elif called.value.name == "raw_call()":
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

        if isinstance(called, Identifier):
            print("called", called)
            print("called.value", called.value.__class__.__name__)
            # Since the AST lacks the type of the return values, we recover it.
            if isinstance(called.value, Function):
                rets = called.value.returns
                # Default arguments are not represented in the AST, so we recover them as well.
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
                # so we infer that a type conversion is occurring if `called` is a `Contract` type.
                type_to = parse_type(expression.func, caller_context)
                parsed_expr = TypeConversion(arguments[0], type_to)
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                return parsed_expr

            else:
                rets = ["tuple()"]

        elif isinstance(called, MemberAccess) and called.type is not None:
            # (recover_type_2) Propagate the type collected to the `CallExpression`
            # see recover_type_1
            rets = [called.type]
        else:
            rets = ["tuple()"]

        def get_type_str(x):
            if isinstance(x, str):
                return x
            return str(x.type)

        print(rets)
        type_str = (
            get_type_str(rets[0])
            if len(rets) == 1
            else f"tuple({','.join(map(get_type_str, rets))})"
        )
        print(arguments)
        parsed_expr = CallExpression(called, arguments, type_str)
        parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
        return parsed_expr

    if isinstance(expression, Attribute):
        member_name = expression.attr
        if isinstance(expression.value, Name):
            # TODO this is ambiguous because it could be a state variable or a call to balance
            if expression.value.id == "self" and member_name != "balance":
                var, was_created = find_variable(member_name, caller_context, is_self=True)
                if was_created:
                    var.set_offset(expression.src, caller_context.compilation_unit)
                parsed_expr = SelfIdentifier(var)
                parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                var.references.append(parsed_expr.source_mapping)
                return parsed_expr

            expr = parse_expression(expression.value, caller_context)
            # TODO this is ambiguous because it could be a type conversion of an interface or a member access
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
            # its enclosing `CallExpression`
            print(expr)
            print(expr.__class__.__name__)

            if isinstance(expr, TypeConversion) and isinstance(expr.type, UserDefinedType):
                # If we access a member of an interface, needs to be interface instead of self namespace
                var, was_created = find_variable(member_name, expr.type.type)
                if isinstance(var, Function):
                    rets = var.returns

                    def get_type_str(x):
                        if isinstance(x, str):
                            return x
                        return str(x.type)

                    type_str = (
                        get_type_str(rets[0])
                        if len(rets) == 1
                        else f"tuple({','.join(map(get_type_str, rets))})"
                    )
                    member_name_ret_type = type_str

            member_access = MemberAccess(member_name, member_name_ret_type, expr)

        member_access.set_offset(expression.src, caller_context.compilation_unit)
        return member_access

    if isinstance(expression, Name):
        var, was_created = find_variable(expression.id, caller_context)
        if was_created:
            var.set_offset(expression.src, caller_context.compilation_unit)
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

        if expression.op in ["In", "NotIn"]:
            # If we see a membership operator e.g. x in [foo(), bar()] we rewrite it as if-else:
            #  if (x == foo()) {
            #   return true
            # } else {
            #   if (x == bar()) {
            #       return true
            #   } else {
            #       return false
            #   }
            # }
            # We assume left operand in membership comparison cannot be Array type
            conditions = deque()
            if isinstance(expression.right, VyList):
                inner_op = (
                    BinaryOperationType.get_type("!=")
                    if expression.op == "NotIn"
                    else BinaryOperationType.get_type("==")
                )
                outer_op = (
                    BinaryOperationType.get_type("&&")
                    if expression.op == "NotIn"
                    else BinaryOperationType.get_type("||")
                )

                for elem in expression.right.elements:
                    elem_expr = parse_expression(elem, caller_context)
                    print("elem", repr(elem_expr))
                    parsed_expr = BinaryOperation(lhs, elem_expr, inner_op)
                    parsed_expr.set_offset(expression.src, caller_context.compilation_unit)
                    conditions.append(parsed_expr)
            else:
                rhs = parse_expression(expression.right, caller_context)
                print(rhs)
                print(rhs.__class__.__name__)
                if isinstance(rhs, Identifier):
                    if isinstance(rhs.value.type, ArrayType):
                        inner_op = (
                            BinaryOperationType.get_type("!=")
                            if expression.op == "NotIn"
                            else BinaryOperationType.get_type("==")
                        )
                        outer_op = (
                            BinaryOperationType.get_type("&&")
                            if expression.op == "NotIn"
                            else BinaryOperationType.get_type("||")
                        )

                        enum_members = rhs.value.type.length_value.value
                        for i in range(enum_members):
                            elem_expr = IndexAccess(rhs, Literal(str(i), ElementaryType("uint256")))
                            elem_expr.set_offset(
                                rhs.source_mapping, caller_context.compilation_unit
                            )
                            parsed_expr = BinaryOperation(lhs, elem_expr, inner_op)
                            parsed_expr.set_offset(
                                lhs.source_mapping, caller_context.compilation_unit
                            )
                            conditions.append(parsed_expr)
                    # elif isinstance(rhs.value.type, UserDefinedType):

                    else:
                        assert False
                else:
                    # This is an indexaccess like hashmap[address, Roles]
                    inner_op = BinaryOperationType.get_type(
                        "|"
                    )  # if expression.op == "NotIn" else BinaryOperationType.get_type("==")
                    outer_op = BinaryOperationType.get_type(
                        "&"
                    )  # if expression.op == "NotIn" else BinaryOperationType.get_type("||")

                    # x, _ = find_variable(expression.right.value.attr, caller_context)
                    # print(x)
                    # print(x.type.type_to)
                    # print(x.type.type_to.__class__)
                    print(repr(rhs))
                    print(rhs)

                    enum_members = rhs.expression_left.value.type.type_to.type.values
                    # for each value, create a literal with value = 2 ^ n (0 indexed)
                    # and then translate to bitmasking
                    enum_values = [
                        Literal(str(2**n), ElementaryType("uint256"))
                        for n in range(len(enum_members))
                    ]
                    inner_lhs = enum_values[0]
                    for expr in enum_values[1:]:
                        inner_lhs = BinaryOperation(inner_lhs, expr, inner_op)
                        conditions.append(inner_lhs)

                    parsed_expr = BinaryOperation(lhs, conditions[0], outer_op)
                    parsed_expr.set_offset(lhs.source_mapping, caller_context.compilation_unit)
                    return parsed_expr

            while len(conditions) > 1:
                lhs = conditions.pop()
                rhs = conditions.pop()

                conditions.appendleft(BinaryOperation(lhs, rhs, outer_op))

            return conditions.pop()

        else:
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

    raise ParsingError(f"Expression not parsed {expression}")
