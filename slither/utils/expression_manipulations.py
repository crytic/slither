"""
    We use protected member, to avoid having setter in the expression
    as they should be immutable
"""
import copy
from typing import Union, Callable

from slither.all_exceptions import SlitherException
from slither.core.expressions import UnaryOperation
from slither.core.expressions.assignment_operation import AssignmentOperation
from slither.core.expressions.binary_operation import BinaryOperation
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.conditional_expression import ConditionalExpression
from slither.core.expressions.elementary_type_name_expression import ElementaryTypeNameExpression
from slither.core.expressions.expression import Expression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.index_access import IndexAccess
from slither.core.expressions.literal import Literal
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.new_array import NewArray
from slither.core.expressions.new_contract import NewContract
from slither.core.expressions.tuple_expression import TupleExpression
from slither.core.expressions.type_conversion import TypeConversion
from slither.core.expressions.new_elementary_type import NewElementaryType

# pylint: disable=protected-access
def f_expressions(
    e: Union[AssignmentOperation, BinaryOperation, TupleExpression],
    x: Union[Identifier, Literal, MemberAccess, IndexAccess],
) -> None:
    e._expressions.append(x)


def f_call(e: CallExpression, x: ElementaryTypeNameExpression) -> None:
    e._arguments.append(x)


def f_call_value(e: CallExpression, x):
    e._value = x


def f_call_gas(e: CallExpression, x):
    e._gas = x


def f_expression(e: Union[TypeConversion, UnaryOperation, MemberAccess], x: CallExpression) -> None:
    e._expression = x


def f_called(e: CallExpression, x: Identifier) -> None:
    e._called = x


class SplitTernaryExpression:
    def __init__(self, expression: Union[AssignmentOperation, ConditionalExpression]) -> None:

        if isinstance(expression, ConditionalExpression):
            self.true_expression = copy.copy(expression.then_expression)
            self.false_expression = copy.copy(expression.else_expression)
            self.condition = copy.copy(expression.if_expression)
        else:
            self.true_expression = copy.copy(expression)
            self.false_expression = copy.copy(expression)
            self.condition = None
            self.copy_expression(expression, self.true_expression, self.false_expression)

    def conditional_not_ahead(
        self,
        next_expr: Expression,
        true_expression: Union[AssignmentOperation, MemberAccess],
        false_expression: Union[AssignmentOperation, MemberAccess],
        f: Callable,
    ) -> bool:
        # look ahead for parenthetical expression (.. ? .. : ..)
        if (
            isinstance(next_expr, TupleExpression)
            and len(next_expr.expressions) == 1
            and isinstance(next_expr.expressions[0], ConditionalExpression)
        ):
            next_expr = next_expr.expressions[0]

        if isinstance(next_expr, ConditionalExpression):
            f(true_expression, copy.copy(next_expr.then_expression))
            f(false_expression, copy.copy(next_expr.else_expression))
            self.condition = copy.copy(next_expr.if_expression)
            return False

        f(true_expression, copy.copy(next_expr))
        f(false_expression, copy.copy(next_expr))
        return True

    def copy_expression(
        self, expression: Expression, true_expression: Expression, false_expression: Expression
    ) -> None:
        if self.condition:
            return

        if isinstance(expression, ConditionalExpression):
            raise SlitherException("Nested ternary operator not handled")

        if isinstance(
            expression,
            (
                Literal,
                Identifier,
                NewArray,
                NewContract,
                ElementaryTypeNameExpression,
                NewElementaryType,
            ),
        ):
            return

        if isinstance(
            expression, (AssignmentOperation, BinaryOperation, TupleExpression, IndexAccess)
        ):
            true_expression._expressions = []
            false_expression._expressions = []
            self.convert_expressions(expression, true_expression, false_expression)

        elif isinstance(expression, CallExpression):
            next_expr = expression.called
            self.convert_call_expression(expression, next_expr, true_expression, false_expression)

        elif isinstance(expression, (TypeConversion, UnaryOperation, MemberAccess)):
            next_expr = expression.expression
            if self.conditional_not_ahead(
                next_expr, true_expression, false_expression, f_expression
            ):
                self.copy_expression(
                    expression.expression,
                    true_expression.expression,
                    false_expression.expression,
                )

        else:
            raise SlitherException(
                f"Ternary operation not handled {expression}({type(expression)})"
            )

    def convert_expressions(
        self,
        expression: Union[AssignmentOperation, BinaryOperation, TupleExpression],
        true_expression: Expression,
        false_expression: Expression,
    ) -> None:
        for next_expr in expression.expressions:
            # TODO: can we get rid of `NoneType` expressions in `TupleExpression`?
            # montyly: this might happen with unnamed tuple (ex: (,,,) = f()), but it needs to be checked
            if next_expr is not None:

                if self.conditional_not_ahead(
                    next_expr, true_expression, false_expression, f_expressions
                ):
                    # always on last arguments added
                    self.copy_expression(
                        next_expr,
                        true_expression.expressions[-1],
                        false_expression.expressions[-1],
                    )
            else:
                true_expression.expressions.append(None)
                false_expression.expressions.append(None)

    def convert_index_access(
        self, next_expr: IndexAccess, true_expression: Expression, false_expression: Expression
    ) -> None:
        # create an index access for each branch
        #  x[if cond ? 1 : 2] -> if cond { x[1] } else { x[2] }
        for expr in next_expr.expressions:
            if self.conditional_not_ahead(expr, true_expression, false_expression, f_expressions):
                self.copy_expression(
                    expr,
                    true_expression.expressions[-1],
                    false_expression.expressions[-1],
                )

    def convert_call_expression(
        self,
        expression: CallExpression,
        next_expr: Expression,
        true_expression: Expression,
        false_expression: Expression,
    ) -> None:
        # case of lib
        # (.. ? .. : ..).add
        if self.conditional_not_ahead(next_expr, true_expression, false_expression, f_called):
            self.copy_expression(next_expr, true_expression.called, false_expression.called)

        # In order to handle ternaries in both call options, gas and value, we return early if the
        # conditional is not ahead to rewrite both ternaries (see `_rewrite_ternary_as_if_else`).
        if expression.call_gas:
            # case of (..).func{gas: .. ? .. : ..}()
            next_expr = expression.call_gas
            if self.conditional_not_ahead(next_expr, true_expression, false_expression, f_call_gas):
                self.copy_expression(
                    next_expr,
                    true_expression.call_gas,
                    false_expression.call_gas,
                )
            else:
                return

        if expression.call_value:
            # case of (..).func{value: .. ? .. : ..}()
            next_expr = expression.call_value
            if self.conditional_not_ahead(
                next_expr, true_expression, false_expression, f_call_value
            ):
                self.copy_expression(
                    next_expr,
                    true_expression.call_value,
                    false_expression.call_value,
                )
            else:
                return

        true_expression._arguments = []
        false_expression._arguments = []

        for expr in expression.arguments:
            if self.conditional_not_ahead(expr, true_expression, false_expression, f_call):
                # always on last arguments added
                self.copy_expression(
                    expr,
                    true_expression.arguments[-1],
                    false_expression.arguments[-1],
                )
